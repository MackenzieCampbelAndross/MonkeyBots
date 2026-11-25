"""
Unit tests for Cartesian Impedance Controller
"""
import numpy as np
import pytest
from core.monkeybots.control.cartesian_impedance import CartesianImpedanceController, ImpedanceGains


def test_cartesian_impedance_zero_error():
    ctrl = CartesianImpedanceController(dof=6)
    pos = np.array([0.4, 0.0, 0.5, 0.0, 0.0, 0.0])
    vel = np.zeros(6)
    q = np.zeros(6)
    qd = np.zeros(6)
    J = np.eye(6)
    grav = np.array([0.0, 15.0, 8.0, 0.0, 2.0, 0.0])

    tau = ctrl.compute_torque(pos, vel, pos, vel, J, q, q, qd, gravity_torque=grav)
    np.testing.assert_allclose(tau, grav, atol=1e-5)


def test_cartesian_impedance_restoring_force():
    ctrl = CartesianImpedanceController(dof=6, gains=ImpedanceGains(kp_trans=500.0))
    curr_pos = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    target_pos = np.array([0.01, 0.0, 0.0, 0.0, 0.0, 0.0])  # +10mm in X
    vel = np.zeros(6)
    q = np.zeros(6)
    qd = np.zeros(6)
    J = np.eye(6)

    tau = ctrl.compute_torque(curr_pos, vel, target_pos, vel, J, q, q, qd)
    # Restoring force should be in +X (joint 0 torque = 500 * 0.01 = 5.0 Nm)
    assert tau[0] == pytest.approx(5.0, rel=1e-3)
