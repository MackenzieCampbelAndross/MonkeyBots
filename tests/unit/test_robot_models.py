"""
Unit and Integration Tests for MonkeyBots Robot Modelling System
Verifies RobotModel, URDF/MJCF import/export, inertia calculations, model validation, and MuJoCo simulation compilation.
"""

import pytest
from core.monkeybots.models.robot import (
    RobotModel,
    Link,
    Joint,
    Inertial,
    InertiaTensor,
    Origin,
    Geometry,
    GeometryType,
    JointType,
    JointLimits,
)
from core.monkeybots.models.inertia_calculator import (
    calculate_box_inertia,
    calculate_cylinder_inertia,
    calculate_sphere_inertia,
)
from core.monkeybots.models.validator import validate_robot_model
from core.monkeybots.models.urdf_parser import export_urdf, import_urdf
from core.monkeybots.models.mjcf_builder import export_mjcf, validate_in_mujoco
from core.monkeybots.models.assets.sample_6dof_arm import create_sample_6dof_arm
from fastapi.testclient import TestClient
from server.monkeybots_server.main import app

client = TestClient(app)


def test_inertia_calculator():
    """Verify analytical moment of inertia tensors satisfy physical triangle inequalities."""
    box_it = calculate_box_inertia([0.1, 0.2, 0.3], mass=2.0)
    assert box_it.ixx > 0 and box_it.iyy > 0 and box_it.izz > 0
    assert box_it.satisfies_triangle_inequalities()

    cyl_it = calculate_cylinder_inertia(radius=0.05, length=0.4, mass=3.0)
    assert cyl_it.ixx > 0 and cyl_it.iyy > 0 and cyl_it.izz > 0
    assert cyl_it.satisfies_triangle_inequalities()

    sphere_it = calculate_sphere_inertia(radius=0.1, mass=5.0)
    assert sphere_it.ixx == sphere_it.iyy == sphere_it.izz
    assert sphere_it.satisfies_triangle_inequalities()


def test_sample_6dof_robot_creation():
    """Verify construction and DOF count of canonical 6-DOF industrial robot arm."""
    arm = create_sample_6dof_arm()
    assert arm.name == "MonkeyBots_Industrial_6DOF_Arm"
    assert arm.root_link == "base_link"
    assert len(arm.links) == 7  # base_link + links 1 to 6
    assert len(arm.joints) == 6  # 6 revolute joints
    assert arm.get_dof() == 6

    # Run model validator
    report = validate_robot_model(arm)
    assert report.is_valid is True
    assert len(report.errors) == 0
    assert report.dof == 6


def test_model_validator_detects_structural_and_physical_defects():
    """Verify validator catches disconnected links, cycles, invalid limits, and non-positive mass."""
    # 1. Invalid joint parent
    bad_model = create_sample_6dof_arm()
    bad_model.joints["joint_1"].parent = "non_existent_link"
    rep = validate_robot_model(bad_model)
    assert rep.is_valid is False
    assert any(e.code == "INVALID_JOINT_PARENT" for e in rep.errors)

    # 2. Invalid joint limits (lower >= upper)
    bad_model2 = create_sample_6dof_arm()
    bad_model2.joints["joint_2"].limits.lower = 2.0
    bad_model2.joints["joint_2"].limits.upper = 1.0
    rep2 = validate_robot_model(bad_model2)
    assert rep2.is_valid is False
    assert any(e.code == "INVALID_JOINT_LIMIT_BOUNDS" for e in rep2.errors)

    # 3. Non-positive mass
    bad_model3 = create_sample_6dof_arm()
    bad_model3.links["link_2"].inertial.mass = -5.0
    rep3 = validate_robot_model(bad_model3)
    assert rep3.is_valid is False
    assert any(e.code == "NON_POSITIVE_MASS" for e in rep3.errors)

    # 4. Disconnected link
    bad_model4 = create_sample_6dof_arm()
    bad_model4.links["isolated_link"] = Link(name="isolated_link")
    rep4 = validate_robot_model(bad_model4)
    assert rep4.is_valid is False
    assert any(e.code == "DISCONNECTED_LINK" for e in rep4.errors)


def test_urdf_export_and_import_roundtrip():
    """Export to URDF XML and parse back into RobotModel."""
    arm = create_sample_6dof_arm()
    urdf_xml = export_urdf(arm)
    assert "<robot name=\"MonkeyBots_Industrial_6DOF_Arm\">" in urdf_xml
    assert "<joint name=\"joint_1\" type=\"revolute\">" in urdf_xml

    # Parse back
    reimported = import_urdf(urdf_xml)
    assert reimported.name == arm.name
    assert len(reimported.links) == len(arm.links)
    assert len(reimported.joints) == len(arm.joints)
    assert reimported.get_dof() == 6


def test_mjcf_export_and_mujoco_compilation():
    """Verify that generated MJCF compiles directly in MuJoCo physics engine."""
    arm = create_sample_6dof_arm()
    mjcf_xml = export_mjcf(arm)
    assert "<mujoco model=\"MonkeyBots_Industrial_6DOF_Arm\">" in mjcf_xml
    assert "<worldbody>" in mjcf_xml
    assert "<joint name=\"joint_1\" type=\"hinge\"" in mjcf_xml

    # Directly verify engine compilation
    is_compiled, msg = validate_in_mujoco(mjcf_xml)
    assert is_compiled is True
    assert "Successfully compiled and stepped in MuJoCo!" in msg


def test_api_models_endpoints():
    """Verify FastAPI model validation, export, and inertia calculation endpoints."""
    # 1. Sample 6DOF
    res = client.get("/api/v1/models/sample-6dof")
    assert res.status_code == 200
    model_data = res.json()
    assert model_data["name"] == "MonkeyBots_Industrial_6DOF_Arm"

    # 2. Validate
    res_val = client.post("/api/v1/models/validate", json=model_data)
    assert res_val.status_code == 200
    assert res_val.json()["is_valid"] is True

    # 3. Export URDF
    res_urdf = client.post("/api/v1/models/export/urdf", json=model_data)
    assert res_urdf.status_code == 200
    assert "<robot" in res_urdf.json()["content"]

    # 4. Export MJCF
    res_mjcf = client.post("/api/v1/models/export/mjcf", json=model_data)
    assert res_mjcf.status_code == 200
    assert res_mjcf.json()["mujoco_verified"] is True

    # 5. Calculate Inertia
    calc_req = {
        "geometry": {"type": "box", "size": [0.1, 0.2, 0.3]},
        "mass": 4.5
    }
    res_calc = client.post("/api/v1/models/calculate-inertia", json=calc_req)
    assert res_calc.status_code == 200
    assert res_calc.json()["ixx"] > 0
