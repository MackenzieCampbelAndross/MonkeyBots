"""
Universal Robots UR10e Heavy Collaborative Manipulator (12.5 kg payload)
"""

from .ur5e_robot import create_ur5e_robot
from ..robot import RobotModel


def create_ur10e_robot() -> RobotModel:
    """Builds the UR10e collaborative robot model with extended 1.3m reach."""
    robot = create_ur5e_robot()
    robot.name = "ur10e_robot"
    # Scale link dimensions and mass for 12.5 kg payload class
    robot.links["upper_arm_link"].inertial.mass = 13.05
    robot.links["forearm_link"].inertial.mass = 3.98
    robot.joints["shoulder_pan_joint"].limits.effort = 330.0
    robot.joints["shoulder_lift_joint"].limits.effort = 330.0
    robot.joints["elbow_joint"].limits.effort = 150.0
    return robot
