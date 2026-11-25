"""
Cartesian Impedance Controller
Computes joint torques for compliant end-effector interaction and posture stabilization.
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class ImpedanceGains:
    kp_trans: float = 800.0   # N/m
    kd_trans: float = 40.0    # N/(m/s)
    kp_rot: float = 60.0      # Nm/rad
    kd_rot: float = 5.0       # Nm/(rad/s)
    k_null: float = 10.0      # Posture stiffness
    d_null: float = 1.0       # Posture damping


class CartesianImpedanceController:
    """
    Implements standard task-space Cartesian impedance control:
    tau = J^T * (K_p * delta_x + D_p * delta_v) + (I - J^T * J_dagger^T) * tau_null + g(q)
    """

    def __init__(self, dof: int = 6, gains: Optional[ImpedanceGains] = None):
        self.dof = dof
        self.gains = gains or ImpedanceGains()

    def compute_torque(
        self,
        current_pos: np.ndarray,
        current_vel: np.ndarray,
        target_pos: np.ndarray,
        target_vel: np.ndarray,
        jacobian: np.ndarray,
        current_q: np.ndarray,
        nominal_q: np.ndarray,
        current_qd: np.ndarray,
        gravity_torque: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Calculates joint torques matching Cartesian impedance dynamics.
        """
        # Cartesian error: 3 translational, 3 rotational
        err_pos = np.zeros(6)
        err_pos[:3] = target_pos[:3] - current_pos[:3]
        if len(target_pos) >= 6 and len(current_pos) >= 6:
            err_pos[3:] = target_pos[3:] - current_pos[3:]

        err_vel = np.zeros(6)
        err_vel[:3] = target_vel[:3] - current_vel[:3]
        if len(target_vel) >= 6 and len(current_vel) >= 6:
            err_vel[3:] = target_vel[3:] - current_vel[3:]

        # Cartesian stiffness & damping matrices
        Kp = np.diag([
            self.gains.kp_trans, self.gains.kp_trans, self.gains.kp_trans,
            self.gains.kp_rot, self.gains.kp_rot, self.gains.kp_rot,
        ])
        Dp = np.diag([
            self.gains.kd_trans, self.gains.kd_trans, self.gains.kd_trans,
            self.gains.kd_rot, self.gains.kd_rot, self.gains.kd_rot,
        ])

        F_task = Kp @ err_pos + Dp @ err_vel
        tau_task = jacobian.T @ F_task

        # Null-space posture stabilization
        J_pinv = np.linalg.pinv(jacobian)
        null_proj = np.eye(self.dof) - jacobian.T @ J_pinv.T
        tau_null_des = self.gains.k_null * (nominal_q - current_q) - self.gains.d_null * current_qd
        tau_null = null_proj @ tau_null_des

        tau = tau_task + tau_null
        if gravity_torque is not None:
            tau += gravity_torque

        return tau
