"""
Unit Tests for Yoshikawa Manipulability and Ellipsoid Decomposition
"""

import numpy as np
from core.monkeybots.kinematics.manipulability import (
    compute_yoshikawa_index,
    decompose_manipulability_ellipsoid,
)


def test_yoshikawa_index_identity():
    J = np.eye(6)
    w = compute_yoshikawa_index(J)
    assert np.isclose(w, 1.0)


def test_yoshikawa_index_singular():
    J = np.zeros((6, 6))
    w = compute_yoshikawa_index(J)
    assert np.isclose(w, 0.0)


def test_ellipsoid_decomposition():
    J = np.random.randn(6, 6)
    res = decompose_manipulability_ellipsoid(J)
    assert "translational" in res
    assert "rotational" in res
    assert len(res["translational"]["radii"]) == 3
    assert len(res["rotational"]["radii"]) == 3
    assert res["condition_number"] >= 1.0
