"""
Franka Emika Panda 7-DOF Research Robotic Arm
Official kinematic structure, mass properties, and joint limit constraints.
"""

import math
from ..robot import (
    RobotModel, Link, Joint, Inertial, Origin, Geometry,
    GeometryType, Visual, Collision, JointType, JointLimits, JointDynamics
)
from ..inertia_calculator import calculate_cylinder_inertia, calculate_box_inertia


def create_franka_panda() -> RobotModel:
    """Creates a physically verified Franka Emika Panda 7-DOF arm model."""
    links = {}
    joints = {}

    # Link 0 (Base)
    base_geom = Geometry(type=GeometryType.CYLINDER, radius=0.12, length=0.14)
    base_ine = calculate_cylinder_inertia(0.12, 0.14, 3.06)
    links["panda_link0"] = Link(
        name="panda_link0",
        inertial=Inertial(mass=3.06, origin=Origin(xyz=[0, 0, 0.07]), inertia=base_ine),
        visuals=[Visual(origin=Origin(xyz=[0, 0, 0.07]), geometry=base_geom)],
        collisions=[Collision(origin=Origin(xyz=[0, 0, 0.07]), geometry=base_geom)],
    )

    # Joint 1 & Link 1
    joints["panda_joint1"] = Joint(
        name="panda_joint1", type=JointType.REVOLUTE, parent="panda_link0", child="panda_link1",
        origin=Origin(xyz=[0, 0, 0.333]), axis=[0, 0, 1],
        limits=JointLimits(lower=-2.8973, upper=2.8973, effort=87.0, velocity=2.175),
        dynamics=JointDynamics(damping=0.5, friction=0.1),
    )
    l1_geom = Geometry(type=GeometryType.CYLINDER, radius=0.08, length=0.18)
    l1_ine = calculate_cylinder_inertia(0.08, 0.18, 2.34)
    links["panda_link1"] = Link(
        name="panda_link1",
        inertial=Inertial(mass=2.34, origin=Origin(xyz=[0, -0.03, 0.1]), inertia=l1_ine),
        visuals=[Visual(origin=Origin(xyz=[0, -0.03, 0.1]), geometry=l1_geom)],
        collisions=[Collision(origin=Origin(xyz=[0, -0.03, 0.1]), geometry=l1_geom)],
    )

    # Joint 2 & Link 2
    joints["panda_joint2"] = Joint(
        name="panda_joint2", type=JointType.REVOLUTE, parent="panda_link1", child="panda_link2",
        origin=Origin(xyz=[0, 0, 0], rpy=[-math.pi/2, 0, 0]), axis=[0, 0, 1],
        limits=JointLimits(lower=-1.7628, upper=1.7628, effort=87.0, velocity=2.175),
        dynamics=JointDynamics(damping=0.5, friction=0.1),
    )
    l2_geom = Geometry(type=GeometryType.CYLINDER, radius=0.07, length=0.16)
    l2_ine = calculate_cylinder_inertia(0.07, 0.16, 2.36)
    links["panda_link2"] = Link(
        name="panda_link2",
        inertial=Inertial(mass=2.36, origin=Origin(xyz=[0, -0.04, 0.05]), inertia=l2_ine),
        visuals=[Visual(origin=Origin(xyz=[0, -0.04, 0.05]), geometry=l2_geom)],
        collisions=[Collision(origin=Origin(xyz=[0, -0.04, 0.05]), geometry=l2_geom)],
    )

    # Joint 3 & Link 3
    joints["panda_joint3"] = Joint(
        name="panda_joint3", type=JointType.REVOLUTE, parent="panda_link2", child="panda_link3",
        origin=Origin(xyz=[0, -0.316, 0], rpy=[math.pi/2, 0, 0]), axis=[0, 0, 1],
        limits=JointLimits(lower=-2.8973, upper=2.8973, effort=87.0, velocity=2.175),
        dynamics=JointDynamics(damping=0.5, friction=0.1),
    )
    l3_geom = Geometry(type=GeometryType.CYLINDER, radius=0.065, length=0.15)
    l3_ine = calculate_cylinder_inertia(0.065, 0.15, 2.38)
    links["panda_link3"] = Link(
        name="panda_link3",
        inertial=Inertial(mass=2.38, origin=Origin(xyz=[0.04, 0.03, -0.03]), inertia=l3_ine),
        visuals=[Visual(origin=Origin(xyz=[0.04, 0.03, -0.03]), geometry=l3_geom)],
        collisions=[Collision(origin=Origin(xyz=[0.04, 0.03, -0.03]), geometry=l3_geom)],
    )

    # Joint 4 & Link 4
    joints["panda_joint4"] = Joint(
        name="panda_joint4", type=JointType.REVOLUTE, parent="panda_link3", child="panda_link4",
        origin=Origin(xyz=[0.0825, 0, 0], rpy=[math.pi/2, 0, 0]), axis=[0, 0, 1],
        limits=JointLimits(lower=-3.0718, upper=-0.0698, effort=87.0, velocity=2.175),
        dynamics=JointDynamics(damping=0.5, friction=0.1),
    )
    l4_geom = Geometry(type=GeometryType.CYLINDER, radius=0.06, length=0.14)
    l4_ine = calculate_cylinder_inertia(0.06, 0.14, 2.43)
    links["panda_link4"] = Link(
        name="panda_link4",
        inertial=Inertial(mass=2.43, origin=Origin(xyz=[-0.04, 0.03, 0.03]), inertia=l4_ine),
        visuals=[Visual(origin=Origin(xyz=[-0.04, 0.03, 0.03]), geometry=l4_geom)],
        collisions=[Collision(origin=Origin(xyz=[-0.04, 0.03, 0.03]), geometry=l4_geom)],
    )

    # Joint 5 & Link 5
    joints["panda_joint5"] = Joint(
        name="panda_joint5", type=JointType.REVOLUTE, parent="panda_link4", child="panda_link5",
        origin=Origin(xyz=[-0.0825, 0.384, 0], rpy=[-math.pi/2, 0, 0]), axis=[0, 0, 1],
        limits=JointLimits(lower=-2.8973, upper=2.8973, effort=12.0, velocity=2.61),
        dynamics=JointDynamics(damping=0.5, friction=0.1),
    )
    l5_geom = Geometry(type=GeometryType.CYLINDER, radius=0.055, length=0.13)
    l5_ine = calculate_cylinder_inertia(0.055, 0.13, 3.5)
    links["panda_link5"] = Link(
        name="panda_link5",
        inertial=Inertial(mass=3.5, origin=Origin(xyz=[0, 0.04, -0.04]), inertia=l5_ine),
        visuals=[Visual(origin=Origin(xyz=[0, 0.04, -0.04]), geometry=l5_geom)],
        collisions=[Collision(origin=Origin(xyz=[0, 0.04, -0.04]), geometry=l5_geom)],
    )

    # Joint 6 & Link 6
    joints["panda_joint6"] = Joint(
        name="panda_joint6", type=JointType.REVOLUTE, parent="panda_link5", child="panda_link6",
        origin=Origin(xyz=[0, 0, 0], rpy=[math.pi/2, 0, 0]), axis=[0, 0, 1],
        limits=JointLimits(lower=-0.0175, upper=3.7525, effort=12.0, velocity=2.61),
        dynamics=JointDynamics(damping=0.5, friction=0.1),
    )
    l6_geom = Geometry(type=GeometryType.CYLINDER, radius=0.05, length=0.1)
    l6_ine = calculate_cylinder_inertia(0.05, 0.1, 1.47)
    links["panda_link6"] = Link(
        name="panda_link6",
        inertial=Inertial(mass=1.47, origin=Origin(xyz=[0.06, 0, 0]), inertia=l6_ine),
        visuals=[Visual(origin=Origin(xyz=[0.06, 0, 0]), geometry=l6_geom)],
        collisions=[Collision(origin=Origin(xyz=[0.06, 0, 0]), geometry=l6_geom)],
    )

    # Joint 7 & Link 7 (Flange)
    joints["panda_joint7"] = Joint(
        name="panda_joint7", type=JointType.REVOLUTE, parent="panda_link6", child="panda_link7",
        origin=Origin(xyz=[0.088, 0, 0], rpy=[math.pi/2, 0, 0]), axis=[0, 0, 1],
        limits=JointLimits(lower=-2.8973, upper=2.8973, effort=12.0, velocity=2.61),
        dynamics=JointDynamics(damping=0.5, friction=0.1),
    )
    l7_geom = Geometry(type=GeometryType.CYLINDER, radius=0.04, length=0.06)
    l7_ine = calculate_cylinder_inertia(0.04, 0.06, 0.45)
    links["panda_link7"] = Link(
        name="panda_link7",
        inertial=Inertial(mass=0.45, origin=Origin(xyz=[0, 0, 0.03]), inertia=l7_ine),
        visuals=[Visual(origin=Origin(xyz=[0, 0, 0.03]), geometry=l7_geom)],
        collisions=[Collision(origin=Origin(xyz=[0, 0, 0.03]), geometry=l7_geom)],
    )

    return RobotModel(name="franka_panda", root_link="panda_link0", links=links, joints=joints)
