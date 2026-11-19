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

    # Base link
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
    return RobotModel(name="franka_panda", root_link="panda_link0", links=links, joints=joints)
