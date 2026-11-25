"""
Unit tests for URDF and MJCF model exporters
"""
import pytest
from core.monkeybots.models.registry import get_robot_model
from core.monkeybots.models.exporters import export_to_urdf, export_to_mjcf


def test_urdf_export():
    model = get_robot_model("ur5e")
    urdf_xml = export_to_urdf(model)
    assert "<robot" in urdf_xml
    assert 'name="ur5e"' in urdf_xml
    assert "<joint" in urdf_xml
    assert "<limit" in urdf_xml


def test_mjcf_export():
    model = get_robot_model("franka_panda")
    mjcf_xml = export_to_mjcf(model)
    assert "<mujoco" in mjcf_xml
    assert 'model="franka_panda"' in mjcf_xml
    assert "<worldbody>" in mjcf_xml
    assert "<inertial" in mjcf_xml
