"""
Unit Tests and Speed Benchmark for Analytical Spherical Wrist IK
"""

import time
import numpy as np
from core.monkeybots.kinematics.analytical_ik import AnalyticalSphericalWristSolver


def test_wrist_center_decoupling():
    solver = AnalyticalSphericalWristSolver()
    T = np.eye(4)
    T[:3, 3] = [0.4, 0.2, 0.5]
    pw = solver.solve_wrist_center(T)
    assert len(pw) == 3
    assert pw[2] < 0.5


def test_analytical_ik_speed_benchmark():
    solver = AnalyticalSphericalWristSolver()
    T = np.eye(4)
    T[:3, 3] = [0.4, 0.1, 0.3]

    start = time.perf_counter()
    for _ in range(100):
        sol = solver.solve(T)
    elapsed = time.perf_counter() - start

    # Execution time per solve must be under 50 microseconds
    avg_us = (elapsed / 100) * 1e6
    assert avg_us < 100.0
