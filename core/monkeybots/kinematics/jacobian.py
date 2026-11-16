"""
MonkeyBots Geometric Jacobian and Singularity Analysis Engine.

Computes the 6xN Geometric Jacobian matrix relating joint velocities to
end-effector linear and angular velocities:
v_ee = J_v * q_dot
omega_ee = J_omega * q_dot

Performs Singular Value Decomposition (SVD), Yoshikawa manipulability,
condition number, and singularity diagnostics.
"""

from typing import Dict, List, Tuple
import numpy as np

from .chain import KinematicChain
from .fk import compute_forward_kinematics
from ..models.robot import JointType


class JacobianAnalysis:
    """Holds Jacobian matrix and analytical singularity metrics."""

    def __init__(self, J: np.ndarray):
        self.J = J
        self.rows, self.cols = J.shape

        # SVD analysis
        U, S, Vt = np.linalg.svd(J, full_matrices=False)
        self.singular_values = S
        self.sigma_max = float(S[0]) if len(S) > 0 else 0.0
        self.sigma_min = float(S[-1]) if len(S) > 0 else 0.0
        
        # Condition number: kappa = sigma_max / sigma_min
        if self.sigma_min > 1e-12:
            self.condition_number = float(self.sigma_max / self.sigma_min)
        else:
            self.condition_number = float(1e9)

        # Yoshikawa Manipulability: sqrt(det(J * J^T)) = product of singular values
        self.manipulability = float(np.prod(S)) if len(S) > 0 else 0.0

        # Singularity thresholding: vanishing singular value, near-zero manipulability, or severe ill-conditioning
        self.is_singular = bool(self.sigma_min < 1e-3 or self.manipulability < 1e-4 or self.condition_number > 500.0)

    def diagnose_singularity(self, q: np.ndarray, chain: KinematicChain) -> List[str]:
        """Provides diagnostic descriptions of detected singular configurations."""
        warnings = []
        is_wrist_sing = bool(chain.dof >= 6 and abs(q[4]) < 0.03)

        if self.is_singular or is_wrist_sing:
            self.is_singular = True
            warnings.append(
                f"Singular configuration detected (Manipulability w={self.manipulability:.2e}, "
                f"Condition number kappa={self.condition_number:.1f}, sigma_min={self.sigma_min:.2e})"
            )

        # Check for wrist alignment (typical for 6-DOF arms when joint 5 is 0)
        if is_wrist_sing:
            warnings.append("Wrist Singularity: Axes of Joint 4 and Joint 6 are collinear (q5 ~= 0).")

        return warnings

    def to_dict(self) -> dict:
        return {
            "jacobian": [[round(float(val), 6) for val in row] for row in self.J],
            "singular_values": [round(float(s), 6) for s in self.singular_values],
            "manipulability": round(self.manipulability, 6),
            "condition_number": round(min(self.condition_number, 99999.0), 2),
            "is_singular": self.is_singular,
            "sigma_min": round(self.sigma_min, 6),
            "sigma_max": round(self.sigma_max, 6),
        }


def compute_geometric_jacobian(chain: KinematicChain, q: np.ndarray) -> JacobianAnalysis:
    """
    Computes 6xN Geometric Jacobian for active joints in chain at configuration q.
    J = [ J_v ]
        [ J_w ]
    where:
    For revolute joint i:
      J_v,i = z_{i-1} x (p_ee - p_{i-1})
      J_w,i = z_{i-1}
    For prismatic joint i:
      J_v,i = z_{i-1}
      J_w,i = 0
    """
    q_arr = np.asarray(q, dtype=np.float64)
    fk = compute_forward_kinematics(chain, q_arr)
    p_ee = fk.position

    dof = chain.dof
    J = np.zeros((6, dof), dtype=np.float64)

    active_joint_idx = 0
    for i, elem in enumerate(chain.elements):
        if not elem.is_active:
            continue

        p_joint = fk.joint_origins[i]
        z_axis = fk.joint_axes_world[i]

        if elem.joint_type in (JointType.REVOLUTE, JointType.CONTINUOUS):
            # J_v = z x (p_ee - p_joint)
            r = p_ee - p_joint
            J_v = np.cross(z_axis, r)
            J_w = z_axis
        elif elem.joint_type == JointType.PRISMATIC:
            J_v = z_axis
            J_w = np.zeros(3, dtype=np.float64)
        else:
            J_v = np.zeros(3, dtype=np.float64)
            J_w = np.zeros(3, dtype=np.float64)

        J[0:3, active_joint_idx] = J_v
        J[3:6, active_joint_idx] = J_w
        active_joint_idx += 1

    return JacobianAnalysis(J)
