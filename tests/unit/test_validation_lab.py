"""
Unit and Integration Tests for MonkeyBots Stage 10: Engineering Validation & Benchmarking Laboratory
Verifies:
1. All 10 individual engineering validation capability benchmarks.
2. The ValidationLaboratory suite orchestrator and Markdown report generation.
3. Repeatable simulation experiment persistence, execution, and comparative analysis.
4. FastAPI validation and experiment REST API endpoints.
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from core.monkeybots.validation import (
    ValidationStatus,
    ValidationMetric,
    ValidationTestCase,
    ValidationSuiteReport,
    ValidationLaboratory,
    ExperimentConfig,
    ExperimentResult,
    ExperimentComparison,
    ExperimentManager,
    validate_robot_model_integrity,
    validate_joint_limits,
    validate_kinematics,
    validate_physics_engine,
    validate_trajectory_planning,
    validate_collision_and_contact,
    validate_numerical_stability,
    validate_repeatability_and_determinism,
    validate_controller_performance,
    validate_numerical_error_analysis,
)
from server.monkeybots_server.main import app

client = TestClient(app)


def test_validation_cap_01_model_integrity():
    """VAL_CAP_01: Verify structural tree, positive mass, and inertia positive-definiteness."""
    tc = validate_robot_model_integrity()
    assert tc.id == "VAL_CAP_01"
    assert tc.status == ValidationStatus.VERIFIED
    assert len(tc.metrics) == 3
    for m in tc.metrics:
        assert m.status == ValidationStatus.VERIFIED
        assert m.difference <= m.tolerance


def test_validation_cap_02_joint_limits():
    """VAL_CAP_02: Verify joint position bounds, clamping, and velocity constraints."""
    tc = validate_joint_limits()
    assert tc.id == "VAL_CAP_02"
    assert tc.status == ValidationStatus.VERIFIED
    assert len(tc.metrics) == 3
    for m in tc.metrics:
        assert m.status == ValidationStatus.VERIFIED


def test_validation_cap_03_kinematics():
    """VAL_CAP_03: Verify forward kinematics closure, DLS IK convergence, and Jacobian gradient."""
    tc = validate_kinematics()
    assert tc.id == "VAL_CAP_03"
    assert tc.status == ValidationStatus.VERIFIED
    assert len(tc.metrics) == 3
    # Check that DLS IK converges within sub-millimeter precision (tolerance <= 0.25 mm)
    ik_metric = next(m for m in tc.metrics if "inverse_kinematics" in m.name or "ik" in m.name)
    assert ik_metric.actual_value <= ik_metric.tolerance
    assert ik_metric.unit == "mm"


def test_validation_cap_04_physics_dynamics():
    """VAL_CAP_04: Verify Galileo free-fall, pendulum Hamiltonian conservation, static torque, and friction."""
    tc = validate_physics_engine()
    assert tc.id == "VAL_CAP_04"
    assert tc.status == ValidationStatus.VERIFIED
    assert len(tc.metrics) == 3
    for m in tc.metrics:
        assert m.status == ValidationStatus.VERIFIED


def test_validation_cap_05_trajectory_planning():
    """VAL_CAP_05: Verify boundary conditions, velocity/acceleration constraints, and C2 continuity."""
    tc = validate_trajectory_planning()
    assert tc.id == "VAL_CAP_05"
    assert tc.status == ValidationStatus.VERIFIED
    assert len(tc.metrics) == 3


def test_validation_cap_06_collision_and_contact():
    """VAL_CAP_06: Verify contact detection, normal force, Coulomb friction cone, and non-penetration."""
    tc = validate_collision_and_contact()
    assert tc.id == "VAL_CAP_06"
    assert tc.status in (ValidationStatus.VERIFIED, ValidationStatus.KNOWN_LIMITATION)
    assert len(tc.metrics) >= 2


def test_validation_cap_07_numerical_stability():
    """VAL_CAP_07: Verify velocity impulse recovery, bounded kinetic energy, and zero NaN/Inf divergence."""
    tc = validate_numerical_stability()
    assert tc.id == "VAL_CAP_07"
    assert tc.status == ValidationStatus.VERIFIED
    assert len(tc.metrics) == 2


def test_validation_cap_08_repeatability_and_determinism():
    """VAL_CAP_08: Verify bit-level reproducibility across N=3 runs with variance < 1e-12."""
    tc = validate_repeatability_and_determinism()
    assert tc.id == "VAL_CAP_08"
    assert tc.status == ValidationStatus.VERIFIED
    var_metric = next(m for m in tc.metrics if "variance" in m.name)
    assert var_metric.actual_value <= 1e-12


def test_validation_cap_09_controller_performance():
    """VAL_CAP_09: Verify closed-loop step response (rise time, overshoot, steady-state error)."""
    tc = validate_controller_performance()
    assert tc.id == "VAL_CAP_09"
    assert tc.status == ValidationStatus.VERIFIED
    ess_metric = next(m for m in tc.metrics if "steady_state_error" in m.name)
    assert ess_metric.actual_value <= 0.05


def test_validation_cap_10_numerical_error_analysis():
    """VAL_CAP_10: Verify timestep convergence, Richardson order, and solver constraint residuals."""
    tc = validate_numerical_error_analysis()
    assert tc.id == "VAL_CAP_10"
    assert tc.status == ValidationStatus.VERIFIED
    assert len(tc.metrics) == 2


def test_validation_laboratory_suite_and_report():
    """Verify full validation laboratory execution and markdown generation."""
    lab = ValidationLaboratory()
    report = lab.run_suite()

    assert isinstance(report, ValidationSuiteReport)
    assert report.total_tests == 10
    assert report.verified_count >= 9
    assert report.failed_count == 0
    assert report.compliance_percentage >= 95.0
    assert report.overall_status == ValidationStatus.VERIFIED

    md_report = lab.generate_markdown_report(report)
    assert "# MONKEYBOTS | ENGINEERING VALIDATION & BENCHMARKING REPORT" in md_report
    assert "VAL_CAP_01" in md_report
    assert "VAL_CAP_10" in md_report
    assert "System Environment & Execution Context" in md_report
    assert "Executive Validation Summary" in md_report


def test_experiment_manager_lifecycle(tmp_path: Path):
    """Verify running, saving, loading, and comparing simulation experiments."""
    manager = ExperimentManager(storage_dir=tmp_path)

    config1 = ExperimentConfig(
        id="EXP_TEST_01",
        name="Low Gain Test",
        timestep=0.002,
        duration=1.0,
        kp=[150.0, 150.0, 100.0, 50.0, 30.0, 15.0],
        kd=[15.0, 15.0, 10.0, 5.0, 3.0, 1.5],
        trajectory_type="quintic",
    )

    res1 = manager.run_experiment(config1)
    assert res1.id == "EXP_TEST_01"
    assert res1.metrics.position_rmse_rad > 0.0
    assert len(res1.time_series["timestamps"]) > 0

    # Load back from disk
    loaded = manager.load_experiment("EXP_TEST_01")
    assert loaded is not None
    assert loaded.id == "EXP_TEST_01"
    assert loaded.metrics.position_rmse_rad == res1.metrics.position_rmse_rad

    # Run second experiment with higher gains
    config2 = ExperimentConfig(
        id="EXP_TEST_02",
        name="High Gain Test",
        timestep=0.002,
        duration=1.0,
        kp=[300.0, 350.0, 250.0, 120.0, 70.0, 35.0],
        kd=[30.0, 40.0, 25.0, 10.0, 5.0, 2.5],
        trajectory_type="quintic",
    )
    res2 = manager.run_experiment(config2)

    # Multi-experiment comparison
    comparison = manager.compare_experiments(["EXP_TEST_01", "EXP_TEST_02"])
    assert len(comparison.experiments) == 2
    assert "EXP_TEST_02_vs_EXP_TEST_01" in comparison.comparative_analysis
    diff = comparison.comparative_analysis["EXP_TEST_02_vs_EXP_TEST_01"]
    assert "delta_rmse_mrad" in diff
    assert "rmse_improvement_percent" in diff


def test_api_validation_suite_endpoint():
    """Verify GET /api/v1/validation/suite."""
    response = client.get("/api/v1/validation/suite")
    assert response.status_code == 200
    data = response.json()
    assert data["total_tests"] == 10
    assert data["overall_status"] == "VERIFIED"
    assert data["compliance_percentage"] >= 95.0
    assert len(data["test_cases"]) == 10


def test_api_validation_capabilities_metadata():
    """Verify GET /api/v1/validation/capabilities."""
    response = client.get("/api/v1/validation/capabilities")
    assert response.status_code == 200
    caps = response.json()["capabilities"]
    assert len(caps) == 10
    assert any(c["id"] == "VAL_CAP_01" for c in caps)
    assert any(c["id"] == "VAL_CAP_10" for c in caps)


def test_api_validation_single_capability():
    """Verify GET /api/v1/validation/capability/{id} with both ID and alias."""
    # Test by ID
    res1 = client.get("/api/v1/validation/capability/VAL_CAP_03")
    assert res1.status_code == 200
    assert res1.json()["id"] == "VAL_CAP_03"
    assert res1.json()["status"] == "VERIFIED"

    # Test by alias
    res2 = client.get("/api/v1/validation/capability/kinematics")
    assert res2.status_code == 200
    assert res2.json()["id"] == "VAL_CAP_03"

    # Test unknown capability
    res_bad = client.get("/api/v1/validation/capability/non_existent")
    assert res_bad.status_code == 404


def test_api_validation_markdown_report():
    """Verify GET /api/v1/validation/report/markdown."""
    response = client.get("/api/v1/validation/report/markdown")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert "MONKEYBOTS | ENGINEERING VALIDATION & BENCHMARKING REPORT" in response.text


def test_api_experiment_run_and_compare():
    """Verify POST /api/v1/validation/experiments/run and compare endpoints."""
    config_payload = {
        "id": "API_EXP_TEST_01",
        "name": "API Test Run",
        "description": "Integration test experiment",
        "robot_id": "default_6dof_arm",
        "timestep": 0.002,
        "duration": 0.8,
        "controller_type": "PID",
        "kp": [250.0, 300.0, 200.0, 100.0, 60.0, 30.0],
        "ki": [2.0, 5.0, 3.0, 1.0, 0.5, 0.2],
        "kd": [25.0, 35.0, 20.0, 8.0, 4.0, 2.0],
        "trajectory_type": "quintic",
        "waypoints": [
            [0.0, -0.6, 1.2, 0.0, 0.6, 0.0],
            [0.2, -0.4, 1.0, 0.1, 0.5, 0.1],
            [0.0, -0.6, 1.2, 0.0, 0.6, 0.0],
        ],
        "v_max": 2.0,
        "a_max": 4.0,
    }

    # Run experiment via API
    run_res = client.post("/api/v1/validation/experiments/run", json=config_payload)
    assert run_res.status_code == 200
    result = run_res.json()
    assert result["id"] == "API_EXP_TEST_01"
    assert result["metrics"]["position_rmse_rad"] >= 0.0
    assert "timestamps" in result["time_series"]

    # Retrieve experiment by ID
    get_res = client.get("/api/v1/validation/experiments/API_EXP_TEST_01")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == "API_EXP_TEST_01"

    # List experiments
    list_res = client.get("/api/v1/validation/experiments")
    assert list_res.status_code == 200
    exps = list_res.json()["experiments"]
    assert any(e["id"] == "API_EXP_TEST_01" for e in exps)

    # Compare with itself
    comp_res = client.post(
        "/api/v1/validation/experiments/compare",
        json={"experiment_ids": ["API_EXP_TEST_01"]},
    )
    assert comp_res.status_code == 200
    assert len(comp_res.json()["experiments"]) == 1
