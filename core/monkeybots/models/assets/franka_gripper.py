"""
Franka Hand Parallel Gripper Specification
Bilateral finger actuation, finger contact geometries, and grasp friction parameters.
"""

from ..robot import (
    RobotModel, Link, Joint, Inertial, Origin, Geometry,
    GeometryType, Visual, Collision, JointType, JointLimits, JointDynamics
)
from ..inertia_calculator import calculate_box_inertia


def add_franka_hand(robot: RobotModel) -> RobotModel:
    """Attaches the official Franka Hand parallel gripper to panda_link7."""
    # Gripper body
    body_geom = Geometry(type=GeometryType.BOX, size=[0.08, 0.12, 0.06])
    body_ine = calculate_box_inertia([0.08, 0.12, 0.06], 0.73)
    robot.links["panda_hand"] = Link(
        name="panda_hand",
        inertial=Inertial(mass=0.73, origin=Origin(xyz=[0, 0, 0.03]), inertia=body_ine),
        visuals=[Visual(origin=Origin(xyz=[0, 0, 0.03]), geometry=body_geom)],
        collisions=[Collision(origin=Origin(xyz=[0, 0, 0.03]), geometry=body_geom)],
    )
    robot.joints["panda_hand_joint"] = Joint(
        name="panda_hand_joint", type=JointType.FIXED, parent="panda_link7", child="panda_hand",
        origin=Origin(xyz=[0, 0, 0.06], rpy=[0, 0, -0.785398]),
    )

    # Left finger
    finger_geom = Geometry(type=GeometryType.BOX, size=[0.02, 0.02, 0.04])
    finger_ine = calculate_box_inertia([0.02, 0.02, 0.04], 0.05)
    robot.links["panda_leftfinger"] = Link(
        name="panda_leftfinger",
        inertial=Inertial(mass=0.05, origin=Origin(xyz=[0, 0.01, 0.02]), inertia=finger_ine),
        visuals=[Visual(origin=Origin(xyz=[0, 0.01, 0.02]), geometry=finger_geom)],
        collisions=[Collision(origin=Origin(xyz=[0, 0.01, 0.02]), geometry=finger_geom)],
    )
    robot.joints["panda_finger_joint1"] = Joint(
        name="panda_finger_joint1", type=JointType.PRISMATIC, parent="panda_hand", child="panda_leftfinger",
        origin=Origin(xyz=[0, 0, 0.06]), axis=[0, 1, 0],
        limits=JointLimits(lower=0.0, upper=0.04, effort=20.0, velocity=0.2),
        dynamics=JointDynamics(damping=2.0, friction=0.8),
    )

    # Right finger
    robot.links["panda_rightfinger"] = Link(
        name="panda_rightfinger",
        inertial=Inertial(mass=0.05, origin=Origin(xyz=[0, -0.01, 0.02]), inertia=finger_ine),
        visuals=[Visual(origin=Origin(xyz=[0, -0.01, 0.02]), geometry=finger_geom)],
        collisions=[Collision(origin=Origin(xyz=[0, -0.01, 0.02]), geometry=finger_geom)],
    )
    robot.joints["panda_finger_joint2"] = Joint(
        name="panda_finger_joint2", type=JointType.PRISMATIC, parent="panda_hand", child="panda_rightfinger",
        origin=Origin(xyz=[0, 0, 0.06]), axis=[0, -1, 0],
        limits=JointLimits(lower=0.0, upper=0.04, effort=20.0, velocity=0.2),
        dynamics=JointDynamics(damping=2.0, friction=0.8),
    )
    return robot
