"""
MonkeyBots Forward Kinematics (FK) Engine.

Computes exact SE(3) end-effector poses and intermediate link frames
along an arbitrary serial kinematic chain for any joint coordinate vector q.
"""

from typing import Dict, List, Optional
import numpy as np

from .chain import KinematicChain
from .transforms import (
    rotation_matrix_to_euler,
    quaternion_from_rotation_matrix,
    homogeneous_transform,
)


class FKResult:
    """Holds the complete forward kinematics output."""

    def __init__(
        self,
        T_end_effector: np.ndarray,
        link_transforms: Dict[str, np.ndarray],
        joint_origins: List[np.ndarray],
        joint_axes_world: List[np.ndarray],
    ):
        self.T = T_end_effector
        self.position = T_end_effector[0:3, 3]
        self.rotation_matrix = T_end_effector[0:3, 0:3]
        self.quaternion = quaternion_from_rotation_matrix(self.rotation_matrix)
        self.rpy = rotation_matrix_to_euler(self.rotation_matrix)
        self.link_transforms = link_transforms
        self.joint_origins = joint_origins
        self.joint_axes_world = joint_axes_world

    def to_dict(self) -> dict:
        """Converts result to JSON-serializable dictionary."""
        return {
            "position": [round(float(x), 6) for x in self.position],
            "quaternion": [round(float(x), 6) for x in self.quaternion],
            "rpy_rad": [round(float(x), 6) for x in self.rpy],
            "rpy_deg": [round(float(np.degrees(x)), 4) for x in self.rpy],
            "transform_matrix": [[round(float(val), 6) for val in row] for row in self.T],
            "link_transforms": {
                name: [[round(float(val), 6) for val in row] for row in mat]
                for name, mat in self.link_transforms.items()
            },
        }


def compute_forward_kinematics(chain: KinematicChain, q: Optional[np.ndarray] = None) -> FKResult:
    """
    Computes forward kinematics for the given kinematic chain.
    q: active joint angles/displacements. If None, defaults to zeros.
    """
    if q is None:
        q = np.zeros(chain.dof, dtype=np.float64)
    else:
        q = np.asarray(q, dtype=np.float64)
        if len(q) != chain.dof:
            raise ValueError(f"Joint vector dimension {len(q)} does not match chain DOF {chain.dof}.")

    # Cumulative transformation from base frame
    T_curr = np.eye(4, dtype=np.float64)
    link_transforms: Dict[str, np.ndarray] = {chain.base_link: T_curr.copy()}
    
    joint_origins: List[np.ndarray] = []
    joint_axes_world: List[np.ndarray] = []

    active_idx = 0
    for elem in chain.elements:
        if elem.is_active:
            q_val = float(q[active_idx])
            active_idx += 1
        else:
            q_val = 0.0

        # Transform to joint origin frame in world
        T_joint_origin = T_curr @ elem.T_origin
        joint_origins.append(T_joint_origin[0:3, 3])

        # Express joint axis in base/world frame
        R_joint = T_joint_origin[0:3, 0:3]
        axis_world = R_joint @ elem.axis
        joint_axes_world.append(axis_world / np.linalg.norm(axis_world))

        # Apply joint displacement
        T_curr = T_curr @ elem.joint_transform(q_val)
        link_transforms[elem.child_link_name] = T_curr.copy()

    return FKResult(
        T_end_effector=T_curr,
        link_transforms=link_transforms,
        joint_origins=joint_origins,
        joint_axes_world=joint_axes_world,
    )
