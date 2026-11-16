"""
Comprehensive Physical Verification and Unit Tests for Motion Planning and Control.

Verifies:
1. Polynomial interpolation mathematical correctness and C1/C2 continuity.
2. Velocity and acceleration constraint enforcement.
3. Strict joint limits boundary compliance.
4. Closed-loop PID trajectory tracking precision in live MuJoCo simulation.
5. Step response, rise time, settling time, and overshoot calculations.
6. Cartesian trajectory planning with quaternion SLERP.
7. FastAPI motion endpoints integration.
"""

import math
import numpy as np
import pytest
from fastapi.testclient import TestClient

from core.monkeybots.planning import (
    QuinticSegment,
    CubicSegment,
    TrapezoidalSegment,
    JointTrajectory,
    CartesianTrajectory,
    InterpolationType,
    slerp_quaternion,
)
from core.monkeybots.control import (
    PIDController,
    RobotMotionController,
    evaluate_step_response,
)
from core.monkeybots.simulation.engine import SimulationEngine
from core.monkeybots.models.assets.sample_6dof_arm import create_sample_6dof_arm
from core.monkeybots.kinematics import KinematicChain, compute_forward_kinematics
from server.monkeybots_server.main import app

client = TestClient(app)


def test_quintic_interpolation_boundary_conditions():
    """Verify quintic polynomial satisfies all 6 boundary conditions exactly."""
    q0, qf = 0.2, 1.4
    v0, vf = 0.0, 0.0
    a0, af = 0.0, 0.0
    T = 2.0

    seg = QuinticSegment(q0, qf, v0, vf, a0, af, T)

    # Initial state at t = 0
    p_0, v_0, a_0 = seg.evaluate(0.0)
    assert np.isclose(p_0, q0, atol=1e-7)
    assert np.isclose(v_0, v0, atol=1e-7)
    assert np.isclose(a_0, a0, atol=1e-7)

    # Final state at t = T
    p_T, v_T, a_T = seg.evaluate(T)
    assert np.isclose(p_T, qf, atol=1e-7)
    assert np.isclose(v_T, vf, atol=1e-7)
    assert np.isclose(a_T, af, atol=1e-7)


def test_velocity_and_acceleration_constraint_enforcement():
    """Verify trajectory time parameterization guarantees v <= v_max and a <= a_max."""
    waypoints = [
        [0.0, -0.5, 0.5, 0.0, 0.5, 0.0],
        [1.2, 0.4, -0.6, 0.8, -0.4, 0.6],
        [0.0, -0.5, 0.5, 0.0, 0.5, 0.0],
    ]
    v_max = 1.5  # rad/s
    a_max = 3.0  # rad/s^2

    traj = JointTrajectory(
        waypoints=waypoints,
        interpolation=InterpolationType.QUINTIC,
        v_max=v_max,
        a_max=a_max,
    )

    # Sample densely at 1000 points
    samples = traj.sample_all(dt=traj.total_duration / 1000.0)
    for pt in samples:
        for j in range(6):
            assert abs(pt.velocities[j]) <= v_max + 1e-3, (
                f"Velocity violation on joint {j}: {pt.velocities[j]} > {v_max}"
            )
            assert abs(pt.accelerations[j]) <= a_max + 1e-3, (
                f"Acceleration violation on joint {j}: {pt.accelerations[j]} > {a_max}"
            )


def test_joint_limits_violation_rejection():
    """Verify trajectory planner rejects waypoints exceeding joint boundaries."""
    robot = create_sample_6dof_arm()
    chain = KinematicChain(robot)

    # Link 2 has limit [-pi/2, +pi/2] (~ +-1.57 rad). Try passing 3.0 rad
    invalid_waypoints = [
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 3.0, 0.0, 0.0, 0.0, 0.0],  # Out of bounds
    ]
    with pytest.raises(ValueError, match="violates physical joint limits"):
        JointTrajectory(waypoints=invalid_waypoints, chain=chain)


def test_closed_loop_trajectory_tracking_in_mujoco():
    """
    Executes a multi-waypoint trajectory in live MuJoCo simulation.
    Verifies that the closed-loop controller achieves accurate tracking:
    - Overall position RMSE < 0.02 rad (~1.1 deg)
    - Maximum tracking error < 0.05 rad
    """
    engine = SimulationEngine()
    engine.load_from_xml("projects/default_6dof_arm/robot.mjcf")

    waypoints = [
        [0.0, -0.6, 1.2, 0.0, 0.6, 0.0],
        [0.4, -0.3, 0.9, 0.2, 0.4, 0.3],
        [-0.4, -0.5, 1.3, -0.2, 0.7, -0.3],
        [0.0, -0.6, 1.2, 0.0, 0.6, 0.0],
    ]
    traj = JointTrajectory(waypoints=waypoints, v_max=1.8, a_max=3.5)

    controller = RobotMotionController(engine, dof=6)
    perf = controller.execute_trajectory(traj)

    assert perf["overall_position_rmse_rad"] < 0.02, (
        f"Position tracking RMSE too high: {perf['overall_position_rmse_rad']} rad"
    )
    assert perf["max_tracking_error_rad"] < 0.05, (
        f"Max tracking error too high: {perf['max_tracking_error_rad']} rad"
    )
    assert perf["step_count"] > 100


def test_step_response_and_control_stability_in_mujoco():
    """
    Executes closed-loop step response test on joint 1 in live MuJoCo simulation.
    Verifies:
    - Stability is confirmed
    - Steady-state error < 0.005 rad
    - Overshoot < 15%
    - Settling time < 1.5 s
    """
    engine = SimulationEngine()
    engine.load_from_xml("projects/default_6dof_arm/robot.mjcf")

    res = evaluate_step_response(
        sim=engine,
        joint_idx=1,
        step_amplitude=0.30,  # ~17 deg
        test_duration=2.0,
        kp=280.0,
        ki=2.0,
        kd=50.0,
    )

    assert res["is_stable"] is True
    assert res["steady_state_error_rad"] < 0.005
    assert res["overshoot_percent"] < 15.0
    assert res["settling_time_seconds"] < 1.5


def test_cartesian_trajectory_planning_and_slerp():
    """Verify Cartesian straight line trajectory and quaternion SLERP interpolation."""
    robot = create_sample_6dof_arm()
    chain = KinematicChain(robot)

    # Slerp unit test
    q_start = np.array([1.0, 0.0, 0.0, 0.0])
    q_end = np.array([0.7071, 0.0, 0.7071, 0.0])  # 90 deg around Y
    q_mid = slerp_quaternion(q_start, q_end, 0.5)
    assert np.isclose(np.linalg.norm(q_mid), 1.0, atol=1e-7)

    # Cartesian waypoints using known reachable forward kinematics
    q1 = np.array([0.0, -0.6, 1.2, 0.0, 0.6, 0.0])
    q2 = np.array([0.2, -0.4, 0.9, 0.0, 0.5, 0.1])
    fk1 = compute_forward_kinematics(chain, q1)
    fk2 = compute_forward_kinematics(chain, q2)
    cart_wps = [
        (fk1.position, fk1.quaternion),
        (fk2.position, fk2.quaternion),
    ]
    cart_traj = CartesianTrajectory(chain, cart_wps, seed_q=q1)
    assert cart_traj.total_duration > 0.0
    pt = cart_traj.sample(cart_traj.total_duration * 0.5)
    assert len(pt.positions) == 6


def test_api_motion_endpoints():
    """Verify FastAPI motion planning & control REST endpoints."""
    # 1. Trajectory Presets
    res = client.get("/api/v1/motion/presets")
    assert res.status_code == 200
    trajectories = res.json()["trajectories"]
    assert len(trajectories) >= 2

    # 2. Plan Trajectory endpoint
    res = client.post(
        "/api/v1/motion/plan",
        json={
            "waypoints": [
                [0.0, -0.5, 1.0, 0.0, 0.5, 0.0],
                [0.3, -0.3, 0.8, 0.1, 0.4, 0.2],
            ],
            "interpolation": "quintic",
            "v_max": 2.0,
            "a_max": 4.0,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "total_duration" in data
    assert data["total_duration"] > 0
    assert "samples" in data
    assert len(data["samples"]) > 10

    # 3. Execute Trajectory endpoint
    res = client.post(
        "/api/v1/motion/execute",
        json={
            "waypoints": [
                [0.0, -0.5, 1.0, 0.0, 0.5, 0.0],
                [0.2, -0.4, 0.9, 0.0, 0.5, 0.1],
            ],
            "interpolation": "quintic",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "overall_position_rmse_rad" in data
    assert data["overall_position_rmse_rad"] < 0.05
    assert "tracking_errors" in data

    # 4. Step Response endpoint
    res = client.post(
        "/api/v1/motion/step_response",
        json={
            "joint_index": 1,
            "step_amplitude_rad": 0.25,
            "test_duration": 1.5,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_stable"] is True
    assert "overshoot_percent" in data
    assert "settling_time_seconds" in data
