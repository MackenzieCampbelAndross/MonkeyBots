"""
Unit Tests for Universal Robots UR5e & UR10e Models
"""

from core.monkeybots.models.assets.ur5e_robot import create_ur5e_robot
from core.monkeybots.models.validator import ModelValidator


def test_ur5e_creation_and_validation():
    robot = create_ur5e_robot()
    assert robot.name == "ur5e_robot"
    assert len(robot.links) == 7
    assert len(robot.joints) == 6

    validator = ModelValidator(robot)
    res = validator.validate_all()
    assert res.is_valid is True
    assert res.error_count == 0
