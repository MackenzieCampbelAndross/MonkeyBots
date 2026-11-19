"""
2-Wheel Differential Drive Mobile Robotics Base
"""

from ..robot import (
    RobotModel, Link, Joint, Inertial, Origin, Geometry,
    GeometryType, Visual, Collision, JointType, JointLimits, JointDynamics
)
from ..inertia_calculator import calculate_cylinder_inertia, calculate_box_inertia


def create_mobile_base() -> RobotModel:
    """Creates a differential drive mobile robot platform."""
    links = {}
    joints = {}

    # Chassis
    chassis_geom = Geometry(type=GeometryType.BOX, size=[0.45, 0.35, 0.15])
    links["chassis"] = Link(
        name="chassis",
        inertial=Inertial(mass=12.0, origin=Origin(xyz=[0, 0, 0.08]), inertia=calculate_box_inertia([0.45, 0.35, 0.15], 12.0)),
        visuals=[Visual(origin=Origin(xyz=[0, 0, 0.08]), geometry=chassis_geom)],
        collisions=[Collision(origin=Origin(xyz=[0, 0, 0.08]), geometry=chassis_geom)],
    )

    # Left & Right Drive Wheels
    for side, sign in [("left", 1), ("right", -1)]:
        w_name = f"{side}_wheel"
        j_name = f"{side}_wheel_joint"
        joints[j_name] = Joint(
            name=j_name, type=JointType.CONTINUOUS, parent="chassis", child=w_name,
            origin=Origin(xyz=[0, sign * 0.20, 0.05]), axis=[0, 1, 0],
            limits=JointLimits(effort=30.0, velocity=20.0),
            dynamics=JointDynamics(damping=0.1, friction=0.9),
        )
        w_geom = Geometry(type=GeometryType.CYLINDER, radius=0.08, length=0.04)
        links[w_name] = Link(
            name=w_name,
            inertial=Inertial(mass=1.2, origin=Origin(xyz=[0, 0, 0]), inertia=calculate_cylinder_inertia(0.08, 0.04, 1.2)),
            visuals=[Visual(origin=Origin(xyz=[0, 0, 0]), geometry=w_geom)],
            collisions=[Collision(origin=Origin(xyz=[0, 0, 0]), geometry=w_geom)],
        )

    return RobotModel(name="diff_mobile_base", root_link="chassis", links=links, joints=joints)
