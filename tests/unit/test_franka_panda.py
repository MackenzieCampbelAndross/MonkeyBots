"""
Unit Tests for Franka Emika Panda 7-DOF Robotic Manipulator
"""

import math
from core.monkeybots.models.assets.franka_panda import create_franka_panda
from core.monkeybots.models.assets.franka_gripper import add_franka_hand
from core.monkeybots.models.validator import ModelValidator
from core.monkeybots.models.mjcf_builder import export_mjcf


def test_franka_panda_creation():
    robot = create_franka_panda()
    assert robot.name == "franka_panda"
    assert len(robot.links) == 8
    assert len(robot.joints) == 7


def test_franka_panda_structural_validation():
    robot = create_franka_panda()
    validator = ModelValidator(robot)
    res = validator.validate_all()
    assert res.is_valid is True
    assert res.error_count == 0


def test_franka_hand_attachment_and_mjcf_compilation():
    robot = create_franka_panda()
    robot = add_franka_hand(robot)
    assert "panda_hand" in robot.links
    assert "panda_leftfinger" in robot.links
    assert "panda_rightfinger" in robot.links

    xml_str = export_mjcf(robot)
    assert "panda_link0" in xml_str
    assert "panda_joint7" in xml_str
    assert "panda_hand" in xml_str
