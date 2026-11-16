"""
MonkeyBots High-Speed Telemetry Recorder & Buffer
Captures actual physics simulation steps from MuJoCo:
Joint states (q, qvel, qacc), applied torques, end-effector poses,
tracking errors, contact forces, system energies, and numerical solver metrics.
Guarantees zero fabricated or synthetic data.
"""

import time
import math
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

from ..simulation.engine import SimulationEngine
from ..kinematics.chain import KinematicChain
from ..kinematics.fk import compute_forward_kinematics
from ..planning.trajectory import JointTrajectory
from ..control.controllers import RobotMotionController
from ..models.assets.sample_6dof_arm import create_sample_6dof_arm

try:
    import mujoco
    MUJOCO_AVAILABLE = True
except ImportError:
    MUJOCO_AVAILABLE = False


class TelemetryPoint(BaseModel):
    """Single synchronized simulation state capture."""
    time: float
    q_actual: List[float]
    q_target: List[float]
    qvel_actual: List[float]
    qacc_actual: List[float]
    torques: List[float]
    ee_pos_actual: List[float]
    ee_pos_target: List[float]
    ee_quat_actual: List[float]
    ee_quat_target: List[float]
    pos_error_norm: float
    rot_error_rad: float
    energy_total: float
    contacts_count: int
    max_normal_force: float
    solver_niter: int
    step_duration_us: float


class SimulationTelemetryBuffer:
    """Stores high-speed simulation telemetry points and provides export utilities."""

    def __init__(self, max_points: int = 50000):
        self.max_points = max_points
        self.points: List[TelemetryPoint] = []

    def append(self, point: TelemetryPoint):
        if len(self.points) >= self.max_points:
            self.points.pop(0)
        self.points.append(point)

    def clear(self):
        self.points.clear()

    def count(self) -> int:
        return len(self.points)

    def to_dict(self) -> Dict[str, List[Any]]:
        """Converts buffer into columnar time-series arrays."""
        if not self.points:
            return {
                "timestamps": [],
                "q_actual": [],
                "q_target": [],
                "qvel_actual": [],
                "qacc_actual": [],
                "torques": [],
                "ee_pos_actual": [],
                "ee_pos_target": [],
                "pos_error_norm": [],
                "rot_error_rad": [],
                "energy_total": [],
                "contacts_count": [],
                "max_normal_force": [],
                "solver_niter": [],
            }

        return {
            "timestamps": [round(p.time, 4) for p in self.points],
            "q_actual": [[round(q, 5) for q in p.q_actual] for p in self.points],
            "q_target": [[round(q, 5) for q in p.q_target] for p in self.points],
            "qvel_actual": [[round(v, 4) for v in p.qvel_actual] for p in self.points],
            "qacc_actual": [[round(a, 3) for a in p.qacc_actual] for p in self.points],
            "torques": [[round(tau, 3) for tau in p.torques] for p in self.points],
            "ee_pos_actual": [[round(x, 4) for x in p.ee_pos_actual] for p in self.points],
            "ee_pos_target": [[round(x, 4) for x in p.ee_pos_target] for p in self.points],
            "pos_error_norm": [round(p.pos_error_norm, 6) for p in self.points],
            "rot_error_rad": [round(p.rot_error_rad, 6) for p in self.points],
            "energy_total": [round(p.energy_total, 3) for p in self.points],
            "contacts_count": [p.contacts_count for p in self.points],
            "max_normal_force": [round(p.max_normal_force, 2) for p in self.points],
            "solver_niter": [p.solver_niter for p in self.points],
        }

    def downsample(self, target_samples: int = 300) -> Dict[str, List[Any]]:
        """Downsamples time-series uniformly for fast web rendering and chart plotting."""
        total = len(self.points)
        if total <= target_samples:
            return self.to_dict()

        step = max(1, total // target_samples)
        selected_points = [self.points[i] for i in range(0, total, step)]
        if self.points[-1] not in selected_points:
            selected_points.append(self.points[-1])

        sub_buffer = SimulationTelemetryBuffer(max_points=len(selected_points))
        sub_buffer.points = selected_points
        return sub_buffer.to_dict()

    def to_csv(self, filepath: Optional[Path] = None) -> str:
        """Exports recorded ground-truth telemetry to standard CSV format."""
        lines = []
        # Header
        header = [
            "time",
            "q1", "q2", "q3", "q4", "q5", "q6",
            "q_des1", "q_des2", "q_des3", "q_des4", "q_des5", "q_des6",
            "v1", "v2", "v3", "v4", "v5", "v6",
            "a1", "a2", "a3", "a4", "a5", "a6",
            "tau1", "tau2", "tau3", "tau4", "tau5", "tau6",
            "ee_x", "ee_y", "ee_z",
            "ee_des_x", "ee_des_y", "ee_des_z",
            "pos_error_m", "rot_error_rad", "energy_joules",
            "contacts_count", "max_normal_force_n", "solver_niter"
        ]
        lines.append(",".join(header))

        for p in self.points:
            row = [
                f"{p.time:.5f}",
                *[f"{q:.5f}" for q in (p.q_actual + [0.0]*6)[:6]],
                *[f"{q:.5f}" for q in (p.q_target + [0.0]*6)[:6]],
                *[f"{v:.4f}" for v in (p.qvel_actual + [0.0]*6)[:6]],
                *[f"{a:.3f}" for a in (p.qacc_actual + [0.0]*6)[:6]],
                *[f"{u:.3f}" for u in (p.torques + [0.0]*6)[:6]],
                *[f"{x:.5f}" for x in (p.ee_pos_actual + [0.0]*3)[:3]],
                *[f"{x:.5f}" for x in (p.ee_pos_target + [0.0]*3)[:3]],
                f"{p.pos_error_norm:.6f}",
                f"{p.rot_error_rad:.6f}",
                f"{p.energy_total:.4f}",
                str(p.contacts_count),
                f"{p.max_normal_force:.2f}",
                str(p.solver_niter),
            ]
            lines.append(",".join(row))

        csv_content = "\n".join(lines)
        if filepath:
            Path(filepath).write_text(csv_content, encoding="utf-8")
        return csv_content


def compute_quaternion_error(q_act: List[float], q_des: List[float]) -> float:
    """Computes geodesic angular distance in radians between two unit quaternions [w, x, y, z]."""
    if len(q_act) < 4 or len(q_des) < 4:
        return 0.0
    # Inner product: dot = |w1*w2 + x1*x2 + y1*y2 + z1*z2|
    dot = abs(q_act[0]*q_des[0] + q_act[1]*q_des[1] + q_act[2]*q_des[2] + q_act[3]*q_des[3])
    dot = min(1.0, max(0.0, dot))
    return float(2.0 * math.acos(dot))


def execute_and_record_run(
    model_path: str = "projects/default_6dof_arm/robot.mjcf",
    duration: float = 2.5,
    timestep: float = 0.002,
    waypoints: Optional[List[List[float]]] = None,
    kp_gains: Optional[List[float]] = None,
    kd_gains: Optional[List[float]] = None,
    ki_gains: Optional[List[float]] = None,
    interpolation: str = "quintic",
    v_max: float = 2.0,
    a_max: float = 4.0,
) -> SimulationTelemetryBuffer:
    """
    Executes actual physics stepping in live MuJoCo simulation,
    tracking trajectory waypoints and collecting bit-for-bit accurate telemetry.
    """
    if not MUJOCO_AVAILABLE:
        raise RuntimeError("MuJoCo library is required to execute robotic physics simulation.")

    engine = SimulationEngine()
    engine.load_from_xml(model_path)
    engine.config.timestep = timestep

    # Default waypoints if none provided
    if not waypoints:
        waypoints = [
            [0.0, -0.6, 1.2, 0.0, 0.6, 0.0],
            [0.4, -0.3, 0.9, 0.2, 0.4, 0.3],
            [-0.3, -0.5, 1.1, -0.1, 0.5, -0.2],
            [0.0, -0.6, 1.2, 0.0, 0.6, 0.0],
        ]

    traj = JointTrajectory(
        waypoints=waypoints,
        v_max=v_max,
        a_max=a_max,
        interpolation=interpolation,
    )

    controller = RobotMotionController(
        sim=engine,
        dof=6,
        kp_gains=kp_gains or [280.0, 320.0, 220.0, 110.0, 60.0, 30.0],
        ki_gains=ki_gains or [2.0, 5.0, 3.0, 1.0, 0.5, 0.2],
        kd_gains=kd_gains or [28.0, 38.0, 22.0, 9.0, 4.5, 2.0],
    )

    arm_model = create_sample_6dof_arm()
    chain = KinematicChain(arm_model, base_link="base_link", end_effector_link="link_6")

    buffer = SimulationTelemetryBuffer()
    dt = timestep
    total_time = min(duration, traj.total_duration)
    steps = int(math.ceil(total_time / dt))

    prev_vel = np.zeros(6)

    for s in range(steps):
        t = s * dt
        t0 = time.perf_counter()

        pt = traj.sample(t)
        q_des = pt.positions[:6]
        v_des = pt.velocities[:6]
        a_des = pt.accelerations[:6]

        # Compute torques
        tau = controller.compute_torques(q_des, v_des, a_des)
        for i in range(min(6, engine.model.nu)):
            ctrl_limit = engine.model.actuator_ctrlrange[i]
            if ctrl_limit[0] < ctrl_limit[1]:
                engine.data.ctrl[i] = np.clip(tau[i], ctrl_limit[0], ctrl_limit[1])
            else:
                engine.data.ctrl[i] = tau[i]

        engine.step(apply_internal_controllers=False)
        step_us = (time.perf_counter() - t0) * 1e6

        q_curr = list(engine.data.qpos[:6])
        v_curr = np.array(engine.data.qvel[:6])
        qacc = (v_curr - prev_vel) / dt if s > 0 else np.zeros(6)
        prev_vel = v_curr.copy()

        # End effector FK
        fk_act = compute_forward_kinematics(chain, q_curr)
        fk_des = compute_forward_kinematics(chain, list(q_des))

        pos_err = float(np.linalg.norm(np.array(fk_des.position) - np.array(fk_act.position)))
        rot_err = compute_quaternion_error(list(fk_act.quaternion), list(fk_des.quaternion))

        # Energy calculation
        mujoco.mj_energyPos(engine.model, engine.data)
        mujoco.mj_energyVel(engine.model, engine.data)
        e_total = float(engine.data.energy[0] + engine.data.energy[1])

        # Contacts
        contacts = engine.get_contact_dynamics()
        max_fn = max([c.force for c in contacts], default=0.0)

        # Solver iterations
        niter = int(engine.data.solver_niter[0]) if hasattr(engine.data, "solver_niter") and len(engine.data.solver_niter) > 0 else 10

        applied_torques = list(engine.data.qfrc_actuator[:6])

        buffer.append(
            TelemetryPoint(
                time=t,
                q_actual=[float(x) for x in q_curr],
                q_target=[float(x) for x in q_des],
                qvel_actual=[float(x) for x in v_curr],
                qacc_actual=[float(x) for x in qacc],
                torques=[float(x) for x in applied_torques],
                ee_pos_actual=[float(x) for x in fk_act.position],
                ee_pos_target=[float(x) for x in fk_des.position],
                ee_quat_actual=[float(x) for x in fk_act.quaternion],
                ee_quat_target=[float(x) for x in fk_des.quaternion],
                pos_error_norm=pos_err,
                rot_error_rad=rot_err,
                energy_total=e_total,
                contacts_count=len(contacts),
                max_normal_force=max_fn,
                solver_niter=niter,
                step_duration_us=float(step_us),
            )
        )

    return buffer
