"""
Unit Tests for Delta Manipulator and Mobile Base
"""

from core.monkeybots.models.assets.delta_robot import create_delta_robot
from core.monkeybots.models.validator import ModelValidator


def test_delta_robot_kinematics():
    robot = create_delta_robot()
    assert robot.name == "delta_robot"
    assert len(robot.links) == 4
    assert len(robot.joints) == 3
    validator = ModelValidator(robot)
    assert validator.validate_all().is_valid is True
