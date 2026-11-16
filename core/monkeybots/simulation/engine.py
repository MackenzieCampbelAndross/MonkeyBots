"""
MonkeyBots High-Fidelity Physics Simulation Engine
Wraps DeepMind MuJoCo with deterministic stepping, numerical divergence protection,
energy accounting, and real-time state telemetry.
"""

import math
import time
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Callable, Union, Any
from pydantic import BaseModel, Field

import mujoco
from server.monkeybots_server.schemas.telemetry import TelemetryFrame, Pose3D, ContactInfo
from server.monkeybots_server.utils.logger import get_logger
from .collision import CollisionTracker, ContactCategory, ContactPointData, CollisionEvent

logger = get_logger("physics_engine")


class SimulationConfig(BaseModel):
    timestep: float = Field(default=0.002, ge=0.0001, le=0.02, description="Integration timestep (s)")
    gravity: List[float] = Field(default_factory=lambda: [0.0, 0.0, -9.81], description="[gx, gy, gz]")
    integrator: str = Field(default="RK4", description="RK4, Euler, or implicit")
    iterations: int = Field(default=50, ge=1, le=500, description="Constraint solver max iterations")
    tolerance: float = Field(default=1e-6, ge=1e-12, le=1e-2, description="Constraint solver tolerance")
    speed_multiplier: float = Field(default=1.0, ge=0.1, le=10.0, description="Simulation speed factor")


class SimulationEngine:
    """Core physics simulation orchestrator wrapping MuJoCo MjModel and MjData."""

    def __init__(self, config: Optional[SimulationConfig] = None):
        self.config = config or SimulationConfig()
        self.model: Optional[mujoco.MjModel] = None
        self.data: Optional[mujoco.MjData] = None
        self.status: str = "IDLE"  # IDLE, RUNNING, PAUSED, DIVERGED

        # Initial state caches for reset
        self._initial_qpos: Optional[np.ndarray] = None
        self._initial_qvel: Optional[np.ndarray] = None

        # Timing & Real-time factor metrics
        self.step_count: int = 0
        self.sim_time: float = 0.0
        self._last_step_wall_time: float = time.perf_counter()
        self.real_time_factor: float = 1.0
        self.last_step_latency_ms: float = 1.2

        # Actuator command buffers
        self._target_qpos: Optional[np.ndarray] = None
        self._feedforward_torque: Optional[np.ndarray] = None

        # Internal PID control gains
        self.kp = 350.0
        self.kd = 25.0
        self.ki = 0.5
        self._integral_error: Optional[np.ndarray] = None

        # Gripper control states
        self._gripper_force: float = 0.0
        self._gripper_target_pos: Optional[float] = None

        # Real-time collision detection and dynamic event logger
        self.collision_tracker = CollisionTracker()

    def load_from_xml(self, xml_content: Union[str, Path]):
        """Loads and compiles an MJCF XML model string or file path directly into MuJoCo."""
        try:
            path = Path(xml_content)
            if path.exists() and path.is_file():
                content = path.read_text(encoding="utf-8")
            else:
                content = str(xml_content)
            self.model = mujoco.MjModel.from_xml_string(content)
            self.data = mujoco.MjData(self.model)

            # Apply simulation parameters
            self.model.opt.timestep = self.config.timestep
            self.model.opt.gravity[:] = self.config.gravity

            if self.config.integrator == "Euler":
                self.model.opt.integrator = mujoco.mjtIntegrator.mjINT_EULER
            elif self.config.integrator == "implicit":
                self.model.opt.integrator = mujoco.mjtIntegrator.mjINT_IMPLICITFAST
            else:
                self.model.opt.integrator = mujoco.mjtIntegrator.mjINT_RK4

            self.model.opt.iterations = self.config.iterations
            self.model.opt.tolerance = self.config.tolerance

            # Cache initial states
            self._initial_qpos = np.copy(self.data.qpos)
            self._initial_qvel = np.copy(self.data.qvel)

            # Initialize actuator targets
            nu = self.model.nu
            self._target_qpos = np.zeros(nu)
            self._feedforward_torque = np.zeros(nu)
            self._integral_error = np.zeros(nu)

            for i in range(nu):
                jnt_id = self.model.actuator_trnid[i, 0]
                if jnt_id >= 0:
                    q_adr = self.model.jnt_qposadr[jnt_id]
                    self._target_qpos[i] = float(self.data.qpos[q_adr])

            self.step_count = 0
            self.sim_time = 0.0
            self.status = "PAUSED"
            logger.info(f"Loaded MuJoCo model '{self.model.names}': nq={self.model.nq}, nv={self.model.nv}, geoms={self.model.ngeom}")
        except Exception as e:
            self.status = "ERROR"
            logger.error(f"Failed to compile MuJoCo model: {e}")
            raise RuntimeError(f"MuJoCo compilation error: {e}")

    def configure(self, config: SimulationConfig):
        """Applies updated runtime simulation configuration to active MuJoCo model."""
        self.config = config
        if self.model is not None:
            self.model.opt.timestep = self.config.timestep
            self.model.opt.gravity[:] = self.config.gravity
            if self.config.integrator == "Euler":
                self.model.opt.integrator = mujoco.mjtIntegrator.mjINT_EULER
            elif self.config.integrator == "implicit":
                self.model.opt.integrator = mujoco.mjtIntegrator.mjINT_IMPLICITFAST
            else:
                self.model.opt.integrator = mujoco.mjtIntegrator.mjINT_RK4
            self.model.opt.iterations = self.config.iterations
            self.model.opt.tolerance = self.config.tolerance

    def start(self):
        """Start or resume physics integration."""
        if self.model is not None:
            self.status = "RUNNING"
            self._last_step_wall_time = time.perf_counter()

    def pause(self):
        """Pause physics integration without clearing state."""
        self.status = "PAUSED"

    def resume(self):
        """Resume physics execution."""
        self.start()

    def stop(self):
        """Stop and pause physics integration."""
        self.status = "PAUSED"

    def reset(self):
        """Reset generalized coordinates, velocities, and timers to initial conditions."""
        if self.model is None or self.data is None:
            return

        mujoco.mj_resetData(self.model, self.data)
        if self._initial_qpos is not None:
            self.data.qpos[:] = self._initial_qpos
        if self._initial_qvel is not None:
            self.data.qvel[:] = self._initial_qvel

        if self._target_qpos is not None and self._initial_qpos is not None:
            for i in range(min(self.model.nu, len(self._target_qpos))):
                jnt_id = self.model.actuator_trnid[i, 0]
                if jnt_id >= 0:
                    q_adr = self.model.jnt_qposadr[jnt_id]
                    self._target_qpos[i] = float(self._initial_qpos[q_adr])
        if self._integral_error is not None:
            self._integral_error.fill(0.0)

        # Forward kinematics to refresh internal structures
        mujoco.mj_forward(self.model, self.data)
        self.collision_tracker.clear()

        self.sim_time = 0.0
        self.step_count = 0
        self.status = "PAUSED"
        logger.info("Simulation state reset to t=0.")

    def step(self, n: int = 1, apply_internal_controllers: bool = True) -> bool:
        """
        Advances the simulation by n integration steps (n * dt seconds).
        Applies internal joint PD/PID control torques if apply_internal_controllers is True.
        Returns True if successful, False if numerical instability was detected.
        """
        if self.model is None or self.data is None:
            return False

        dt = self.model.opt.timestep
        t_step_start = time.perf_counter()

        for _ in range(n):
            # Apply Joint Actuation / PID Controls if enabled
            if apply_internal_controllers:
                self._apply_joint_controllers(dt)

            # High-fidelity step
            mujoco.mj_step(self.model, self.data)
            self.step_count += 1
            self.sim_time += dt

            # Update dynamic collision tracking
            self.collision_tracker.update(self.model, self.data, self.sim_time, dt)

            # Numerical Divergence Protection
            is_stable, reason = self.check_numerical_stability()
            if not is_stable:
                self.status = "DIVERGED"
                logger.error(f"Simulation diverged at t={self.sim_time:.4f}s: {reason}")
                return False

        # Compute Real-Time Factor & Step Execution Latency
        now = time.perf_counter()
        elapsed_wall = now - self._last_step_wall_time
        if elapsed_wall > 0:
            sim_elapsed = n * dt
            instant_rtf = sim_elapsed / elapsed_wall
            self.real_time_factor = 0.95 * self.real_time_factor + 0.05 * instant_rtf
        self._last_step_wall_time = now
        self.last_step_latency_ms = max(0.01, round((now - t_step_start) * 1000.0, 3))

        return True

    def _apply_joint_controllers(self, dt: float):
        """Computes and applies feedback PD control torques to actuators."""
        if self.model.nu == 0 or self._target_qpos is None:
            return

        nu = self.model.nu
        for i in range(nu):
            act_name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, i) or ""
            if "gripper" in act_name.lower():
                self.data.ctrl[i] = self._gripper_force
                continue

            jnt_id = self.model.actuator_trnid[i, 0]
            if jnt_id < 0:
                continue

            q_adr = self.model.jnt_qposadr[jnt_id]
            v_adr = self.model.jnt_dofadr[jnt_id]

            target_q = self._target_qpos[i] if i < len(self._target_qpos) else self.data.qpos[q_adr]
            current_q = self.data.qpos[q_adr]
            current_v = self.data.qvel[v_adr]

            err = target_q - current_q
            if self._integral_error is not None and i < len(self._integral_error):
                self._integral_error[i] += err * dt
                self._integral_error[i] = np.clip(self._integral_error[i], -10.0, 10.0)
                int_term = self.ki * self._integral_error[i]
            else:
                int_term = 0.0

            u = self.kp * err - self.kd * current_v + int_term
            if self._feedforward_torque is not None and i < len(self._feedforward_torque):
                u += self._feedforward_torque[i]

            # Check actuator force limits
            ctrl_limit = self.model.actuator_ctrlrange[i]
            if ctrl_limit[0] < ctrl_limit[1]:
                self.data.ctrl[i] = np.clip(u, ctrl_limit[0], ctrl_limit[1])
            else:
                self.data.ctrl[i] = u

    def set_target_joint_positions(self, targets: List[float]):
        """Sets desired target joint positions for the internal actuators."""
        if self._target_qpos is not None:
            for i, val in enumerate(targets[: len(self._target_qpos)]):
                self._target_qpos[i] = val

    def set_joint_torques(self, torques: List[float]):
        """Sets direct feedforward joint torques."""
        if self._feedforward_torque is not None:
            for i, val in enumerate(torques[: len(self._feedforward_torque)]):
                self._feedforward_torque[i] = val

    def check_numerical_stability(self) -> Tuple[bool, str]:
        """Checks for NaN, Inf, or physical divergence in generalized coordinates and velocities."""
        if self.data is None:
            return True, "No data"

        if np.isnan(self.data.qpos).any():
            return False, "NaN detected in generalized coordinates (qpos)"
        if np.isnan(self.data.qvel).any():
            return False, "NaN detected in generalized velocities (qvel)"
        if np.isinf(self.data.qpos).any():
            return False, "Infinite values in generalized coordinates"
        if np.isinf(self.data.qvel).any():
            return False, "Infinite values in generalized velocities"

        # Check for unphysical explosion of velocity (> 1000 rad/s or m/s)
        max_vel = np.max(np.abs(self.data.qvel)) if len(self.data.qvel) > 0 else 0.0
        if max_vel > 1000.0:
            return False, f"Velocity explosion detected: {max_vel:.1f} rad/s"

        return True, "Stable"

    def get_contact_dynamics(self) -> List[ContactInfo]:
        """Extracts active contact points, normal contact forces, normals, friction, and slip state."""
        if self.model is None or self.data is None:
            return []

        dt = self.model.opt.timestep
        contact_points = self.collision_tracker.update(self.model, self.data, self.sim_time, dt)

        contacts: List[ContactInfo] = []
        for cp in contact_points:
            contacts.append(
                ContactInfo(
                    geom1=cp.geom1,
                    geom2=cp.geom2,
                    force=cp.normal_force,
                    distance=cp.distance,
                    position=cp.position,
                    normal=cp.normal,
                    friction_force=cp.friction_force,
                    category=cp.category.value,
                    slip_state=cp.slip_state,
                )
            )
        return contacts

    def set_gripper_force(self, force_n: float):
        """Sets grasping squeeze force on gripper actuators (N)."""
        self._gripper_force = float(force_n)
        if self.model is not None and self.data is not None:
            for i in range(self.model.nu):
                act_name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, i) or ""
                if "gripper" in act_name.lower():
                    self.data.ctrl[i] = self._gripper_force

    def get_gripper_state(self) -> Dict[str, Any]:
        """Returns gripper aperture width (m), finger normal forces, and grasping status."""
        if self.model is None or self.data is None:
            return {"width": 0.08, "left_force": 0.0, "right_force": 0.0, "is_grasping": False}

        left_force = 0.0
        right_force = 0.0
        contacts = self.collision_tracker.update(self.model, self.data, self.sim_time, self.model.opt.timestep)
        for c in contacts:
            pair = (c.geom1 + " " + c.geom2 + " " + c.body1 + " " + c.body2).lower()
            if "left" in pair and ("box" in pair or "object" in pair or "part" in pair):
                left_force += c.normal_force
            if "right" in pair and ("box" in pair or "object" in pair or "part" in pair):
                right_force += c.normal_force

        aperture = 0.08
        try:
            l_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "left_finger")
            r_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "right_finger")
            if l_id != -1 and r_id != -1:
                aperture = float(np.linalg.norm(self.data.xpos[l_id] - self.data.xpos[r_id]))
        except Exception:
            pass

        is_grasping = (left_force > 0.5 and right_force > 0.5)
        return {
            "width": round(aperture, 4),
            "left_force": round(left_force, 2),
            "right_force": round(right_force, 2),
            "is_grasping": is_grasping,
        }

    def get_collision_events(self, limit: int = 50) -> List[CollisionEvent]:
        """Returns recent dynamic collision events from the tracker."""
        return self.collision_tracker.get_events(limit=limit)

    def get_telemetry_frame(self) -> TelemetryFrame:
        """Assembles a high-frequency telemetry frame conforming to the IPC contract."""
        if self.model is None or self.data is None:
            return TelemetryFrame(
                sim_time=0.0,
                real_time_factor=1.0,
                step_count=0,
                joint_names=[],
                qpos=[],
                qvel=[],
                qtorque=[],
                status="IDLE",
            )

        nv = self.model.nv
        joint_names = [
            mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_JOINT, i) or f"joint_{i+1}"
            for i in range(nv)
        ]

        qpos_list = [round(float(q), 4) for q in self.data.qpos[:nv]]
        qvel_list = [round(float(v), 4) for v in self.data.qvel[:nv]]
        qtorque_list = [round(float(self.data.qfrc_actuator[i]), 2) for i in range(nv)]

        # Extract End-Effector / Flange Pose (Last body)
        ee_pose = None
        if self.model.nbody > 1:
            last_body_id = self.model.nbody - 1
            body_pos = self.data.xpos[last_body_id]
            body_quat = self.data.xquat[last_body_id]
            ee_pose = Pose3D(
                position=[round(float(body_pos[0]), 4), round(float(body_pos[1]), 4), round(float(body_pos[2]), 4)],
                quaternion=[round(float(body_quat[0]), 4), round(float(body_quat[1]), 4), round(float(body_quat[2]), 4), round(float(body_quat[3]), 4)],
            )

        contacts = self.get_contact_dynamics()

        return TelemetryFrame(
            sim_time=round(self.sim_time, 4),
            real_time_factor=round(self.real_time_factor, 2),
            step_count=self.step_count,
            joint_names=joint_names,
            qpos=qpos_list,
            qvel=qvel_list,
            qtorque=qtorque_list,
            end_effector=ee_pose,
            contacts=contacts,
            status=self.status,
        )

    def compute_energy(self) -> Dict[str, float]:
        """Calculates kinetic, potential, and total mechanical energy of the system."""
        if self.model is None or self.data is None:
            return {"kinetic": 0.0, "potential": 0.0, "total": 0.0}

        mujoco.mj_energyPos(self.model, self.data)
        mujoco.mj_energyVel(self.model, self.data)

        # MuJoCo stores energy in data.energy: [potential, kinetic]
        potential = float(self.data.energy[0])
        kinetic = float(self.data.energy[1])
        total = potential + kinetic
        return {"kinetic": kinetic, "potential": potential, "total": total}
