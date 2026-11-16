"""
MonkeyBots Robotics Kinematics Engine.
"""

from .transforms import (
    euler_to_rotation_matrix,
    rotation_matrix_to_euler,
    quaternion_from_rotation_matrix,
    quaternion_to_rotation_matrix,
    quaternion_multiply,
    quaternion_conjugate,
    quaternion_error,
    axis_angle_to_rotation_matrix,
    homogeneous_transform,
    transform_inverse,
    normalize_vector,
)
from .chain import KinematicChain, ChainElement
from .fk import compute_forward_kinematics, FKResult
from .jacobian import compute_geometric_jacobian, JacobianAnalysis
from .ik import IKSolver, IKSolverMethod, IKResult

__all__ = [
    "euler_to_rotation_matrix",
    "rotation_matrix_to_euler",
    "quaternion_from_rotation_matrix",
    "quaternion_to_rotation_matrix",
    "quaternion_multiply",
    "quaternion_conjugate",
    "quaternion_error",
    "axis_angle_to_rotation_matrix",
    "homogeneous_transform",
    "transform_inverse",
    "normalize_vector",
    "KinematicChain",
    "ChainElement",
    "compute_forward_kinematics",
    "FKResult",
    "compute_geometric_jacobian",
    "JacobianAnalysis",
    "IKSolver",
    "IKSolverMethod",
    "IKResult",
]
