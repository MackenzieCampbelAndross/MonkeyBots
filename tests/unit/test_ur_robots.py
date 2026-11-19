"""
Unit Tests for Universal Robots UR5e & UR10e Models
"""

from core.monkeybots.models.assets.ur5e_robot import create_ur5e_robot
from core.monkeybots.models.assets.ur10e_robot import create_ur10e_robot
from core.monkeybots.models.validator import ModelValidator


def test_ur5e_creation_and_validation():
    robot = create_ur5e_robot()
    assert robot.name == "ur5e_robot"
    assert len(robot.links) == 7
    assert len(robot.joints) == 6
    validator = ModelValidator(robot)
    assert validator.validate_all().is_valid is True


def test_ur10e_creation_and_validation():
    robot = create_ur10e_robot()
    assert robot.name == "ur10e_robot"
    assert robot.links["upper_arm_link"].inertial.mass == 13.05
    assert robot.joints["shoulder_pan_joint"].limits.effort == 330.0
    validator = ModelValidator(robot)
    assert validator.validate_all().is_valid is True
