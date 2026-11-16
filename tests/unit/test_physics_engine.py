"""
Comprehensive Unit & Integration Tests for MuJoCo Physics Simulation Engine
Verifies physical accuracy, numerical stability, divergence protection, and the 5 analytical benchmarks.
"""

import pytest
from core.monkeybots.simulation.engine import SimulationEngine, SimulationConfig
from core.monkeybots.simulation.benchmarks import (
    run_free_fall_benchmark,
    run_pendulum_energy_conservation_benchmark,
    run_multi_joint_static_equilibrium_benchmark,
    run_elastic_collision_benchmark,
    run_sliding_friction_benchmark,
    run_all_physics_benchmarks,
)
from core.monkeybots.models.assets.sample_6dof_arm import create_sample_6dof_arm
from core.monkeybots.models.mjcf_builder import export_mjcf
from fastapi.testclient import TestClient
from server.monkeybots_server.main import app

client = TestClient(app)


def test_simulation_engine_lifecycle():
    """Verify load, start, pause, step, reset, and telemetry extraction."""
    engine = SimulationEngine()
    arm = create_sample_6dof_arm()
    mjcf_xml = export_mjcf(arm)

    engine.load_from_xml(mjcf_xml)
    assert engine.status == "PAUSED"
    assert engine.model is not None
    assert engine.model.nv == 6

    # Start
    engine.start()
    assert engine.status == "RUNNING"

    # Step
    stepped = engine.step(5)
    assert stepped is True
    assert engine.step_count == 5
    assert engine.sim_time == pytest.approx(0.010, rel=1e-3)

    # Telemetry
    frame = engine.get_telemetry_frame()
    assert frame.type == "telemetry"
    assert len(frame.qpos) == 6
    assert len(frame.qvel) == 6
    assert frame.status == "RUNNING"
    assert frame.end_effector is not None

    # Pause
    engine.pause()
    assert engine.status == "PAUSED"

    # Reset
    engine.reset()
    assert engine.sim_time == 0.0
    assert engine.step_count == 0


def test_numerical_divergence_protection():
    """Verify engine detects extreme states and reports divergence cleanly."""
    engine = SimulationEngine()
    arm = create_sample_6dof_arm()
    engine.load_from_xml(export_mjcf(arm))

    # Inject NaN into generalized coordinates
    engine.data.qpos[0] = float("nan")
    is_stable, reason = engine.check_numerical_stability()
    assert is_stable is False
    assert "NaN detected" in reason


def test_benchmark_1_free_fall():
    """Controlled Test 1: Rigid body free fall under gravity."""
    res = run_free_fall_benchmark(duration=1.0, dt=0.001)
    assert res["passed"] is True
    assert res["z_error_m"] <= res["tolerance"]
    assert res["vz_error_mps"] <= res["tolerance"]


def test_benchmark_2_pendulum_energy_conservation():
    """Controlled Test 2: Undamped rotating joint mechanical energy conservation."""
    res = run_pendulum_energy_conservation_benchmark(duration=1.0, dt=0.001)
    assert res["passed"] is True
    assert res["relative_drift"] <= res["tolerance"]


def test_benchmark_3_arm_gravity_equilibrium():
    """Controlled Test 3: Multi-joint 6-DOF arm static gravity compensation."""
    res = run_multi_joint_static_equilibrium_benchmark(dt=0.002)
    assert res["passed"] is True
    assert res["max_position_drift_rad"] <= res["tolerance"]


def test_benchmark_4_elastic_collision():
    """Controlled Test 4: Collision between two spheres & linear momentum conservation."""
    res = run_elastic_collision_benchmark(duration=0.5, dt=0.0005)
    assert res["passed"] is True
    assert res["relative_error"] <= res["tolerance"]


def test_benchmark_5_sliding_friction():
    """Controlled Test 5: Coulomb sliding friction deceleration and stopping distance."""
    res = run_sliding_friction_benchmark(duration=2.0, dt=0.001)
    assert res["passed"] is True
    assert res["relative_error"] <= res["tolerance"]


def test_run_all_physics_benchmarks_aggregator():
    """Verify all 5 benchmarks pass in the comprehensive aggregator."""
    agg = run_all_physics_benchmarks()
    assert agg["all_passed"] is True
    assert agg["passed_count"] == 5


def test_simulation_api_endpoints():
    """Verify REST API status, control, and benchmark endpoints."""
    # Status
    res_status = client.get("/api/v1/simulation/status")
    assert res_status.status_code == 200
    data = res_status.json()
    assert data["is_active"] is True
    assert data["dof"] == 6

    # Control Pause
    res_pause = client.post("/api/v1/simulation/control", json={"action": "PAUSE"})
    assert res_pause.status_code == 200

    # Benchmarks
    res_bench = client.get("/api/v1/simulation/benchmarks")
    assert res_bench.status_code == 200
    bench_data = res_bench.json()
    assert bench_data["all_passed"] is True
    assert bench_data["passed_count"] == 5
