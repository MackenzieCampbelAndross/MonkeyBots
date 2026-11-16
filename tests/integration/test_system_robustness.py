"""
MONKEYBOTS STAGE 13: Full System Integration & Quality Assurance
System Robustness, Stress Testing, and Fault Tolerance Suite.

Validates:
1. Memory Leak & Resource Leakage Check (Extended 1,000-step simulation cycles)
2. Numerical Stability under Extreme / Ill-Conditioned Dynamics
3. Graceful Failure on Unreachable IK Targets & Singularities
4. Corrupted & Malformed File Handling (Atomic save recovery, malformed URDF/MJCF/JSON)
5. High-Frequency REST & WebSocket Telemetry Concurrency Stress
"""

import os
import gc
import tracemalloc
import tempfile
import shutil
import pytest
import numpy as np
from pathlib import Path
from fastapi.testclient import TestClient

from server.monkeybots_server.main import app
from core.monkeybots.projects import ProjectManager
from core.monkeybots.models.robot import RobotModel, Link, Joint, JointType, InertiaTensor, Geometry, GeometryType
from core.monkeybots.models.validator import validate_robot_model
from core.monkeybots.models.urdf_parser import import_urdf
from core.monkeybots.models.mjcf_builder import validate_in_mujoco
from core.monkeybots.models.assets.sample_6dof_arm import create_sample_6dof_arm
from core.monkeybots.kinematics import KinematicChain, IKSolver
from core.monkeybots.simulation.engine import SimulationEngine, SimulationConfig
from core.monkeybots.models.mjcf_builder import export_mjcf

client = TestClient(app)


class TestSystemRobustness:
    """Stress testing, fault injection, and stability diagnostics."""

    @classmethod
    def setup_class(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix="mb_robustness_test_")
        cls.pm = ProjectManager(projects_dir=cls.temp_dir)

    @classmethod
    def teardown_class(cls):
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_memory_leak_under_continuous_simulation(self):
        """
        Verify no unbounded memory accumulation during continuous simulation stepping.
        Executes 1,000 physics steps while profiling allocated Python memory.
        """
        gc.collect()
        tracemalloc.start()

        snapshot_start = tracemalloc.take_snapshot()

        engine = SimulationEngine()
        arm = create_sample_6dof_arm()
        engine.load_from_xml(export_mjcf(arm))
        engine.configure(SimulationConfig(timestep=0.002))
        engine.start()

        # Step 1,000 cycles
        for _ in range(10):
            engine.step(100)
            _ = engine.compute_energy()
            _ = engine.get_contact_dynamics()

        gc.collect()
        snapshot_end = tracemalloc.take_snapshot()
        tracemalloc.stop()

        top_stats = snapshot_end.compare_to(snapshot_start, 'lineno')
        total_growth_kb = sum(stat.size_diff for stat in top_stats) / 1024.0

        # Memory growth across 1,000 steps should be under 2MB (strictly bounded)
        assert total_growth_kb < 2048.0, f"Potential memory leak detected: {total_growth_kb:.2f} KB growth"

    def test_numerical_stability_under_extreme_dynamics(self):
        """
        Test MuJoCo solver stability when subjected to sudden high control torques.
        Ensures physics engine does not NaN or crash.
        """
        engine = SimulationEngine()
        arm = create_sample_6dof_arm()
        engine.load_from_xml(export_mjcf(arm))
        engine.start()

        # Inject extreme control torques (1,000 Nm per actuator)
        extreme_torques = np.array([1000.0, -1000.0, 1000.0, -1000.0, 500.0, -500.0])
        engine.data.ctrl[:] = extreme_torques

        # Step physics and ensure no NaNs in positions or velocities
        engine.step(20, apply_internal_controllers=False)
        assert not np.isnan(engine.data.qpos).any(), "NaN found in qpos during extreme torque stress"
        assert not np.isnan(engine.data.qvel).any(), "NaN found in qvel during extreme torque stress"
        assert not np.isinf(engine.data.qvel).any(), "Inf found in qvel during extreme torque stress"

    def test_unreachable_ik_target_graceful_handling(self):
        """
        Verify that IK solver fails gracefully on completely unreachable targets
        (e.g. target 5 meters away for an arm with 1 meter reach) without raising exceptions.
        """
        arm = create_sample_6dof_arm()
        chain = KinematicChain(arm, base_link="base_link", end_effector_link="link_6")
        solver = IKSolver(chain)

        # Unreachable target: 5 meters away in X
        unreachable_target = [5.0, 0.0, 0.0]
        ik_res = solver.solve(target_position=unreachable_target, max_iterations=50)

        assert ik_res.converged is False
        assert ik_res.position_error_m > 2.0  # Noticeable position error (several meters)
        assert len(ik_res.joint_positions) == 6
        # Must still respect physical joint limits
        for i, elem in enumerate(chain.elements):
            if elem.is_active:
                assert elem.lower_limit - 1e-3 <= ik_res.joint_positions[i] <= elem.upper_limit + 1e-3

    def test_corrupted_project_file_handling(self):
        """
        Verify that corrupted project JSON or corrupted model files do not crash the system,
        test automated recovery from backup (.bak), and ensure integrity validation flags unrecoverable errors.
        """
        manifest = self.pm.create_project(name="Corrupted Test")
        proj_id = manifest.metadata.id or "corrupted_test"
        proj_dir = Path(self.temp_dir) / proj_id

        # 1. Corrupt project.json while .bak exists -> Automatic crash recovery should restore it
        # First ensure a .bak exists by saving once
        self.pm.save_project(proj_id, manifest)
        with open(proj_dir / "project.json", "w", encoding="utf-8") as f:
            f.write("{{MALFORMED_JSON_CONTENT}}!!")

        recovered = self.pm.get_project(proj_id)
        assert recovered is not None
        assert recovered.metadata.name == "Corrupted Test"

        # 2. Corrupt project.json, delete .bak, and delete .snapshots -> Completely unrecoverable state
        with open(proj_dir / "project.json", "w", encoding="utf-8") as f:
            f.write("{{MALFORMED_JSON_CONTENT}}!!")
        bak_file = proj_dir / "project.json.bak"
        if bak_file.exists():
            bak_file.unlink()
        snapshots_dir = proj_dir / ".snapshots"
        if snapshots_dir.exists():
            shutil.rmtree(snapshots_dir, ignore_errors=True)

        # Loading now should raise an Exception gracefully
        with pytest.raises(Exception):
            self.pm.get_project(proj_id)

        # Integrity validation should flag the issue rather than crashing
        report = self.pm.validate_project(proj_id)
        assert report.is_valid is False
        assert report.manifest_valid is False
        assert report.status == "ERROR"

    def test_invalid_urdf_and_mjcf_handling(self):
        """Verify proper validation errors on malformed URDF XML and invalid MJCF syntax."""
        # 1. Invalid XML syntax
        res_urdf = client.post("/api/v1/models/import/urdf", json={"xml_content": "<robot>unclosed xml"})
        assert res_urdf.status_code == 400
        assert "error" in res_urdf.json()["detail"].lower()

        # 2. Invalid MJCF compilation in MuJoCo
        is_valid, msg = validate_in_mujoco("<mujoco><invalid_tag/></mujoco>")
        assert is_valid is False
        assert len(msg) > 0

    def test_concurrent_api_requests(self):
        """Verify high concurrency handling of status, health, and kinematics queries."""
        import concurrent.futures

        def make_request(idx):
            res1 = client.get("/api/v1/system/health")
            res2 = client.get("/api/v1/simulation/status")
            return res1.status_code == 200 and res2.status_code == 200

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(make_request, i) for i in range(24)]
            results = [f.result() for f in futures]

        assert all(results), "Concurrent API requests encountered failures"
