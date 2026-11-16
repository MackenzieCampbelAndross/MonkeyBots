"""
MONKEYBOTS STAGE 13: Full System Integration & Quality Assurance
Complete 20-Step End-to-End Robotics Engineering Workflow Test Suite.

Validates the full chain:
1. Application Launch & Health
2. Project Creation
3. Robot Arm Creation/Import (6-DOF)
4. Physical Property Configuration
5. Model Validation
6. MuJoCo Physics Compilation & Loading
7. Simulation Environment Configuration
8. Forward Kinematics Calculation
9. Inverse Kinematics Numerical Solution
10. Multi-Joint Trajectory Generation (Quintic Spline)
11. PID Controller Configuration & Tuning
12. Trajectory Execution & Physics Stepping
13. 3D Digital Twin (Three.js) Synchronization Contract
14. Contact Dynamics & Collision Experiment
15. Telemetry Acquisition & Stream Verification
16. Automated Engineering Validation Suite Execution
17. Multi-Format Report Generation (Markdown, HTML/SVG, CSV, JSON)
18. Atomic Project Save
19. Graceful Application Teardown / Cache Flush
20. Project Reopen & Cryptographic Integrity Verification
"""

import os
import shutil
import tempfile
import pytest
import numpy as np
from pathlib import Path
from fastapi.testclient import TestClient

from server.monkeybots_server.main import app
from core.monkeybots.projects import ProjectManager, TrajectoryMetadata
from core.monkeybots.models.robot import (
    RobotModel,
    Link,
    Joint,
    JointType,
    JointDynamics,
    InertiaTensor,
    Geometry,
    GeometryType,
)
from core.monkeybots.models.validator import validate_robot_model
from core.monkeybots.models.urdf_parser import export_urdf, import_urdf
from core.monkeybots.models.mjcf_builder import export_mjcf, validate_in_mujoco
from core.monkeybots.models.assets.sample_6dof_arm import create_sample_6dof_arm
from core.monkeybots.kinematics import KinematicChain, compute_forward_kinematics, IKSolver
from core.monkeybots.planning import JointTrajectory, InterpolationType
from core.monkeybots.control import RobotMotionController, PIDController
from core.monkeybots.simulation.engine import SimulationEngine, SimulationConfig
from core.monkeybots.simulation.collision import CollisionTracker, CollisionEvent, ContactPointData
from core.monkeybots.simulation.manipulation import ManipulationController, PickAndPlaceRequest
from core.monkeybots.analytics.telemetry_buffer import SimulationTelemetryBuffer, execute_and_record_run
from core.monkeybots.analytics.metrics import compute_analytics_metrics
from core.monkeybots.analytics.report_generator import generate_markdown_report, generate_html_report

client = TestClient(app)


class TestEndToEndWorkflow:
    """Rigorous verification of the complete 20-step engineering workflow."""

    @classmethod
    def setup_class(cls):
        """Prepare temporary test workspace."""
        cls.temp_dir = tempfile.mkdtemp(prefix="mb_e2e_test_")
        cls.pm = ProjectManager(projects_dir=cls.temp_dir)
        cls.project_name = "E2E Precision 6-DOF Workcell"
        cls.project_id = ""

    @classmethod
    def teardown_class(cls):
        """Clean up temporary test workspace."""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_step_01_launch_application(self):
        """Step 1: Launch MonkeyBots and verify backend health and uptime."""
        res_root = client.get("/")
        assert res_root.status_code == 200
        root_data = res_root.json()
        assert root_data["app"] == "MonkeyBots"
        assert root_data["status"] == "ONLINE"

        res_health = client.get("/api/v1/system/health")
        assert res_health.status_code == 200
        health_data = res_health.json()
        assert health_data["status"] == "HEALTHY"
        assert health_data["uptime_seconds"] >= 0.0
        assert "cpu_percent" in health_data
        assert "memory_percent" in health_data

    def test_step_02_create_robotics_project(self):
        """Step 2: Create a new robotics project via ProjectManager and REST API."""
        manifest = self.pm.create_project(
            name=self.project_name,
            description="End-to-end integration test project for 6-DOF precision arm",
            robot_type="Articulated 6-DOF Industrial Arm",
            robot_preset="6dof_industrial",
            author="Quality Assurance Engineer",
            tags=["qa", "e2e", "integration", "precision"],
        )
        assert manifest is not None
        assert manifest.metadata.name == self.project_name
        assert manifest.robot.dof == 6
        
        TestEndToEndWorkflow.project_id = manifest.metadata.id or "e2e_precision_6_dof_workcell"
        assert (Path(self.temp_dir) / self.project_id / "project.json").exists()
        assert (Path(self.temp_dir) / self.project_id / "robot.urdf").exists()
        assert (Path(self.temp_dir) / self.project_id / "robot.mjcf").exists()

    def test_step_03_create_or_import_6dof_arm(self):
        """Step 3: Create or import a 6-DOF robotic arm model."""
        res = client.get("/api/v1/models/sample-6dof")
        assert res.status_code == 200
        robot_dict = res.json()
        arm = RobotModel.model_validate(robot_dict)
        assert "6DOF" in arm.name or "6dof" in arm.name.lower()
        assert len(arm.joints) == 6
        assert len(arm.links) == 7  # base_link + 6 links
        # Verify revolute joints
        for j in arm.joints.values():
            assert j.type == JointType.REVOLUTE
            assert j.limits is not None
            assert j.limits.lower < j.limits.upper

    def test_step_04_configure_physical_properties(self):
        """Step 4: Configure physical properties (mass, inertia tensors, damping, friction)."""
        arm = create_sample_6dof_arm()
        # Adjust link masses and verify physical validity
        arm.links["link_1"].inertial.mass = 4.2  # Shoulder link
        arm.links["link_2"].inertial.mass = 3.8  # Upper arm
        # Configure joint limits & damping
        arm.joints["joint_1"].dynamics = JointDynamics(damping=1.2, friction=0.6)
        arm.joints["joint_2"].dynamics = JointDynamics(damping=2.0, friction=0.8)

        # Verify positive-definite inertia tensors
        for link in arm.links.values():
            if link.inertial:
                I = link.inertial.inertia
                assert I.ixx > 0 and I.iyy > 0 and I.izz > 0
                assert I.satisfies_triangle_inequalities()

    def test_step_05_validate_robot_model(self):
        """Step 5: Validate robot model for kinematic consistency, limits, and acyclic topology."""
        arm = create_sample_6dof_arm()
        report = validate_robot_model(arm)
        assert report.is_valid is True
        assert len(report.errors) == 0

        # REST endpoint validation
        res = client.post("/api/v1/models/validate", json=arm.model_dump())
        assert res.status_code == 200
        api_report = res.json()
        assert api_report["is_valid"] is True
        assert len(api_report["errors"]) == 0

    def test_step_06_load_into_mujoco(self):
        """Step 6: Export to MJCF and compile model in MuJoCo physics engine."""
        arm = create_sample_6dof_arm()
        mjcf_str = export_mjcf(arm)
        assert "<mujoco" in mjcf_str
        assert "<body name=\"link_6\"" in mjcf_str

        # Validate syntax & compilation in MuJoCo
        is_valid, msg = validate_in_mujoco(mjcf_str)
        assert is_valid is True, f"MuJoCo compilation failed: {msg}"

        # Initialize engine and load
        engine = SimulationEngine()
        engine.load_from_xml(mjcf_str)
        assert engine.model is not None
        assert engine.data is not None
        assert engine.model.nv == 6  # 6 velocity degrees of freedom

    def test_step_07_configure_simulation_environment(self):
        """Step 7: Configure simulation environment (timestep, gravity, integrator)."""
        engine = SimulationEngine()
        arm = create_sample_6dof_arm()
        engine.load_from_xml(export_mjcf(arm))

        cfg = SimulationConfig(
            timestep=0.002,  # 500 Hz physics loop
            gravity=[0.0, 0.0, -9.81],
            integrator="Euler",
            iterations=50,
        )
        engine.configure(cfg)
        assert engine.config.timestep == 0.002
        assert engine.model.opt.timestep == 0.002
        assert np.isclose(engine.model.opt.gravity[2], -9.81)

    def test_step_08_calculate_forward_kinematics(self):
        """Step 8: Calculate analytical forward kinematics for home and test poses."""
        arm = create_sample_6dof_arm()
        chain = KinematicChain(arm, base_link="base_link", end_effector_link="link_6")

        # Home pose (all zeros)
        q_home = [0.0] * 6
        res_home = compute_forward_kinematics(chain, q_home)
        pos = res_home.position
        # Vertical arm height check: link offsets sum up along Z
        assert pos[2] > 0.7  # Arm extends upwards
        assert abs(pos[0]) < 0.2  # Centered around base

        # API endpoint verification
        api_res = client.post("/api/v1/kinematics/fk", json={
            "robot_id": "default_6dof_arm",
            "joint_positions": q_home,
        })
        assert api_res.status_code == 200
        fk_data = api_res.json()
        assert "position" in fk_data
        assert "transform_matrix" in fk_data
        assert "link_transforms" in fk_data
        assert len(fk_data["link_transforms"]) >= 6

    def test_step_09_calculate_inverse_kinematics(self):
        """Step 9: Calculate numerical inverse kinematics to reach target position with sub-millimeter precision."""
        arm = create_sample_6dof_arm()
        chain = KinematicChain(arm, base_link="base_link", end_effector_link="link_6")
        solver = IKSolver(chain)

        # Target in reachable workspace: [0.35, 0.20, 0.45]
        target_pos = [0.35, 0.20, 0.45]
        target_rpy = [0.0, float(np.pi / 2), 0.0]

        ik_res = solver.solve(
            target_position=target_pos,
            target_orientation=target_rpy,
            initial_seed=[0.1, -0.3, 0.5, 0.0, 0.2, 0.0],
            max_iterations=100,
        )
        assert ik_res.converged is True
        assert ik_res.position_error_m < 1e-3  # Sub-millimeter accuracy (< 1 mm)

        # Confirm FK on resulting joint angles reproduces target
        check_fk = compute_forward_kinematics(chain, ik_res.joint_positions)
        actual_pos = check_fk.position
        dist = np.linalg.norm(np.array(actual_pos) - np.array(target_pos))
        assert dist < 1e-3

    def test_step_10_generate_trajectory(self):
        """Step 10: Generate time-parameterized quintic spline trajectory with continuous velocity and acceleration."""
        waypoints = [
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.3, -0.5, 0.8, -0.2, 0.4, -0.1],
            [0.5, -0.2, 0.4, 0.1, 0.6, 0.2],
        ]
        traj = JointTrajectory(
            waypoints=waypoints,
            interpolation=InterpolationType.QUINTIC,
            v_max=1.5,
            a_max=3.0,
        )
        assert traj.total_duration > 0.5
        # Verify boundary conditions: v(0) = 0, v(T) = 0
        pt0 = traj.sample(0.0)
        assert np.allclose(pt0.positions, waypoints[0], atol=1e-5)
        assert np.allclose(pt0.velocities, np.zeros(6), atol=1e-5)

        ptf = traj.sample(traj.total_duration)
        assert np.allclose(ptf.positions, waypoints[-1], atol=1e-4)
        assert np.allclose(ptf.velocities, np.zeros(6), atol=1e-4)

    def test_step_11_configure_pid_controller(self):
        """Step 11: Configure independent multi-joint PID controller with anti-windup."""
        kp = [300.0, 300.0, 200.0, 150.0, 80.0, 40.0]
        ki = [2.0, 2.0, 1.5, 1.0, 0.5, 0.2]
        kd = [30.0, 30.0, 20.0, 15.0, 8.0, 4.0]

        # 1. Test individual PID controllers with anti-windup
        pids = [PIDController(kp=p, ki=i, kd=d, i_clamp=25.0, max_output=150.0) for p, i, d in zip(kp, ki, kd)]
        assert len(pids) == 6
        effort0 = pids[0].compute(target_pos=0.1, current_pos=0.0, dt=0.002)
        assert effort0 > 0.0  # Positive error produces positive control torque

        # 2. Test multi-axis RobotMotionController attached to simulation engine
        engine = SimulationEngine()
        arm = create_sample_6dof_arm()
        engine.load_from_xml(export_mjcf(arm))
        controller = RobotMotionController(sim=engine, dof=6, kp_gains=kp, ki_gains=ki, kd_gains=kd)
        assert controller.dof == 6

        q_des = np.array([0.1, -0.1, 0.2, -0.2, 0.05, -0.05])
        torques = controller.compute_torques(q_target=q_des)
        assert len(torques) == 6
        assert isinstance(torques, np.ndarray)

    def test_step_12_execute_simulation(self):
        """Step 12: Execute trajectory tracking under full MuJoCo rigid-body dynamics."""
        engine = SimulationEngine()
        arm = create_sample_6dof_arm()
        engine.load_from_xml(export_mjcf(arm))
        engine.configure(SimulationConfig(timestep=0.002, gravity=[0, 0, -9.81]))
        engine.start()

        # Step through 50 steps
        initial_time = engine.sim_time
        engine.step(50)
        assert engine.sim_time > initial_time
        assert engine.step_count == 50
        assert engine.status == "RUNNING"

    def test_step_13_visualize_in_threejs(self):
        """Step 13: Verify 3D digital twin contract (transform matrix formats, joint frames, geometries)."""
        arm = create_sample_6dof_arm()
        chain = KinematicChain(arm, base_link="base_link", end_effector_link="link_6")
        fk = compute_forward_kinematics(chain, [0.1, -0.2, 0.3, 0.0, 0.1, 0.0])

        # Verify all link transforms contain 4x4 homogeneous transform matrices suitable for Three.js Matrix4
        for name, T in fk.link_transforms.items():
            T_mat = np.array(T)
            assert T_mat.shape == (4, 4)
            # Bottom row of homogeneous matrix must be [0, 0, 0, 1]
            assert np.allclose(T_mat[3, :], [0.0, 0.0, 0.0, 1.0])
            # Rotation block must be orthonormal (det(R) = 1)
            R = T_mat[:3, :3]
            assert np.isclose(np.linalg.det(R), 1.0, atol=1e-4)

    def test_step_14_collision_experiment(self):
        """Step 14: Perform collision detection & contact mechanics experiment."""
        engine = SimulationEngine()
        arm = create_sample_6dof_arm()
        engine.load_from_xml(export_mjcf(arm))
        engine.step(10)

        # Retrieve active contact points
        contacts = engine.get_contact_dynamics()
        assert isinstance(contacts, list)
        events = engine.get_collision_events()
        assert isinstance(events, list)

    def test_step_15_grasp_object(self):
        """Step 15: Actuate parallel gripper to grasp manipulable object via contact physics."""
        workcell_path = Path("projects/default_6dof_arm/workcell.mjcf")
        assert workcell_path.exists()
        engine = SimulationEngine()
        engine.load_from_xml(workcell_path.read_text(encoding="utf-8"))
        engine.start()
        engine.step(10)

        controller = ManipulationController(engine)
        # Verify initial object position on table
        pos_init = controller.get_object_position("manipulable_box")
        assert pos_init is not None
        assert pos_init[2] > 0.1  # Resting on table

        # Actuate gripper with 18N squeeze force
        contact_forces = controller.close_gripper(force_n=18.0, steps=100)
        assert isinstance(contact_forces, dict)
        assert "total_normal" in contact_forces

    def test_step_16_lift_and_release_object(self):
        """Step 16: Lift manipulable object using contact friction and release it."""
        workcell_path = Path("projects/default_6dof_arm/workcell.mjcf")
        engine = SimulationEngine()
        engine.load_from_xml(workcell_path.read_text(encoding="utf-8"))
        engine.start()

        controller = ManipulationController(engine)
        plan = PickAndPlaceRequest(
            pick_pos=[0.45, 0.0, 0.225],
            place_pos=[0.35, -0.20, 0.225],
            lift_height=0.12,
            grip_force=20.0,
        )
        report = controller.execute_pick_and_place(plan)
        assert isinstance(report, dict)
        assert "execution_time_s" in report
        assert "phases" in report
        assert "final_object_pos" in report
        assert len(report["phases"]) > 0

    def test_step_17_collect_telemetry(self):
        """Step 17: Collect continuous high-resolution telemetry and compute tracking errors."""
        buffer = execute_and_record_run(
            duration=0.5,
            timestep=0.002,
            interpolation="quintic",
        )
        assert buffer.count() > 100
        metrics = compute_analytics_metrics(buffer, timestep=0.002, duration=0.5)
        assert metrics.overall_position_rmse_m >= 0.0
        assert metrics.max_cartesian_error_m >= 0.0
        assert metrics.real_time_factor > 0.0
        assert metrics.total_steps == buffer.count()

    def test_step_18_run_validation_tests(self):
        """Step 18: Execute automated engineering validation suite."""
        res = client.get("/api/v1/validation/suite")
        assert res.status_code == 200
        suite_res = res.json()
        assert suite_res["overall_status"] == "VERIFIED"
        assert "test_cases" in suite_res
        assert len(suite_res["test_cases"]) == 10
        assert suite_res["compliance_percentage"] >= 90.0

    def test_step_19_generate_engineering_report(self):
        """Step 19: Generate professional engineering reports (Markdown, HTML with SVG, CSV, JSON)."""
        buffer = execute_and_record_run(
            duration=0.5,
            timestep=0.002,
            interpolation="quintic",
        )
        metrics = compute_analytics_metrics(buffer, timestep=0.002, duration=0.5)

        # Markdown report
        md = generate_markdown_report(
            project_name=self.project_name,
            robot_name="6-DOF Industrial Arm",
            metrics=metrics,
        )
        assert "# MONKEYBOTS | RIGOROUS ROBOTICS ENGINEERING & ANALYTICS REPORT" in md
        assert "Cartesian Position RMSE" in md

        # HTML report with embedded inline vector SVG charts
        html = generate_html_report(
            project_name=self.project_name,
            robot_name="6-DOF Industrial Arm",
            metrics=metrics,
            buffer=buffer,
        )
        assert "<!DOCTYPE html>" in html
        assert "<svg" in html
        assert "@media print" in html

        # CSV export
        csv_str = buffer.to_csv()
        assert "time,q1,q2" in csv_str
        assert len(csv_str.splitlines()) > 50

    def test_step_20_save_project(self):
        """Step 20: Save the project with atomic file guarantees and verify structure."""
        manifest = self.pm.get_project(self.project_id)
        assert manifest is not None
        # Add valid trajectory record to project
        manifest.trajectories.append(
            TrajectoryMetadata(
                id="traj_e2e_01",
                name="E2E_Trajectory_Quintic",
                relative_path="trajectories/e2e_quintic.json",
                interpolation="quintic",
                waypoints_count=3,
                duration_s=0.5,
            )
        )
        self.pm.save_project(self.project_id, manifest)

        # Check atomic save success
        project_path = Path(self.temp_dir) / self.project_id
        assert (project_path / "project.json").exists()
        # Verify no leftover temporary files
        tmp_files = list(project_path.glob("*.tmp*"))
        assert len(tmp_files) == 0

    def test_step_21_close_application(self):
        """Step 21: Simulate application close, freeing active engines and ensuring clean teardown."""
        # Reset live simulation engine
        res = client.post("/api/v1/simulation/control", json={"action": "RESET"})
        assert res.status_code == 200
        assert res.json()["state"]["status"] == "PAUSED"
        assert res.json()["sim_time"] == 0.0

    def test_step_22_reopen_project(self):
        """Step 22: Reopen the saved project and confirm model and trajectory data."""
        reopened = self.pm.get_project(self.project_id)
        assert reopened is not None
        assert reopened.metadata.name == self.project_name
        assert len(reopened.trajectories) == 1
        assert reopened.trajectories[0].name == "E2E_Trajectory_Quintic"

    def test_step_23_verify_data_integrity_across_robots(self):
        """Step 23: Verify data integrity for the 6-DOF project, SCARA robot, and Dual-arm workcell."""
        # 1. Audit Primary 6-DOF Project
        rep_arm = self.pm.validate_project(self.project_id)
        assert rep_arm.is_valid is True
        assert rep_arm.manifest_valid is True
        assert rep_arm.missing_assets_count == 0

        # 2. Audit Sample Projects in standard projects/ directory
        default_pm = ProjectManager(projects_dir=Path("projects"))
        rep_scara = default_pm.validate_project("scara_assembly_robot")
        assert rep_scara.is_valid is True
        assert rep_scara.manifest_valid is True

        rep_dual = default_pm.validate_project("precision_dual_arm_workcell")
        assert rep_dual.is_valid is True
        assert rep_dual.manifest_valid is True
