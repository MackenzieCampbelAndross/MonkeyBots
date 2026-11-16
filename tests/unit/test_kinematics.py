"""
Comprehensive Unit and Verification Tests for MonkeyBots Kinematics Engine.

Verifies:
1. Spatial math (SE3, SO3, Euler RPY, Quaternions, Rodrigues formula).
2. Kinematic chain construction from arbitrary RobotModels.
3. Forward kinematics analytical comparison.
4. Geometric Jacobian verification via central finite differences.
5. Singularity analysis, condition numbers, and Yoshikawa manipulability.
6. Inverse kinematics convergence, precision (<0.1 mm), and joint limits.
7. Unreachable target handling and solver robustness.
8. Robot geometry independence on custom 3-DOF arm.
9. FastAPI kinematics endpoints integration.
"""

import math
import numpy as np
import pytest
from fastapi.testclient import TestClient

from core.monkeybots.models.robot import (
    RobotModel, Link, Joint, JointType, JointLimits, Origin,
)
from core.monkeybots.models.assets.sample_6dof_arm import create_sample_6dof_arm
from core.monkeybots.kinematics import (
    euler_to_rotation_matrix,
    rotation_matrix_to_euler,
    quaternion_from_rotation_matrix,
    quaternion_to_rotation_matrix,
    quaternion_multiply,
    quaternion_conjugate,
    quaternion_error,
    axis_angle_to_rotation_matrix,
    homogeneous_transform,
    transform_inverse,
    KinematicChain,
    compute_forward_kinematics,
    compute_geometric_jacobian,
    IKSolver,
    IKSolverMethod,
)
from server.monkeybots_server.main import app

client = TestClient(app)


def test_spatial_math_transforms():
    """Verify SE(3) and SO(3) mathematical invariants."""
    # 1. Orthonormality: R * R^T = I, det(R) = +1
    r, p, y = 0.35, -0.62, 1.25
    R = euler_to_rotation_matrix(r, p, y)
    assert np.allclose(R @ R.T, np.eye(3), atol=1e-12)
    assert np.isclose(np.linalg.det(R), 1.0, atol=1e-12)

    # 2. Euler RPY round-trip
    r_rec, p_rec, y_rec = rotation_matrix_to_euler(R)
    assert np.isclose(r, r_rec, atol=1e-6)
    assert np.isclose(p, p_rec, atol=1e-6)
    assert np.isclose(y, y_rec, atol=1e-6)

    # 3. Quaternion conversion & Hamilton product
    q = quaternion_from_rotation_matrix(R)
    assert np.isclose(np.linalg.norm(q), 1.0, atol=1e-12)
    R_q = quaternion_to_rotation_matrix(q)
    assert np.allclose(R, R_q, atol=1e-7)

    # Quaternion identity multiplication: q * q^-1 = [1, 0, 0, 0]
    q_inv = quaternion_conjugate(q)
    q_id = quaternion_multiply(q, q_inv)
    assert np.isclose(q_id[0], 1.0, atol=1e-7)
    assert np.allclose(q_id[1:4], 0.0, atol=1e-7)

    # 4. Rodrigues formula: rotation by 2*pi around arbitrary axis is identity
    axis = [1.0, 2.0, 3.0]
    R_full = axis_angle_to_rotation_matrix(axis, 2.0 * math.pi)
    assert np.allclose(R_full, np.eye(3), atol=1e-10)

    # 5. Homogeneous transform inverse: T * T^-1 = I_4
    T = homogeneous_transform(R, [1.5, -2.3, 0.8])
    T_inv = transform_inverse(T)
    assert np.allclose(T @ T_inv, np.eye(4), atol=1e-12)


def test_kinematic_chain_extraction():
    """Verify chain parsing from RobotModel."""
    robot = create_sample_6dof_arm()
    chain = KinematicChain(robot)

    assert chain.base_link == "base_link"
    assert chain.end_effector_link in ("link_6", "tool0", "flange")
    assert chain.dof == 6
    assert len(chain.active_elements) == 6
    assert len(chain.lower_limits) == 6
    assert len(chain.upper_limits) == 6
    for i in range(6):
        assert chain.lower_limits[i] < chain.upper_limits[i]


def test_forward_kinematics_accuracy():
    """Verify forward kinematics matches geometric expectation."""
    robot = create_sample_6dof_arm()
    chain = KinematicChain(robot)

    # Zero configuration
    q_zero = np.zeros(6)
    fk = compute_forward_kinematics(chain, q_zero)

    # The end-effector position must be strictly positive Z and match link offsets
    assert fk.position[2] > 0.5  # Arm points upwards/forwards
    assert len(fk.link_transforms) >= 6
    assert np.isclose(np.linalg.norm(fk.quaternion), 1.0, atol=1e-6)

    # Check 90 deg rotation on joint 1 (yaw about Z)
    q_yaw = np.array([math.pi / 2.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    fk_yaw = compute_forward_kinematics(chain, q_yaw)
    # Rotating 90 deg around Z transforms x-offset into y-offset
    assert np.isclose(fk_yaw.position[2], fk.position[2], atol=1e-5)
    assert np.isclose(math.sqrt(fk_yaw.position[0]**2 + fk_yaw.position[1]**2),
                      math.sqrt(fk.position[0]**2 + fk.position[1]**2), atol=1e-5)


def test_geometric_jacobian_finite_difference():
    """
    Verify geometric Jacobian J_v matches numerical central finite differences:
    d(p_ee)/d(q_i) ~= [p_ee(q + eps*e_i) - p_ee(q - eps*e_i)] / (2*eps)
    """
    robot = create_sample_6dof_arm()
    chain = KinematicChain(robot)

    q_test = np.array([0.4, -0.6, 0.8, -0.3, 0.5, 0.2])
    jac_analysis = compute_geometric_jacobian(chain, q_test)
    J_v_geom = jac_analysis.J[0:3, :]

    eps = 1e-6
    J_v_num = np.zeros((3, 6))
    for i in range(6):
        q_plus = q_test.copy()
        q_minus = q_test.copy()
        q_plus[i] += eps
        q_minus[i] -= eps
        p_plus = compute_forward_kinematics(chain, q_plus).position
        p_minus = compute_forward_kinematics(chain, q_minus).position
        J_v_num[:, i] = (p_plus - p_minus) / (2.0 * eps)

    # Geometric and numerical central differences must match within 1e-5
    diff = np.abs(J_v_geom - J_v_num)
    assert np.max(diff) < 1e-5, f"Jacobian mismatch: max diff = {np.max(diff)}"


def test_singularity_detection():
    """Verify singularity metrics on singular vs non-singular poses."""
    robot = create_sample_6dof_arm()
    chain = KinematicChain(robot)

    # Wrist singularity: joint 5 is 0.0 (axes of joints 4 and 6 collinear)
    q_singular_wrist = np.array([0.0, 0.2, 0.5, 0.0, 0.0, 0.0])
    jac_wrist = compute_geometric_jacobian(chain, q_singular_wrist)
    diag = jac_wrist.diagnose_singularity(q_singular_wrist, chain)
    assert any("Wrist Singularity" in d for d in diag)

    # Healthy non-singular configuration
    q_healthy = np.array([0.3, -0.7, 1.2, 0.4, 0.9, -0.5])
    jac_healthy = compute_geometric_jacobian(chain, q_healthy)
    assert jac_healthy.manipulability > 1e-3
    assert jac_healthy.condition_number < 500.0


def test_inverse_kinematics_precision():
    """
    Verify IK solves to high precision (< 0.1 mm position error, < 0.001 rad orientation error).
    Tests across multiple reachable configurations.
    """
    robot = create_sample_6dof_arm()
    chain = KinematicChain(robot)
    solver = IKSolver(chain)

    test_configurations = [
        np.array([0.2, -0.5, 0.9, 0.1, 0.8, -0.3]),
        np.array([-0.6, 0.3, 1.1, -0.4, 0.6, 0.7]),
        np.array([0.0, -0.8, 1.4, 0.0, 0.5, 0.0]),
        np.array([0.5, 0.0, 0.7, -0.2, 1.0, 0.4]),
    ]

    for q_true in test_configurations:
        fk_target = compute_forward_kinematics(chain, q_true)
        target_pos = fk_target.position
        target_quat = fk_target.quaternion

        # Provide a perturbed seed configuration
        seed = chain.clamp_to_limits(q_true + np.random.uniform(-0.3, 0.3, 6))

        result = solver.solve(
            target_position=target_pos,
            target_orientation=target_quat,
            initial_seed=seed,
            method=IKSolverMethod.DLS,
            pos_tolerance_m=1e-4,   # 0.1 mm
            rot_tolerance_rad=1e-3,  # 0.057 deg
            max_iterations=120,
        )

        assert result.converged is True
        assert result.position_error_m < 1e-4  # < 0.1 mm
        assert result.orientation_error_rad < 1e-3
        assert chain.is_within_limits(result.joint_positions)


def test_ik_unreachable_target():
    """Verify solver handles targets outside workspace gracefully."""
    robot = create_sample_6dof_arm()
    chain = KinematicChain(robot)
    solver = IKSolver(chain)

    # Target far out at 10 meters
    unreachable_pos = [5.0, 5.0, 5.0]
    result = solver.solve(target_position=unreachable_pos)

    assert result.converged is False
    assert result.status == "UNREACHABLE_TARGET"
    assert len(result.warnings) > 0


def test_kinematics_independence_on_custom_robot():
    """
    Prove the kinematics engine is independent of hardcoded robot geometry
    by testing on a custom 3-DOF planar arm.
    """
    # Build custom 3-DOF planar robot: 3 links of length 1.0m rotating about Z
    links = {
        "base": Link(name="base"),
        "link1": Link(name="link1"),
        "link2": Link(name="link2"),
        "link3": Link(name="link3"),
    }
    joints = {
        "j1": Joint(
            name="j1", type=JointType.REVOLUTE, parent="base", child="link1",
            origin=Origin(xyz=[0.0, 0.0, 0.0]), axis=[0.0, 0.0, 1.0],
            limits=JointLimits(lower=-math.pi, upper=math.pi),
        ),
        "j2": Joint(
            name="j2", type=JointType.REVOLUTE, parent="link1", child="link2",
            origin=Origin(xyz=[1.0, 0.0, 0.0]), axis=[0.0, 0.0, 1.0],
            limits=JointLimits(lower=-math.pi, upper=math.pi),
        ),
        "j3": Joint(
            name="j3", type=JointType.REVOLUTE, parent="link2", child="link3",
            origin=Origin(xyz=[1.0, 0.0, 0.0]), axis=[0.0, 0.0, 1.0],
            limits=JointLimits(lower=-math.pi, upper=math.pi),
        ),
    }
    custom_robot = RobotModel(name="planar_3dof", root_link="base", links=links, joints=joints)
    chain = KinematicChain(custom_robot, end_effector_link="link3")

    assert chain.dof == 3

    # At q = [0, 0, 0], end-effector should be at x = 2.0, y = 0.0
    fk_zero = compute_forward_kinematics(chain, np.zeros(3))
    assert np.isclose(fk_zero.position[0], 2.0, atol=1e-5)
    assert np.isclose(fk_zero.position[1], 0.0, atol=1e-5)

    # Solve IK for (x=1.0, y=1.0)
    solver = IKSolver(chain)
    res = solver.solve(target_position=[1.0, 1.0, 0.0], method=IKSolverMethod.DLS)
    assert res.converged is True
    assert res.position_error_m < 1e-4


def test_api_kinematics_endpoints():
    """Verify FastAPI kinematics REST endpoints."""
    # 1. Chain inspection
    res = client.get("/api/v1/kinematics/chain")
    assert res.status_code == 200
    data = res.json()
    assert data["dof"] == 6
    assert len(data["joints"]) == 6

    # 2. Forward Kinematics endpoint
    res = client.post(
        "/api/v1/kinematics/fk",
        json={"robot_id": "default_6dof_arm", "joint_positions": [0.1, -0.3, 0.5, 0.0, 0.8, -0.2]},
    )
    assert res.status_code == 200
    data = res.json()
    assert "position" in data
    assert len(data["position"]) == 3
    assert "quaternion" in data
    assert "jacobian_analysis" in data
    assert "manipulability" in data["jacobian_analysis"]

    # 3. Inverse Kinematics endpoint
    res = client.post(
        "/api/v1/kinematics/ik",
        json={
            "robot_id": "default_6dof_arm",
            "target_position": [0.4, 0.1, 0.6],
            "target_rpy_deg": [0.0, 45.0, 0.0],
            "method": "damped_least_squares",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "converged" in data
    assert "joint_positions_rad" in data
    assert len(data["joint_positions_rad"]) == 6
    assert "position_error_mm" in data

    # 4. Presets endpoint
    res = client.get("/api/v1/kinematics/presets")
    assert res.status_code == 200
    presets = res.json()["presets"]
    assert len(presets) >= 4
