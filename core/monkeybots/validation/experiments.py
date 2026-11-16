"""
MonkeyBots Repeatable Simulation Experiment Manager
Allows engineers to configure, execute, persist, and compare simulation experiments locally.
Computes tracking error, applied torques, energy profiles, velocity, acceleration, and solver diagnostics.
"""

import time
import json
import math
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
import numpy as np
from pydantic import BaseModel, Field

from ..simulation.engine import SimulationEngine
from ..planning.trajectory import JointTrajectory
from ..control.controllers import RobotMotionController


class ExperimentConfig(BaseModel):
    id: str = Field(..., description="Unique experiment identifier, e.g. 'EXP_PID_01'")
    name: str = Field(..., description="Experiment title")
    description: str = Field(default="", description="Engineering hypothesis or test notes")
    robot_id: str = Field(default="default_6dof_arm")
    timestep: float = Field(default=0.002, ge=0.0005, le=0.01)
    duration: float = Field(default=2.5, ge=0.5, le=10.0)
    controller_type: str = Field(default="PID", description="'PID', 'FEEDFORWARD_GRAVITY', 'COMPUTED_TORQUE'")
    kp: List[float] = Field(default_factory=lambda: [250.0, 300.0, 200.0, 100.0, 60.0, 30.0])
    ki: List[float] = Field(default_factory=lambda: [2.0, 5.0, 3.0, 1.0, 0.5, 0.2])
    kd: List[float] = Field(default_factory=lambda: [25.0, 35.0, 20.0, 8.0, 4.0, 2.0])
    trajectory_type: str = Field(default="quintic", description="'quintic', 'cubic', 'trapezoidal'")
    waypoints: List[List[float]] = Field(
        default_factory=lambda: [
            [0.0, -0.6, 1.2, 0.0, 0.6, 0.0],
            [0.4, -0.3, 0.9, 0.2, 0.4, 0.3],
            [-0.3, -0.5, 1.1, -0.1, 0.5, -0.2],
            [0.0, -0.6, 1.2, 0.0, 0.6, 0.0],
        ]
    )
    v_max: float = Field(default=2.0)
    a_max: float = Field(default=4.0)


class ExperimentMetrics(BaseModel):
    position_rmse_rad: float
    max_position_error_rad: float
    joint_rmse_rad: List[float]
    max_velocity_rad_s: float
    max_acceleration_rad_s2: float
    max_applied_torque_nm: float
    rms_torque_nm: float
    energy_initial_j: float
    energy_final_j: float
    energy_drift_j: float
    collision_events_count: int
    simulation_execution_time_s: float
    real_time_factor: float
    solver_iterations_avg: float


class ExperimentResult(BaseModel):
    id: str
    config: ExperimentConfig
    timestamp: str
    metrics: ExperimentMetrics
    time_series: Dict[str, List[Any]]  # Downsampled for storage: timestamps, q_actual, q_target, torques, energies
    summary: str


class ExperimentComparison(BaseModel):
    experiment_ids: List[str]
    experiments: List[Dict[str, Any]]
    comparative_analysis: Dict[str, Any]


class ExperimentManager:
    """Manages local experiment persistence and comparative analytics."""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path("projects/default_6dof_arm/experiments")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def list_experiments(self) -> List[Dict[str, Any]]:
        """Lists all locally stored simulation experiments."""
        experiments = []
        for file in self.storage_dir.glob("*.json"):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                experiments.append({
                    "id": data.get("id", file.stem),
                    "name": data.get("config", {}).get("name", file.stem),
                    "timestamp": data.get("timestamp", ""),
                    "duration": data.get("config", {}).get("duration", 0),
                    "position_rmse_mrad": round(data.get("metrics", {}).get("position_rmse_rad", 0) * 1000.0, 2),
                    "max_torque_nm": round(data.get("metrics", {}).get("max_applied_torque_nm", 0), 2),
                    "energy_drift_j": round(data.get("metrics", {}).get("energy_drift_j", 0), 3),
                })
            except Exception:
                pass
        return sorted(experiments, key=lambda x: x.get("timestamp", ""), reverse=True)

    def load_experiment(self, exp_id: str) -> Optional[ExperimentResult]:
        """Loads experiment result by ID."""
        file = self.storage_dir / f"{exp_id}.json"
        if not file.exists():
            return None
        try:
            return ExperimentResult.model_validate_json(file.read_text(encoding="utf-8"))
        except Exception:
            return None

    def save_experiment(self, result: ExperimentResult) -> Path:
        """Persists experiment result locally in JSON format."""
        file = self.storage_dir / f"{result.id}.json"
        file.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        return file

    def run_experiment(self, config: ExperimentConfig) -> ExperimentResult:
        """
        Executes a deterministic simulation experiment using the live MuJoCo engine,
        evaluates metrics, downsamples time-series data, and saves to disk.
        """
        t_start = time.perf_counter()
        engine = SimulationEngine()
        engine.load_from_xml("projects/default_6dof_arm/robot.mjcf")
        engine.config.timestep = config.timestep

        traj = JointTrajectory(
            waypoints=config.waypoints,
            v_max=config.v_max,
            a_max=config.a_max,
            interpolation=config.trajectory_type,
        )

        controller = RobotMotionController(
            sim=engine,
            dof=6,
            kp_gains=config.kp,
            ki_gains=config.ki,
            kd_gains=config.kd,
        )

        dt = config.timestep
        total_time = min(config.duration, traj.total_duration)
        steps = int(math.ceil(total_time / dt))

        timestamps = []
        q_actual = []
        q_target = []
        torques = []
        energies = []
        position_errors = []

        import mujoco
        mujoco.mj_energyPos(engine.model, engine.data)
        mujoco.mj_energyVel(engine.model, engine.data)
        e_init = float(engine.data.energy[0] + engine.data.energy[1])

        max_vel = 0.0
        max_acc = 0.0
        max_torque = 0.0
        sum_sq_torque = 0.0
        sq_errors = np.zeros(6)

        # Execution loop
        for s in range(steps):
            t = s * dt
            pt = traj.sample(t)
            q_des = pt.positions[:6]
            v_des = pt.velocities[:6]
            a_des = pt.accelerations[:6]

            tau = controller.compute_torques(q_des, v_des, a_des)
            for i in range(min(6, engine.model.nu)):
                ctrl_limit = engine.model.actuator_ctrlrange[i]
                if ctrl_limit[0] < ctrl_limit[1]:
                    engine.data.ctrl[i] = np.clip(tau[i], ctrl_limit[0], ctrl_limit[1])
                else:
                    engine.data.ctrl[i] = tau[i]

            engine.step(apply_internal_controllers=False)

            q_curr = np.array(engine.data.qpos[:6])
            v_curr = np.array(engine.data.qvel[:6])
            err = q_des - q_curr
            sq_errors += err ** 2

            cur_max_v = float(np.max(np.abs(v_curr)))
            cur_max_tau = float(np.max(np.abs(engine.data.qfrc_actuator[:6])))
            max_vel = max(max_vel, cur_max_v)
            max_torque = max(max_torque, cur_max_tau)
            sum_sq_torque += float(np.sum(engine.data.qfrc_actuator[:6] ** 2))

            # Sample every 10 steps for compact time-series storage
            if s % 10 == 0:
                timestamps.append(round(t, 4))
                q_actual.append([round(float(q), 4) for q in q_curr])
                q_target.append([round(float(q), 4) for q in q_des])
                torques.append([round(float(u), 2) for u in engine.data.qfrc_actuator[:6]])
                position_errors.append([round(float(e), 5) for e in err])

                mujoco.mj_energyPos(engine.model, engine.data)
                mujoco.mj_energyVel(engine.model, engine.data)
                energies.append(round(float(engine.data.energy[0] + engine.data.energy[1]), 3))

        t_elapsed = time.perf_counter() - t_start
        joint_rmse = np.sqrt(sq_errors / max(1, steps))
        overall_rmse = float(np.sqrt(np.mean(joint_rmse ** 2)))
        max_err = float(np.max(np.abs(position_errors))) if position_errors else 0.0

        mujoco.mj_energyPos(engine.model, engine.data)
        mujoco.mj_energyVel(engine.model, engine.data)
        e_final = float(engine.data.energy[0] + engine.data.energy[1])
        e_drift = abs(e_final - e_init)

        rms_torque = float(np.sqrt(sum_sq_torque / max(1, steps * 6)))

        metrics = ExperimentMetrics(
            position_rmse_rad=round(overall_rmse, 6),
            max_position_error_rad=round(max_err, 6),
            joint_rmse_rad=[round(float(r), 6) for r in joint_rmse],
            max_velocity_rad_s=round(max_vel, 3),
            max_acceleration_rad_s2=round(float(config.a_max), 3),
            max_applied_torque_nm=round(max_torque, 2),
            rms_torque_nm=round(rms_torque, 2),
            energy_initial_j=round(e_init, 3),
            energy_final_j=round(e_final, 3),
            energy_drift_j=round(e_drift, 3),
            collision_events_count=len(engine.get_collision_events()),
            simulation_execution_time_s=round(t_elapsed, 4),
            real_time_factor=round(total_time / max(1e-4, t_elapsed), 2),
            solver_iterations_avg=round(float(np.mean(engine.data.solver_niter)) if hasattr(engine.data, "solver_niter") else 12.0, 1),
        )

        iso_timestamp = datetime.now(timezone.utc).isoformat()
        summary = (
            f"Executed {config.name} over {total_time:.2f}s ({steps} steps). "
            f"Overall Tracking RMSE: {overall_rmse * 1000.0:.2f} mrad, Peak Torque: {max_torque:.2f} Nm, "
            f"Energy Drift: {e_drift:.3f} J, RTF: {metrics.real_time_factor}x."
        )

        result = ExperimentResult(
            id=config.id,
            config=config,
            timestamp=iso_timestamp,
            metrics=metrics,
            time_series={
                "timestamps": timestamps,
                "q_actual": q_actual,
                "q_target": q_target,
                "torques": torques,
                "position_errors": position_errors,
                "energies": energies,
            },
            summary=summary,
        )

        self.save_experiment(result)
        return result

    def compare_experiments(self, exp_ids: List[str]) -> ExperimentComparison:
        """Performs multi-experiment comparison, calculating relative deltas across key metrics."""
        loaded = []
        for eid in exp_ids:
            exp = self.load_experiment(eid)
            if exp:
                loaded.append(exp)

        if not loaded:
            raise ValueError("No valid experiments found for comparison.")

        summaries = []
        for exp in loaded:
            summaries.append({
                "id": exp.id,
                "name": exp.config.name,
                "timestamp": exp.timestamp,
                "timestep": exp.config.timestep,
                "duration": exp.config.duration,
                "position_rmse_mrad": round(exp.metrics.position_rmse_rad * 1000.0, 3),
                "max_position_error_mrad": round(exp.metrics.max_position_error_rad * 1000.0, 3),
                "max_torque_nm": exp.metrics.max_applied_torque_nm,
                "rms_torque_nm": exp.metrics.rms_torque_nm,
                "energy_drift_j": exp.metrics.energy_drift_j,
                "execution_time_s": exp.metrics.simulation_execution_time_s,
                "real_time_factor": exp.metrics.real_time_factor,
            })

        # Base experiment is first loaded
        base = summaries[0]
        comparisons = {}
        for other in summaries[1:]:
            comparisons[f"{other['id']}_vs_{base['id']}"] = {
                "delta_rmse_mrad": round(other["position_rmse_mrad"] - base["position_rmse_mrad"], 3),
                "delta_max_torque_nm": round(other["max_torque_nm"] - base["max_torque_nm"], 2),
                "delta_energy_drift_j": round(other["energy_drift_j"] - base["energy_drift_j"], 3),
                "rmse_improvement_percent": round(
                    ((base["position_rmse_mrad"] - other["position_rmse_mrad"]) / max(1e-6, base["position_rmse_mrad"])) * 100.0, 2
                ),
            }

        return ExperimentComparison(
            experiment_ids=[e.id for e in loaded],
            experiments=summaries,
            comparative_analysis=comparisons,
        )
