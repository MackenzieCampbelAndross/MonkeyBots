"""
Robotiq 2F-85 Adaptive Gripper Model
Dual-finger parallel grasping with 85mm stroke.
"""

from ..robot import (
    RobotModel, Link, Joint, Inertial, Origin, Geometry,
    GeometryType, Visual, Collision, JointType, JointLimits, JointDynamics
)
from ..inertia_calculator import calculate_box_inertia


def create_robotiq_2f85() -> RobotModel:
    """Builds the Robotiq 2F-85 adaptive parallel gripper."""
    links = {}
    joints = {}

    b_geom = Geometry(type=GeometryType.BOX, size=[0.075, 0.075, 0.10])
    links["robotiq_base"] = Link(
        name="robotiq_base",
        inertial=Inertial(mass=0.9, origin=Origin(xyz=[0, 0, 0.05]), inertia=calculate_box_inertia([0.075, 0.075, 0.10], 0.9)),
        visuals=[Visual(origin=Origin(xyz=[0, 0, 0.05]), geometry=b_geom)],
        collisions=[Collision(origin=Origin(xyz=[0, 0, 0.05]), geometry=b_geom)],
    )

    for side, sign in [("left", 1), ("right", -1)]:
        f_name = f"finger_{side}"
        j_name = f"finger_{side}_joint"
        joints[j_name] = Joint(
            name=j_name, type=JointType.PRISMATIC, parent="robotiq_base", child=f_name,
            origin=Origin(xyz=[0, sign * 0.0425, 0.10]), axis=[0, -sign, 0],
            limits=JointLimits(lower=0.0, upper=0.0425, effort=120.0, velocity=0.15),
            dynamics=JointDynamics(damping=5.0, friction=1.2),
        )
        geom = Geometry(type=GeometryType.BOX, size=[0.02, 0.025, 0.05])
        links[f_name] = Link(
            name=f_name,
            inertial=Inertial(mass=0.08, origin=Origin(xyz=[0, 0, 0.025]), inertia=calculate_box_inertia([0.02, 0.025, 0.05], 0.08)),
            visuals=[Visual(origin=Origin(xyz=[0, 0, 0.025]), geometry=geom)],
            collisions=[Collision(origin=Origin(xyz=[0, 0, 0.025]), geometry=geom)],
        )

    return RobotModel(name="robotiq_2f85", root_link="robotiq_base", links=links, joints=joints)
