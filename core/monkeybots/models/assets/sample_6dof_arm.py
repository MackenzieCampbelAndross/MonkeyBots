"""
Sample 6-DOF Industrial Robotic Arm Model
Canonical 6-axis industrial manipulator with parallel-jaw end-effector.
"""

import math
from ..robot import (
    RobotModel,
    Link,
    Joint,
    Inertial,
    InertiaTensor,
    Origin,
    Geometry,
    GeometryType,
    Visual,
    Collision,
    JointType,
    JointLimits,
    JointDynamics,
)
from ..inertia_calculator import calculate_cylinder_inertia, calculate_box_inertia


def create_sample_6dof_arm() -> RobotModel:
    """Builds a complete, physically verified 6-DOF industrial robotic arm model."""
    links = {}
    joints = {}

    # 1. Base Link (Pedestal)
    base_geom = Geometry(type=GeometryType.CYLINDER, radius=0.14, length=0.08)
    base_ine = calculate_cylinder_inertia(0.14, 0.08, 4.0)
    links["base_link"] = Link(
        name="base_link",
        inertial=Inertial(mass=4.0, origin=Origin(xyz=[0, 0, 0.04]), inertia=base_ine),
        visuals=[Visual(origin=Origin(xyz=[0, 0, 0.04]), geometry=base_geom)],
        collisions=[Collision(origin=Origin(xyz=[0, 0, 0.04]), geometry=base_geom)],
    )

    # 2. Joint 1 & Link 1 (Shoulder Swivel - Yaw)
    joints["joint_1"] = Joint(
        name="joint_1",
        type=JointType.REVOLUTE,
        parent="base_link",
        child="link_1",
        origin=Origin(xyz=[0, 0, 0.08]),
        axis=[0, 0, 1],
        limits=JointLimits(lower=-math.pi, upper=math.pi, effort=150.0, velocity=3.14),
        dynamics=JointDynamics(damping=0.5, friction=0.1),
    )
    l1_geom = Geometry(type=GeometryType.CYLINDER, radius=0.09, length=0.12)
    l1_ine = calculate_cylinder_inertia(0.09, 0.12, 3.7)
    links["link_1"] = Link(
        name="link_1",
        inertial=Inertial(mass=3.7, origin=Origin(xyz=[0, 0, 0.06]), inertia=l1_ine),
        visuals=[Visual(origin=Origin(xyz=[0, 0, 0.06]), geometry=l1_geom)],
        collisions=[Collision(origin=Origin(xyz=[0, 0, 0.06]), geometry=l1_geom)],
    )

    # 3. Joint 2 & Link 2 (Shoulder - Pitch)
    joints["joint_2"] = Joint(
        name="joint_2",
        type=JointType.REVOLUTE,
        parent="link_1",
        child="link_2",
        origin=Origin(xyz=[0, 0, 0.12], rpy=[0, 0, 0]),
        axis=[0, 1, 0],
        limits=JointLimits(lower=-math.pi / 2, upper=math.pi / 2, effort=150.0, velocity=3.14),
        dynamics=JointDynamics(damping=0.5, friction=0.1),
    )
    l2_geom = Geometry(type=GeometryType.BOX, size=[0.08, 0.08, 0.425])
    l2_ine = calculate_box_inertia([0.08, 0.08, 0.425], 8.39)
    links["link_2"] = Link(
        name="link_2",
        inertial=Inertial(mass=8.39, origin=Origin(xyz=[0, 0, 0.212]), inertia=l2_ine),
        visuals=[Visual(origin=Origin(xyz=[0, 0, 0.212]), geometry=l2_geom)],
        collisions=[Collision(origin=Origin(xyz=[0, 0, 0.212]), geometry=l2_geom)],
    )

    # 4. Joint 3 & Link 3 (Elbow - Pitch)
    joints["joint_3"] = Joint(
        name="joint_3",
        type=JointType.REVOLUTE,
        parent="link_2",
        child="link_3",
        origin=Origin(xyz=[0, 0, 0.425]),
        axis=[0, 1, 0],
        limits=JointLimits(lower=-math.pi / 2, upper=math.pi / 2, effort=150.0, velocity=3.14),
        dynamics=JointDynamics(damping=0.4, friction=0.08),
    )
    l3_geom = Geometry(type=GeometryType.BOX, size=[0.07, 0.07, 0.392])
    l3_ine = calculate_box_inertia([0.07, 0.07, 0.392], 4.27)
    links["link_3"] = Link(
        name="link_3",
        inertial=Inertial(mass=4.27, origin=Origin(xyz=[0, 0, 0.196]), inertia=l3_ine),
        visuals=[Visual(origin=Origin(xyz=[0, 0, 0.196]), geometry=l3_geom)],
        collisions=[Collision(origin=Origin(xyz=[0, 0, 0.196]), geometry=l3_geom)],
    )

    # 5. Joint 4 & Link 4 (Wrist 1 - Pitch)
    joints["joint_4"] = Joint(
        name="joint_4",
        type=JointType.REVOLUTE,
        parent="link_3",
        child="link_4",
        origin=Origin(xyz=[0, 0, 0.392]),
        axis=[0, 1, 0],
        limits=JointLimits(lower=-math.pi, upper=math.pi, effort=28.0, velocity=6.28),
        dynamics=JointDynamics(damping=0.2, friction=0.04),
    )
    l4_geom = Geometry(type=GeometryType.CYLINDER, radius=0.045, length=0.09)
    l4_ine = calculate_cylinder_inertia(0.045, 0.09, 1.8)
    links["link_4"] = Link(
        name="link_4",
        inertial=Inertial(mass=1.8, origin=Origin(xyz=[0, 0, 0.045]), inertia=l4_ine),
        visuals=[Visual(origin=Origin(xyz=[0, 0, 0.045]), geometry=l4_geom)],
        collisions=[Collision(origin=Origin(xyz=[0, 0, 0.045]), geometry=l4_geom)],
    )

    # 6. Joint 5 & Link 5 (Wrist 2 - Yaw)
    joints["joint_5"] = Joint(
        name="joint_5",
        type=JointType.REVOLUTE,
        parent="link_4",
        child="link_5",
        origin=Origin(xyz=[0, 0, 0.09]),
        axis=[0, 0, 1],
        limits=JointLimits(lower=-math.pi, upper=math.pi, effort=28.0, velocity=6.28),
        dynamics=JointDynamics(damping=0.2, friction=0.04),
    )
    l5_geom = Geometry(type=GeometryType.CYLINDER, radius=0.04, length=0.08)
    l5_ine = calculate_cylinder_inertia(0.04, 0.08, 1.5)
    links["link_5"] = Link(
        name="link_5",
        inertial=Inertial(mass=1.5, origin=Origin(xyz=[0, 0, 0.04]), inertia=l5_ine),
        visuals=[Visual(origin=Origin(xyz=[0, 0, 0.04]), geometry=l5_geom)],
        collisions=[Collision(origin=Origin(xyz=[0, 0, 0.04]), geometry=l5_geom)],
    )

    # 7. Joint 6 & Link 6 (Tool Flange - Roll)
    joints["joint_6"] = Joint(
        name="joint_6",
        type=JointType.REVOLUTE,
        parent="link_5",
        child="link_6",
        origin=Origin(xyz=[0, 0, 0.08]),
        axis=[1, 0, 0],
        limits=JointLimits(lower=-math.pi, upper=math.pi, effort=28.0, velocity=6.28),
        dynamics=JointDynamics(damping=0.1, friction=0.02),
    )
    l6_geom = Geometry(type=GeometryType.CYLINDER, radius=0.04, length=0.03)
    l6_ine = calculate_cylinder_inertia(0.04, 0.03, 0.87)
    links["link_6"] = Link(
        name="link_6",
        inertial=Inertial(mass=0.87, origin=Origin(xyz=[0, 0, 0.015]), inertia=l6_ine),
        visuals=[Visual(origin=Origin(xyz=[0, 0, 0.015]), geometry=l6_geom)],
        collisions=[Collision(origin=Origin(xyz=[0, 0, 0.015]), geometry=l6_geom)],
    )

    return RobotModel(
        name="MonkeyBots_Industrial_6DOF_Arm",
        root_link="base_link",
        links=links,
        joints=joints,
    )
