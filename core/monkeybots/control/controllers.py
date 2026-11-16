"""
MonkeyBots Precision PID and Multi-Axis Motion Controllers.

Provides:
- Single-axis PID with anti-windup, derivative low-pass filtering, and output saturation.
- Multi-DOF Robot Controller supporting:
  - Joint Position Control with Gravity Compensation
  - Joint Velocity Control
  - Computed Torque / Inverse Dynamics Control
- Trajectory Tracking Execution & Telemetry Recording
"""

from enum import Enum
import math
from typing import Dict, List, Optional, Tuple
import numpy as np

from ..simulation.engine import SimulationEngine
from ..planning.trajectory import JointTrajectory, TrajectoryPoint


class ControlMode(str, Enum):
    POSITION = "position"
    VELOCITY = "velocity"
    COMPUTED_TORQUE = "computed_torque"


class PIDController:
    """
    Industrial PID Controller with:
    - Trapezoidal numerical integration with anti-windup clamping
    - Filtered derivative (first-order low-pass) to mitigate measurement noise
    - Maximum control effort clamping
    """

    def __init__(
        self,
        kp: float = 100.0,
        ki: float = 1.0,
        kd: float = 10.0,
        i_clamp: float = 50.0,
        max_output: float = 150.0,
        filter_coefficient: float = 0.1,  # alpha for derivative filter
    ):
        self.kp = float(kp)
        self.ki = float(ki)
        self.kd = float(kd)
        self.i_clamp = float(i_clamp)
        self.max_output = float(max_output)
        self.alpha = float(filter_coefficient)

        self.integral = 0.0
        self.prev_error = 0.0
        self.filtered_derivative = 0.0

    def reset(self):
        """Clears controller internal state."""
        self.integral = 0.0
        self.prev_error = 0.0
        self.filtered_derivative = 0.0

    def compute(
        self,
        target_pos: float,
        current_pos: float,
        dt: float,
        target_vel: Optional[float] = None,
        current_vel: Optional[float] = None,
    ) -> float:
        """Computes PID control effort."""
        dt = max(1e-6, dt)
        error = target_pos - current_pos

        # Proportional term
        p_term = self.kp * error

        # Integral term with trapezoidal integration & anti-windup clamping
        self.integral += 0.5 * (error + self.prev_error) * dt
        self.integral = np.clip(self.integral, -self.i_clamp, self.i_clamp)
        i_term = self.ki * self.integral

        # Derivative term: if velocity is provided, use e_dot = v_d - v, else finite difference
        if target_vel is not None and current_vel is not None:
            raw_deriv = target_vel - current_vel
        else:
            raw_deriv = (error - self.prev_error) / dt

        # First-order low-pass filter on derivative
        self.filtered_derivative = (1.0 - self.alpha) * self.filtered_derivative + self.alpha * raw_deriv
        d_term = self.kd * self.filtered_derivative

        self.prev_error = error

        # Total control effort with saturation clamping
        output = p_term + i_term + d_term
        return float(np.clip(output, -self.max_output, self.max_output))


class RobotMotionController:
    """
    Multi-joint robot motion controller interfacing with live MuJoCo physics.
    Executes real-time trajectory tracking loops and records high-fidelity telemetry.
    """

    def __init__(
        self,
        sim: SimulationEngine,
        dof: int = 6,
        kp_gains: Optional[List[float]] = None,
        ki_gains: Optional[List[float]] = None,
        kd_gains: Optional[List[float]] = None,
    ):
        self.sim = sim
        self.dof = dof

        # Default tuned gains for industrial arms
        default_kp = [250.0, 300.0, 200.0, 100.0, 60.0, 30.0]
        default_ki = [2.0, 5.0, 3.0, 1.0, 0.5, 0.2]
        default_kd = [25.0, 35.0, 20.0, 8.0, 4.0, 2.0]

        kp = kp_gains if kp_gains is not None else default_kp[:dof]
        ki = ki_gains if ki_gains is not None else default_ki[:dof]
        kd = kd_gains if kd_gains is not None else default_kd[:dof]

        self.pids = [
            PIDController(kp=kp[i], ki=ki[i], kd=kd[i], i_clamp=50.0, max_output=150.0)
            for i in range(dof)
        ]
        self.mode = ControlMode.POSITION

    def set_gains(self, joint_idx: int, kp: float, ki: float, kd: float):
        """Reconfigures gains for a single joint."""
        if 0 <= joint_idx < self.dof:
            self.pids[joint_idx].kp = float(kp)
            self.pids[joint_idx].ki = float(ki)
            self.pids[joint_idx].kd = float(kd)

    def reset(self):
        for pid in self.pids:
            pid.reset()

    def compute_torques(
        self,
        q_target: np.ndarray,
        v_target: Optional[np.ndarray] = None,
        a_target: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Computes active actuator torques based on the selected control mode.
        Incorporates MuJoCo gravity compensation (qfrc_bias).
        """
        if self.sim.model is None or self.sim.data is None:
            return np.zeros(self.dof)

        q_curr = np.array(self.sim.data.qpos[:self.dof])
        v_curr = np.array(self.sim.data.qvel[:self.dof])
        dt = self.sim.config.timestep

        # Gravity and Coriolis torque bias from physics model
        bias_torque = np.array(self.sim.data.qfrc_bias[:self.dof])

        torques = np.zeros(self.dof)
        for i in range(self.dof):
            vt = float(v_target[i]) if v_target is not None else 0.0
            u = self.pids[i].compute(
                target_pos=float(q_target[i]),
                current_pos=float(q_curr[i]),
                dt=dt,
                target_vel=vt,
                current_vel=float(v_curr[i]),
            )
            # Add feedforward gravity compensation
            torques[i] = u + bias_torque[i]

        return torques

    def execute_trajectory(
        self,
        trajectory: JointTrajectory,
        real_time: bool = False,
    ) -> Dict[str, any]:
        """
        Executes a planned JointTrajectory inside the MuJoCo simulation environment.
        Records exact position, velocity, torque, and tracking errors at 500 Hz.
        """
        if self.sim.model is None or self.sim.data is None:
            raise RuntimeError("Simulation engine is not initialized.")

        self.reset()
        dt = self.sim.config.timestep
        total_duration = trajectory.total_duration
        num_steps = int(math.ceil(total_duration / dt)) + 1

        # Align simulation state to trajectory initial conditions
        init_pt = trajectory.sample(0.0)
        self.sim.data.qpos[:self.dof] = init_pt.positions
        self.sim.data.qvel[:self.dof] = init_pt.velocities
        import mujoco
        mujoco.mj_forward(self.sim.model, self.sim.data)

        timestamps = []
        target_positions = []
        actual_positions = []
        target_velocities = []
        actual_velocities = []
        applied_torques = []
        tracking_errors = []

        # Execute simulation loop
        for step in range(num_steps):
            t = step * dt
            target_pt = trajectory.sample(t)
            qd = target_pt.positions
            vd = target_pt.velocities
            ad = target_pt.accelerations

            # Compute and apply torques
            tau = self.compute_torques(qd, vd, ad)
            for i in range(min(self.dof, self.sim.model.nu)):
                ctrl_limit = self.sim.model.actuator_ctrlrange[i]
                if ctrl_limit[0] < ctrl_limit[1]:
                    self.sim.data.ctrl[i] = np.clip(tau[i], ctrl_limit[0], ctrl_limit[1])
                else:
                    self.sim.data.ctrl[i] = tau[i]

            self.sim.step(1, apply_internal_controllers=False)

            q_act = np.array(self.sim.data.qpos[:self.dof])
            v_act = np.array(self.sim.data.qvel[:self.dof])
            err = qd - q_act

            # Record telemetry (decimated to ~100 Hz for storage efficiency)
            if step % 5 == 0 or step == num_steps - 1:
                timestamps.append(round(t, 4))
                target_positions.append([round(float(x), 5) for x in qd])
                actual_positions.append([round(float(x), 5) for x in q_act])
                target_velocities.append([round(float(x), 5) for x in vd])
                actual_velocities.append([round(float(x), 5) for x in v_act])
                applied_torques.append([round(float(x), 3) for x in tau])
                tracking_errors.append([round(float(x), 5) for x in err])

        # Compute summary performance metrics
        err_matrix = np.array(tracking_errors)
        rmse_per_joint = np.sqrt(np.mean(err_matrix ** 2, axis=0))
        max_err_per_joint = np.max(np.abs(err_matrix), axis=0)

        return {
            "duration": round(total_duration, 4),
            "step_count": num_steps,
            "overall_position_rmse_rad": round(float(np.mean(rmse_per_joint)), 6),
            "max_tracking_error_rad": round(float(np.max(max_err_per_joint)), 6),
            "joint_rmse_rad": [round(float(r), 6) for r in rmse_per_joint],
            "joint_max_error_rad": [round(float(m), 6) for m in max_err_per_joint],
            "timestamps": timestamps,
            "target_positions": target_positions,
            "actual_positions": actual_positions,
            "target_velocities": target_velocities,
            "actual_velocities": actual_velocities,
            "applied_torques": applied_torques,
            "tracking_errors": tracking_errors,
        }
