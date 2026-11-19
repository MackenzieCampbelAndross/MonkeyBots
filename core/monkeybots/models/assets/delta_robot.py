"""
Parallel 3-DOF Delta Robot Model
High-speed pick-and-place parallel manipulator.
"""

from ..robot import (
    RobotModel, Link, Joint, Inertial, Origin, Geometry,
    GeometryType, Visual, Collision, JointType, JointLimits, JointDynamics
)
from ..inertia_calculator import calculate_cylinder_inertia, calculate_box_inertia


def create_delta_robot() -> RobotModel:
    """Builds a 3-DOF parallel delta manipulator."""
    links = {}
    joints = {}

    # Base Plate
    b_geom = Geometry(type=GeometryType.CYLINDER, radius=0.25, length=0.04)
    links["delta_base"] = Link(
        name="delta_base",
        inertial=Inertial(mass=5.0, origin=Origin(xyz=[0, 0, 0]), inertia=calculate_cylinder_inertia(0.25, 0.04, 5.0)),
        visuals=[Visual(origin=Origin(xyz=[0, 0, 0]), geometry=b_geom)],
        collisions=[Collision(origin=Origin(xyz=[0, 0, 0]), geometry=b_geom)],
    )

    # 3 Actuated Arms
    for i in range(1, 4):
        jname = f"motor_arm_joint_{i}"
        lname = f"motor_arm_{i}"
        angle = (i - 1) * 2.094395  # 120 degrees
        import math
        x = 0.20 * math.cos(angle)
        y = 0.20 * math.sin(angle)

        joints[jname] = Joint(
            name=jname, type=JointType.REVOLUTE, parent="delta_base", child=lname,
            origin=Origin(xyz=[x, y, 0], rpy=[0, 0, angle]), axis=[0, 1, 0],
            limits=JointLimits(lower=-0.785, upper=1.57, effort=60.0, velocity=15.0),
            dynamics=JointDynamics(damping=0.8, friction=0.05),
        )
        geom = Geometry(type=GeometryType.BOX, size=[0.30, 0.04, 0.03])
        links[lname] = Link(
            name=lname,
            inertial=Inertial(mass=0.85, origin=Origin(xyz=[0.15, 0, 0]), inertia=calculate_box_inertia([0.30, 0.04, 0.03], 0.85)),
            visuals=[Visual(origin=Origin(xyz=[0.15, 0, 0]), geometry=geom)],
            collisions=[Collision(origin=Origin(xyz=[0.15, 0, 0]), geometry=geom)],
        )

    return RobotModel(name="delta_robot", root_link="delta_base", links=links, joints=joints)
