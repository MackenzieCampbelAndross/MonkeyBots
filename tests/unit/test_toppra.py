"""
Unit tests for Time-Optimal Path Parameterization
"""
import numpy as np
import pytest
from core.monkeybots.planning.toppra import TimeOptimalPathParameterizer


def test_toppra_basic_parameterization():
    v_max = np.array([2.0, 2.0, 2.0, 3.0, 3.0, 3.0])
    a_max = np.array([4.0, 4.0, 4.0, 6.0, 6.0, 6.0])
    topp = TimeOptimalPathParameterizer(v_max=v_max, a_max=a_max)

    waypoints = np.array([
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.5, -0.3, 0.4, 0.1, 0.2, -0.5],
        [1.0, -0.5, 0.8, 0.0, 0.5, -1.0],
    ])

    traj = topp.parameterize(waypoints, dt=0.02)
    assert len(traj) > 10
    assert traj[0].time_s == 0.0
    np.testing.assert_allclose(traj[0].q, waypoints[0], atol=1e-5)
    np.testing.assert_allclose(traj[-1].q, waypoints[-1], atol=1e-5)

    # Check bounds
    for pt in traj:
        assert np.all(np.abs(pt.qd) <= v_max + 1e-4)
        assert np.all(np.abs(pt.qdd) <= a_max + 1e-4)
