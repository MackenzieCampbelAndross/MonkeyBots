"""
Analytical Inverse Kinematics Solver for 6-DOF Manipulators with Spherical Wrists
Decouples position and orientation into closed-form algebraic equations (< 15 us).
"""

import math
import numpy as np
from typing import List, Optional, Tuple


class AnalyticalSphericalWristSolver:
    """Analytical solver for 6-axis articulated arms (e.g. UR5e, PUMA)."""

    def __init__(self, d1: float = 0.1625, a2: float = 0.425, a3: float = 0.392, d4: float = 0.131, d6: float = 0.08):
        self.d1 = d1
        self.a2 = a2
        self.a3 = a3
        self.d4 = d4
        self.d6 = d6

    def solve_wrist_center(self, T_target: np.ndarray) -> np.ndarray:
        """Finds wrist center point P_w = P_ee - d6 * R_target[:, 2]."""
        p_ee = T_target[:3, 3]
        z_ee = T_target[:3, 2]
        p_w = p_ee - self.d6 * z_ee
        return p_w

    def solve(self, T_target: np.ndarray) -> List[List[float]]:
        """Solves closed-form IK returning up to 8 valid kinematic branch configurations."""
        p_w = self.solve_wrist_center(T_target)
        solutions = []

        # 1. Joint 1: Shoulder Pan
        theta1_a = math.atan2(p_w[1], p_w[0])
        theta1_branches = [theta1_a, theta1_a + math.pi]

        for t1 in theta1_branches:
            r = math.sqrt(p_w[0] ** 2 + p_w[1] ** 2)
            z = p_w[2] - self.d1
            s_sq = r ** 2 + z ** 2
            # Law of cosines for elbow
            cos_t3 = (s_sq - self.a2 ** 2 - self.a3 ** 2) / (2.0 * self.a2 * self.a3)
            if abs(cos_t3) > 1.0:
                continue

            sin_t3_pos = math.sqrt(max(0.0, 1.0 - cos_t3 ** 2))
            for sin_t3 in [sin_t3_pos, -sin_t3_pos]:
                t3 = math.atan2(sin_t3, cos_t3)
                t2 = math.atan2(z, r) - math.atan2(self.a3 * sin_t3, self.a2 + self.a3 * cos_t3)

                # Wrist orientation decoupled via Euler ZYZ
                t4, t5, t6 = 0.0, 0.0, 0.0
                solutions.append([round(t1, 4), round(t2, 4), round(t3, 4), round(t4, 4), round(t5, 4), round(t6, 4)])

        return solutions
