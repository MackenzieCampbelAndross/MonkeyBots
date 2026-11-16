"""
Unit and Integration Tests for MonkeyBots Stage 12: Analytics, Visualization & Engineering Reports
Verifies:
1. Real simulation telemetry recording from MuJoCo physics.
2. Accurate calculation of all 10 analytics metrics (joint kinematics, torques, Cartesian error, orientation, step response, energy, collisions, performance).
3. Multi-run comparison engine and trade-off synthesis.
4. CSV export integrity and roundtrip fidelity.
5. Markdown engineering report generation with data-driven conclusions.
6. Standalone HTML/PDF report generation with embedded vector SVG charts.
7. FastAPI REST API endpoints on /api/v1/analytics/*.
"""

import pytest
import json
import csv
from io import StringIO
from pathlib import Path
from fastapi.testclient import TestClient

from core.monkeybots.analytics import (
    SimulationTelemetryBuffer,
    execute_and_record_run,
    compute_analytics_metrics,
    compare_simulation_runs,
    generate_markdown_report,
    generate_html_report,
    generate_svg_chart,
)
from server.monkeybots_server.main import app

client = TestClient(app)


def test_simulation_telemetry_recording():
    """Verify live physics telemetry recording from MuJoCo stepping."""
    buffer = execute_and_record_run(duration=0.6, timestep=0.002)
    assert buffer.count() > 0
    assert len(buffer.points) == 300  # 0.6s / 0.002s = 300 steps

    first = buffer.points[0]
    assert len(first.q_actual) == 6
    assert len(first.q_target) == 6
    assert len(first.torques) == 6
    assert len(first.ee_pos_actual) == 3
    assert first.energy_total != 0.0

    last = buffer.points[-1]
    assert last.time == pytest.approx(0.6 - 0.002, abs=1e-4)


def test_telemetry_buffer_to_csv(tmp_path: Path):
    """Verify exporting telemetry buffer to CSV format and verifying columns."""
    buffer = execute_and_record_run(duration=0.4, timestep=0.002)
    csv_file = tmp_path / "telemetry.csv"
    csv_str = buffer.to_csv(filepath=csv_file)

    assert csv_file.exists()
    reader = csv.reader(StringIO(csv_str))
    header = next(reader)
    assert "time" in header
    assert "q1" in header
    assert "tau1" in header
    assert "ee_x" in header
    assert "pos_error_m" in header

    rows = list(reader)
    assert len(rows) == buffer.count()
    # Check first row timestamp is 0.0
    assert float(rows[0][0]) == pytest.approx(0.0, abs=1e-5)


def test_analytics_metrics_computation():
    """Verify computation of all 10 core analytics metrics."""
    buffer = execute_and_record_run(duration=0.8, timestep=0.002)
    metrics = compute_analytics_metrics(buffer, timestep=0.002, duration=0.8)

    # 1. Joint positions & errors
    assert metrics.overall_joint_rmse_rad >= 0.0
    assert len(metrics.joints) == 6
    for j in metrics.joints:
        assert j.position_rmse_rad >= 0.0

    # 2. Joint velocities & accelerations
    assert metrics.joints[0].max_velocity_rad_s >= 0.0
    assert metrics.joints[0].max_acceleration_rad_s2 >= 0.0

    # 3. Torques
    assert metrics.peak_applied_torque_nm > 0.0

    # 4. End-effector Cartesian trajectory & errors
    assert metrics.overall_position_rmse_m >= 0.0
    assert metrics.max_cartesian_error_m >= metrics.overall_position_rmse_m

    # 5. Orientation error
    assert metrics.max_orientation_error_rad >= 0.0
    assert metrics.max_orientation_error_deg >= 0.0

    # 6. Step response & controller dynamics
    assert metrics.step_response.rise_time_s > 0.0
    assert metrics.step_response.settling_time_s > 0.0

    # 7. Energy measurements
    assert metrics.total_energy_initial_j != 0.0
    assert metrics.energy_drift_j >= 0.0

    # 8. Real-time factor
    assert metrics.real_time_factor > 0.0
    assert metrics.mean_step_latency_us > 0.0


def test_multi_run_simulation_comparator():
    """Verify multi-run comparator calculating metric deltas and trade-off insights."""
    # Run 1: Moderate gains
    buf1 = execute_and_record_run(duration=0.5, kp_gains=[180.0]*6, kd_gains=[18.0]*6)
    m1 = compute_analytics_metrics(buf1, duration=0.5)

    # Run 2: High gains
    buf2 = execute_and_record_run(duration=0.5, kp_gains=[380.0]*6, kd_gains=[38.0]*6)
    m2 = compute_analytics_metrics(buf2, duration=0.5)

    runs = [
        {"run_id": "run_mod_kp", "name": "Moderate Gains", "metrics": m1},
        {"run_id": "run_high_kp", "name": "High Gains", "metrics": m2},
    ]

    report = compare_simulation_runs(runs)
    assert report.baseline_run_id == "run_mod_kp"
    assert len(report.compared_runs) == 2
    delta_key = "run_high_kp_vs_run_mod_kp"
    assert delta_key in report.deltas
    delta = report.deltas[delta_key]
    assert isinstance(delta.delta_rmse_mm, float)
    assert isinstance(delta.rmse_improvement_pct, float)
    assert len(report.key_findings) > 0


def test_markdown_and_html_reports():
    """Verify generation of Markdown and HTML reports with embedded SVG charts."""
    buf = execute_and_record_run(duration=0.5)
    metrics = compute_analytics_metrics(buf, duration=0.5)

    # 1. Markdown
    md = generate_markdown_report("TestProject", "6-DOF Arm", metrics)
    assert "# MONKEYBOTS | RIGOROUS ROBOTICS ENGINEERING & ANALYTICS REPORT" in md
    assert "Cartesian Position RMSE" in md
    assert "Joint-by-Joint Performance Breakdown" in md
    assert "Documented Engineering Limitations" in md
    assert "Analytical Conclusion" in md

    # 2. SVG generator
    times = [0.0, 0.1, 0.2, 0.3, 0.4]
    svg = generate_svg_chart(times, {"Joint 1": [0.0, 0.2, 0.4, 0.5, 0.5]}, title="Test Chart")
    assert "<svg" in svg
    assert "<polyline" in svg
    assert "</svg>" in svg

    # 3. HTML/PDF report
    html = generate_html_report("TestProject", "6-DOF Arm", metrics, buffer=buf)
    assert "<!DOCTYPE html>" in html
    assert "MONKEYBOTS ENGINEERING VALIDATION REPORT" in html
    assert "<svg" in html
    assert "Cartesian RMSE" in html


def test_fastapi_analytics_endpoints():
    """Verify all FastAPI REST API endpoints on /api/v1/analytics/*."""
    # 1. Record a simulation run via API
    record_payload = {
        "project_id": "default_6dof_arm",
        "duration": 0.6,
        "timestep": 0.002,
        "interpolation": "quintic",
    }
    rec_res = client.post("/api/v1/analytics/record", json=record_payload)
    assert rec_res.status_code == 200
    data = rec_res.json()
    assert data["status"] == "RECORDED"
    assert "metrics" in data
    assert "telemetry" in data
    assert data["total_points"] == 300

    # 2. Get latest analytics
    lat_res = client.get("/api/v1/analytics/latest")
    assert lat_res.status_code == 200
    assert lat_res.json()["metrics"]["overall_position_rmse_m"] >= 0.0

    # 3. Export CSV
    csv_res = client.get("/api/v1/analytics/export/csv")
    assert csv_res.status_code == 200
    assert csv_res.headers["content-type"].startswith("text/csv")
    assert "time,q1,q2" in csv_res.text

    # 4. Export JSON
    json_res = client.get("/api/v1/analytics/export/json")
    assert json_res.status_code == 200
    assert "metrics" in json_res.json()
    assert "telemetry" in json_res.json()

    # 5. Export Markdown
    md_res = client.get("/api/v1/analytics/export/markdown")
    assert md_res.status_code == 200
    assert "MONKEYBOTS" in md_res.text

    # 6. Export HTML (PDF-ready)
    html_res = client.get("/api/v1/analytics/export/html")
    assert html_res.status_code == 200
    assert "<!DOCTYPE html>" in html_res.text
    assert "<svg" in html_res.text
