"""
Universal Robots UR5e 6-DOF Collaborative Robotic Manipulator
"""

import math
from ..robot import (
    RobotModel, Link, Joint, Inertial, Origin, Geometry,
    GeometryType, Visual, Collision, JointType, JointLimits, JointDynamics
)
from ..inertia_calculator import calculate_cylinder_inertia


def create_ur5e_robot() -> RobotModel:
    """Builds the canonical UR5e collaborative robot model."""
    links = {}
    joints = {}

    # Base link
    b_geom = Geometry(type=GeometryType.CYLINDER, radius=0.13, length=0.1)
    links["base_link"] = Link(
        name="base_link",
        inertial=Inertial(mass=4.0, origin=Origin(xyz=[0, 0, 0.05]), inertia=calculate_cylinder_inertia(0.13, 0.1, 4.0)),
        visuals=[Visual(origin=Origin(xyz=[0, 0, 0.05]), geometry=b_geom)],
        collisions=[Collision(origin=Origin(xyz=[0, 0, 0.05]), geometry=b_geom)],
    )

    # Joint 1: Shoulder Pan
    joints["shoulder_pan_joint"] = Joint(
        name="shoulder_pan_joint", type=JointType.REVOLUTE, parent="base_link", child="shoulder_link",
        origin=Origin(xyz=[0, 0, 0.1625]), axis=[0, 0, 1],
        limits=JointLimits(lower=-6.283, upper=6.283, effort=150.0, velocity=3.14),
        dynamics=JointDynamics(damping=1.2, friction=0.1),
    )
    s_geom = Geometry(type=GeometryType.CYLINDER, radius=0.08, length=0.15)
    links["shoulder_link"] = Link(
        name="shoulder_link",
        inertial=Inertial(mass=3.7, origin=Origin(xyz=[0, 0, 0]), inertia=calculate_cylinder_inertia(0.08, 0.15, 3.7)),
        visuals=[Visual(origin=Origin(xyz=[0, 0, 0]), geometry=s_geom)],
        collisions=[Collision(origin=Origin(xyz=[0, 0, 0]), geometry=s_geom)],
    )

    # Joint 2: Shoulder Lift
    joints["shoulder_lift_joint"] = Joint(
        name="shoulder_lift_joint", type=JointType.REVOLUTE, parent="shoulder_link", child="upper_arm_link",
        origin=Origin(xyz=[0, 0.138, 0], rpy=[0, 1.57079, 0]), axis=[0, 1, 0],
        limits=JointLimits(lower=-6.283, upper=6.283, effort=150.0, velocity=3.14),
        dynamics=JointDynamics(damping=1.2, friction=0.1),
    )
    u_geom = Geometry(type=GeometryType.CYLINDER, radius=0.065, length=0.425)
    links["upper_arm_link"] = Link(
        name="upper_arm_link",
        inertial=Inertial(mass=8.39, origin=Origin(xyz=[0, 0, 0.2125]), inertia=calculate_cylinder_inertia(0.065, 0.425, 8.39)),
        visuals=[Visual(origin=Origin(xyz=[0, 0, 0.2125]), geometry=u_geom)],
        collisions=[Collision(origin=Origin(xyz=[0, 0, 0.2125]), geometry=u_geom)],
    )

    # Joint 3: Elbow
    joints["elbow_joint"] = Joint(
        name="elbow_joint", type=JointType.REVOLUTE, parent="upper_arm_link", child="forearm_link",
        origin=Origin(xyz=[0, -0.131, 0.425]), axis=[0, 1, 0],
        limits=JointLimits(lower=-3.1415, upper=3.1415, effort=150.0, velocity=3.14),
        dynamics=JointDynamics(damping=1.0, friction=0.1),
    )
    f_geom = Geometry(type=GeometryType.CYLINDER, radius=0.05, length=0.392)
    links["forearm_link"] = Link(
        name="forearm_link",
        inertial=Inertial(mass=2.27, origin=Origin(xyz=[0, 0, 0.196]), inertia=calculate_cylinder_inertia(0.05, 0.392, 2.27)),
        visuals=[Visual(origin=Origin(xyz=[0, 0, 0.196]), geometry=f_geom)],
        collisions=[Collision(origin=Origin(xyz=[0, 0, 0.196]), geometry=f_geom)],
    )

    # Joint 4: Wrist 1
    joints["wrist_1_joint"] = Joint(
        name="wrist_1_joint", type=JointType.REVOLUTE, parent="forearm_link", child="wrist_1_link",
        origin=Origin(xyz=[0, 0, 0.392], rpy=[0, 1.57079, 0]), axis=[0, 1, 0],
        limits=JointLimits(lower=-6.283, upper=6.283, effort=28.0, velocity=6.28),
        dynamics=JointDynamics(damping=0.5, friction=0.05),
    )
    w1_geom = Geometry(type=GeometryType.CYLINDER, radius=0.045, length=0.09)
    links["wrist_1_link"] = Link(
        name="wrist_1_link",
        inertial=Inertial(mass=1.219, origin=Origin(xyz=[0, 0.127, 0]), inertia=calculate_cylinder_inertia(0.045, 0.09, 1.219)),
        visuals=[Visual(origin=Origin(xyz=[0, 0.127, 0]), geometry=w1_geom)],
        collisions=[Collision(origin=Origin(xyz=[0, 0.127, 0]), geometry=w1_geom)],
    )

    # Joint 5: Wrist 2
    joints["wrist_2_joint"] = Joint(
        name="wrist_2_joint", type=JointType.REVOLUTE, parent="wrist_1_link", child="wrist_2_link",
        origin=Origin(xyz=[0, 0.127, 0]), axis=[0, 0, 1],
        limits=JointLimits(lower=-6.283, upper=6.283, effort=28.0, velocity=6.28),
        dynamics=JointDynamics(damping=0.5, friction=0.05),
    )
    w2_geom = Geometry(type=GeometryType.CYLINDER, radius=0.045, length=0.09)
    links["wrist_2_link"] = Link(
        name="wrist_2_link",
        inertial=Inertial(mass=1.219, origin=Origin(xyz=[0, 0, 0.1]), inertia=calculate_cylinder_inertia(0.045, 0.09, 1.219)),
        visuals=[Visual(origin=Origin(xyz=[0, 0, 0.1]), geometry=w2_geom)],
        collisions=[Collision(origin=Origin(xyz=[0, 0, 0.1]), geometry=w2_geom)],
    )

    # Joint 6: Wrist 3
    joints["wrist_3_joint"] = Joint(
        name="wrist_3_joint", type=JointType.REVOLUTE, parent="wrist_2_link", child="wrist_3_link",
        origin=Origin(xyz=[0, 0, 0.1]), axis=[0, 1, 0],
        limits=JointLimits(lower=-6.283, upper=6.283, effort=28.0, velocity=6.28),
        dynamics=JointDynamics(damping=0.5, friction=0.05),
    )
    w3_geom = Geometry(type=GeometryType.CYLINDER, radius=0.04, length=0.08)
    links["wrist_3_link"] = Link(
        name="wrist_3_link",
        inertial=Inertial(mass=0.1879, origin=Origin(xyz=[0, 0.077, 0]), inertia=calculate_cylinder_inertia(0.04, 0.08, 0.1879)),
        visuals=[Visual(origin=Origin(xyz=[0, 0.077, 0]), geometry=w3_geom)],
        collisions=[Collision(origin=Origin(xyz=[0, 0.077, 0]), geometry=w3_geom)],
    )

    return RobotModel(name="ur5e_robot", root_link="base_link", links=links, joints=joints)
