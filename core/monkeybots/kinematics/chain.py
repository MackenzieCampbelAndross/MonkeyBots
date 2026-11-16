"""
MonkeyBots Kinematic Chain Analysis and Representation.

Extracts serial kinematic chains from general tree-structured RobotModels,
identifying active degrees of freedom, joint limits, axes, and link frames.
"""

from typing import List, Dict, Optional, Tuple
import numpy as np

from ..models.robot import RobotModel, Joint, Link, JointType
from .transforms import (
    euler_to_rotation_matrix,
    homogeneous_transform,
    axis_angle_to_rotation_matrix,
    normalize_vector,
)


class ChainElement:
    """Represents a single joint-link stage in a serial kinematic chain."""

    def __init__(self, joint: Joint, child_link: Link):
        self.joint = joint
        self.child_link = child_link
        self.name = joint.name
        self.joint_type = joint.type
        self.parent_link_name = joint.parent
        self.child_link_name = child_link.name
        self.axis = normalize_vector(joint.axis)
        
        # Origin relative to parent link frame
        xyz = joint.origin.xyz if joint.origin else [0.0, 0.0, 0.0]
        rpy = joint.origin.rpy if joint.origin else [0.0, 0.0, 0.0]
        R_orig = euler_to_rotation_matrix(rpy[0], rpy[1], rpy[2])
        self.T_origin = homogeneous_transform(R_orig, xyz)

        # Limits
        if joint.limits:
            self.lower_limit = float(joint.limits.lower)
            self.upper_limit = float(joint.limits.upper)
            self.max_velocity = float(joint.limits.velocity)
            self.max_effort = float(joint.limits.effort)
        else:
            self.lower_limit = -np.pi if joint.type != JointType.PRISMATIC else -1.0
            self.upper_limit = np.pi if joint.type != JointType.PRISMATIC else 1.0
            self.max_velocity = 5.0
            self.max_effort = 100.0

    @property
    def is_active(self) -> bool:
        """True if the joint possesses a degree of freedom (revolute, continuous, prismatic)."""
        return self.joint_type in (JointType.REVOLUTE, JointType.CONTINUOUS, JointType.PRISMATIC)

    def joint_transform(self, q: float) -> np.ndarray:
        """
        Computes the relative SE(3) transformation produced by joint displacement q.
        T_rel = T_origin * T_joint(q)
        """
        T_j = np.eye(4, dtype=np.float64)
        if self.joint_type in (JointType.REVOLUTE, JointType.CONTINUOUS):
            R = axis_angle_to_rotation_matrix(self.axis, q)
            T_j[0:3, 0:3] = R
        elif self.joint_type == JointType.PRISMATIC:
            T_j[0:3, 3] = self.axis * q
        # FIXED joints remain identity
        return self.T_origin @ T_j


class KinematicChain:
    """
    Serial kinematic chain connecting a base link to a target end-effector link.
    Supports forward kinematics, frame extraction, and parameter queries.
    """

    def __init__(self, robot: RobotModel, base_link: Optional[str] = None, end_effector_link: Optional[str] = None):
        self.robot = robot
        self.base_link = base_link or robot.root_link
        self.end_effector_link = end_effector_link or self._find_default_leaf()
        
        self.elements: List[ChainElement] = []
        self._build_chain()

        self.active_elements: List[ChainElement] = [elem for elem in self.elements if elem.is_active]
        self.dof = len(self.active_elements)
        self.joint_names = [elem.name for elem in self.active_elements]
        self.lower_limits = np.array([elem.lower_limit for elem in self.active_elements], dtype=np.float64)
        self.upper_limits = np.array([elem.upper_limit for elem in self.active_elements], dtype=np.float64)

    def _find_default_leaf(self) -> str:
        """Locates the furthest leaf link in the robot hierarchy."""
        # Find links with no children
        parent_links = {j.parent for j in self.robot.joints.values()}
        child_links = {j.child for j in self.robot.joints.values()}
        leaves = child_links - parent_links
        if leaves:
            # Pick a link containing 'ee', 'tool', or the last alphabetical
            for leaf in leaves:
                if any(k in leaf.lower() for k in ["ee", "tool", "flange", "hand", "tip"]):
                    return leaf
            return sorted(list(leaves))[-1]
        # Fallback to the last defined link
        return list(self.robot.links.keys())[-1]

    def _build_chain(self):
        """Builds ordered sequence of joints and links from base_link to end_effector_link."""
        # Backward search from end_effector_link to base_link
        current = self.end_effector_link
        reversed_chain: List[Tuple[Joint, Link]] = []

        # Map child link to incoming joint
        child_to_joint: Dict[str, Joint] = {j.child: j for j in self.robot.joints.values()}

        while current != self.base_link:
            if current not in child_to_joint:
                raise ValueError(
                    f"Kinematic chain disconnected: link '{current}' cannot reach base link '{self.base_link}'."
                )
            joint = child_to_joint[current]
            child_link = self.robot.links[current]
            reversed_chain.append((joint, child_link))
            current = joint.parent

        for joint, child_link in reversed(reversed_chain):
            self.elements.append(ChainElement(joint, child_link))

    def clamp_to_limits(self, q: np.ndarray) -> np.ndarray:
        """Clamps a joint position vector q to the physical joint limits."""
        q_arr = np.asarray(q, dtype=np.float64)
        return np.clip(q_arr, self.lower_limits, self.upper_limits)

    def is_within_limits(self, q: np.ndarray, tol: float = 1e-4) -> bool:
        """Checks if configuration q is within physical joint limits."""
        q_arr = np.asarray(q, dtype=np.float64)
        return bool(np.all(q_arr >= self.lower_limits - tol) and np.all(q_arr <= self.upper_limits + tol))
