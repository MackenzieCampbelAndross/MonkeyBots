"""
Redundant 7-DOF Inverse Kinematics Engine with Null-Space Optimization
Implements primary task projection and secondary gradient-based optimization
(joint limit avoidance, manipulability maximization).
"""

import numpy as np
from typing import List, Optional, Tuple, Callable


class RedundantIKSolver:
    """Solves inverse kinematics for n > 6 DOF manipulators using null-space projection."""

    def __init__(self, dof: int = 7):
        self.dof = dof

    def compute_null_space_projector(self, J: np.ndarray, damping: float = 0.01) -> Tuple[np.ndarray, np.ndarray]:
        """Calculates damped pseudo-inverse J_dagger and null-space projection matrix (I - J_dagger * J)."""
        m, n = J.shape
        # Damped pseudo-inverse
        JJT = J @ J.T + (damping ** 2) * np.eye(m)
        J_dagger = J.T @ np.linalg.inv(JJT)
        N = np.eye(n) - J_dagger @ J
        return J_dagger, N

    def joint_limit_avoidance_gradient(
        self, q: np.ndarray, q_min: np.ndarray, q_max: np.ndarray, gain: float = 1.0
    ) -> np.ndarray:
        """
        Gradient of secondary objective function H(q) that penalizes joint limit proximity:
        H(q) = sum ( (q_i - q_mid_i) / (q_max_i - q_min_i) )^2
        """
        q_mid = 0.5 * (q_max + q_min)
        q_range = q_max - q_min
        grad = -gain * 2.0 * (q - q_mid) / (q_range ** 2)
        return grad

    def solve_step(
        self,
        q_current: np.ndarray,
        J: np.ndarray,
        v_task: np.ndarray,
        secondary_gradient: Optional[np.ndarray] = None,
        damping: float = 0.01,
    ) -> np.ndarray:
        """
        Calculates one joint velocity step:
        q_dot = J_dagger * v_task + N * grad_secondary
        """
        J_dagger, N = self.compute_null_space_projector(J, damping=damping)
        q_dot_primary = J_dagger @ v_task
        if secondary_gradient is not None:
            q_dot_secondary = N @ secondary_gradient
            return q_dot_primary + q_dot_secondary
        return q_dot_primary


def compute_adaptive_damping(J: np.ndarray, lambda_max: float = 0.05, epsilon: float = 0.02) -> float:
    """Calculates adaptive Levenberg-Marquardt damping based on smallest singular value."""
    s = np.linalg.svd(J, compute_uv=False)
    sigma_min = float(s[-1]) if len(s) > 0 else 0.0
    if sigma_min >= epsilon:
        return 0.0
    return float(lambda_max * (1.0 - (sigma_min / epsilon) ** 2))
