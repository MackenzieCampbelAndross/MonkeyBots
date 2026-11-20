"""
Unit Tests for Redundant IK and Null-Space Optimization
"""

import numpy as np
from core.monkeybots.kinematics.redundant_ik import RedundantIKSolver


def test_null_space_projector_orthogonality():
    solver = RedundantIKSolver(dof=7)
    J = np.random.randn(6, 7)
    J_dagger, N = solver.compute_null_space_projector(J)

    # Fundamental property: J * N must be zeros (or close to 0 under damping)
    JN = J @ N
    assert np.allclose(JN, 0.0, atol=0.05)


def test_null_space_elbow_swivel_zero_end_effector_drift():
    solver = RedundantIKSolver(dof=7)
    J = np.random.randn(6, 7)
    # Zero task velocity -> pure null-space elbow swivel
    v_task = np.zeros(6)
    grad_null = np.array([0.1, -0.2, 0.3, 0.0, -0.1, 0.2, -0.3])

    q_dot = solver.solve_step(np.zeros(7), J, v_task, secondary_gradient=grad_null)
    # Resulting spatial task motion J * q_dot must be essentially 0
    task_motion = J @ q_dot
    assert np.allclose(task_motion, 0.0, atol=0.05)
