"""
MonkeyBots High-Fidelity Physics Simulation Engine
Wraps DeepMind MuJoCo with deterministic stepping, numerical divergence protection,
energy accounting, and real-time state telemetry.
"""

import math
import time
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Callable, Union
from pydantic import BaseModel, Field

import mujoco
from server.monkeybots_server.schemas.telemetry import TelemetryFrame, Pose3D, ContactInfo
from server.monkeybots_server.utils.logger import get_logger

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

        # Actuator command buffers
        self._target_qpos: Optional[np.ndarray] = None
        self._feedforward_torque: Optional[np.ndarray] = None

        # Internal PID control gains
        self.kp = 350.0
        self.kd = 25.0
        self.ki = 0.5
        self._integral_error: Optional[np.ndarray] = None

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
            nv = self.model.nv
            self._target_qpos = np.copy(self.data.qpos[:nv])
            self._feedforward_torque = np.zeros(nv)
            self._integral_error = np.zeros(nv)

            self.step_count = 0
            self.sim_time = 0.0
            self.status = "PAUSED"
            logger.info(f"Loaded MuJoCo model '{self.model.names}': nq={self.model.nq}, nv={self.model.nv}, geoms={self.model.ngeom}")
        except Exception as e:
            self.status = "ERROR"
            logger.error(f"Failed to compile MuJoCo model: {e}")
            raise RuntimeError(f"MuJoCo compilation error: {e}")

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
            self._target_qpos[:] = self._initial_qpos[: len(self._target_qpos)]
        if self._integral_error is not None:
            self._integral_error.fill(0.0)

        # Forward kinematics to refresh internal structures
        mujoco.mj_forward(self.model, self.data)

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

        for _ in range(n):
            # Apply Joint Actuation / PID Controls if enabled
            if apply_internal_controllers:
                self._apply_joint_controllers(dt)

            # High-fidelity step
            mujoco.mj_step(self.model, self.data)
            self.step_count += 1
            self.sim_time += dt

            # Numerical Divergence Protection
            is_stable, reason = self.check_numerical_stability()
            if not is_stable:
                self.status = "DIVERGED"
                logger.error(f"Simulation diverged at t={self.sim_time:.4f}s: {reason}")
                return False

        # Compute Real-Time Factor
        now = time.perf_counter()
        elapsed_wall = now - self._last_step_wall_time
        if elapsed_wall > 0:
            sim_elapsed = n * dt
            instant_rtf = sim_elapsed / elapsed_wall
            self.real_time_factor = 0.95 * self.real_time_factor + 0.05 * instant_rtf
        self._last_step_wall_time = now

        return True

    def _apply_joint_controllers(self, dt: float):
        """Computes and applies feedback PD control torques to actuators."""
        if self.model.nu == 0 or self._target_qpos is None:
            return

        nu = self.model.nu
        nv = self.model.nv
        q = self.data.qpos[:nv]
        v = self.data.qvel[:nv]
        target_q = self._target_qpos[:nv]

        # Position error
        err = target_q - q
        if self._integral_error is not None:
            self._integral_error += err * dt
            # Clamp integral windup
            self._integral_error = np.clip(self._integral_error, -10.0, 10.0)

        # PD torque synthesis
        u = self.kp * err - self.kd * v
        if self._integral_error is not None:
            u += self.ki * self._integral_error

        # Add feedforward if present
        if self._feedforward_torque is not None:
            u += self._feedforward_torque[:nu]

        # Apply to control inputs
        for i in range(min(nu, len(u))):
            # Check actuator force limits
            ctrl_limit = self.model.actuator_ctrlrange[i]
            if ctrl_limit[0] < ctrl_limit[1]:
                self.data.ctrl[i] = np.clip(u[i], ctrl_limit[0], ctrl_limit[1])
            else:
                self.data.ctrl[i] = u[i]

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
        """Extracts active contact points, normal contact forces, and geom names."""
        if self.model is None or self.data is None:
            return []

        contacts: List[ContactInfo] = []
        ncon = self.data.ncon

        for i in range(ncon):
            con = self.data.contact[i]
            geom1_id = con.geom1
            geom2_id = con.geom2

            geom1_name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_GEOM, geom1_id) or f"geom_{geom1_id}"
            geom2_name = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_GEOM, geom2_id) or f"geom_{geom2_id}"

            # Calculate 6D contact force [normal, friction1, friction2, torque...]
            c_force = np.zeros(6, dtype=np.float64)
            mujoco.mj_contactForce(self.model, self.data, i, c_force)
            normal_force = float(abs(c_force[0]))

            contacts.append(
                ContactInfo(
                    geom1=geom1_name,
                    geom2=geom2_name,
                    force=round(normal_force, 2),
                    distance=round(float(con.dist), 4),
                    position=[round(float(p), 4) for p in con.pos],
                )
            )

        return contacts

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
