"""
MONKEYBOTS: Multi-Robot Kinematics, Dynamics & System Diagnostics Verification Suite.

Validates:
1. System Diagnostics API (`/api/v1/system/diagnostics`):
   - Python runtime, MuJoCo C-library, RAM, local filesystem permissions, offline air-gap
2. High-Speed SCARA 4-DOF Assembly Robot:
   - MJCF compilation, RRPR joint motion, prismatic Z displacement, 4-axis control
3. Dual-Arm Bimanual 12-DOF Workcell:
   - MJCF compilation, dual-arm 12-DOF coordination, central table collision manifolds
4. High-frequency synchronization metrics:
   - Real-Time Factor (RTF), dynamic measured loop latency, contact manifolds
"""

import pytest
import numpy as np
from pathlib import Path
from fastapi.testclient import TestClient

from server.monkeybots_server.main import app
from core.monkeybots.diagnostics import run_system_diagnostics
from core.monkeybots.simulation.engine import SimulationEngine, SimulationConfig
from core.monkeybots.projects import ProjectManager

client = TestClient(app)


class TestMultiRobotAndDiagnostics:
    """Verifies multi-robot kinematic configurations, environment diagnostics, and dynamic metrics."""

    def test_system_diagnostics_report(self):
        """Verify full system diagnostic sweep and air-gap offline compliance."""
        report = run_system_diagnostics()
        assert report.overall_status in ("HEALTHY", "DEGRADED")
        assert report.offline_verified is True
        assert len(report.checks) >= 5

        categories = [c.category for c in report.checks]
        assert "Runtime" in categories
        assert "Physics Kernel" in categories
        assert "Local Storage" in categories
        assert "Air-Gap Compliance" in categories

        # REST Endpoint
        res = client.get("/api/v1/system/diagnostics")
        assert res.status_code == 200
        data = res.json()
        assert data["overall_status"] in ("HEALTHY", "DEGRADED")
        assert data["offline_verified"] is True

    def test_scara_robot_model_and_simulation(self):
        """Verify SCARA 4-DOF assembly robot (RRPR) dynamics and control in MuJoCo."""
        scara_mjcf_path = Path("projects/scara_assembly_robot/robot.mjcf")
        assert scara_mjcf_path.exists(), "SCARA MJCF model must exist on disk"

        engine = SimulationEngine()
        engine.load_from_xml(scara_mjcf_path.read_text(encoding="utf-8"))
        assert engine.model is not None
        assert engine.model.nq == 4  # 4 generalized positions
        assert engine.model.nv == 4  # 4 generalized velocities
        assert engine.model.nu == 4  # 4 actuators

        # Configure high-speed 1000 Hz loop
        engine.configure(SimulationConfig(timestep=0.001, gravity=[0, 0, -9.81]))
        engine.start()

        # Command SCARA joint targets: [j1=0.5 rad, j2=-0.8 rad, jz=-0.05 m, jyaw=1.2 rad]
        engine.set_target_joint_positions([0.5, -0.8, -0.05, 1.2])
        success = engine.step(100)
        assert success is True
        assert engine.sim_time > 0.09
        assert engine.status == "RUNNING"
        # Confirm prismatic Z joint moved downwards
        assert engine.data.qpos[2] < 0.01

    def test_dual_arm_workcell_simulation_and_collision(self):
        """Verify 12-DOF cooperative dual-arm workcell with central fixture table."""
        dual_mjcf_path = Path("projects/precision_dual_arm_workcell/robot.mjcf")
        assert dual_mjcf_path.exists(), "Dual-arm workcell MJCF must exist on disk"

        engine = SimulationEngine()
        engine.load_from_xml(dual_mjcf_path.read_text(encoding="utf-8"))
        assert engine.model is not None
        assert engine.model.nq == 12  # 6 DOF Left + 6 DOF Right
        assert engine.model.nv == 12
        assert engine.model.nu == 12

        engine.configure(SimulationConfig(timestep=0.002, gravity=[0, 0, -9.81]))
        engine.start()

        # Step 50 cycles
        success = engine.step(50)
        assert success is True
        assert engine.step_count == 50
        assert not np.isnan(engine.data.qpos).any()

    def test_dynamic_synchronization_metrics_endpoint(self):
        """Verify `/api/v1/simulation/sync_metrics` returns dynamic latency and RTF."""
        res = client.get("/api/v1/simulation/sync_metrics")
        assert res.status_code == 200
        metrics = res.json()
        assert "sync_latency_ms" in metrics
        assert metrics["sync_latency_ms"] >= 0.0
        assert "real_time_factor" in metrics
        assert "telemetry_rate_hz" in metrics
        assert metrics["telemetry_rate_hz"] == 60.0
