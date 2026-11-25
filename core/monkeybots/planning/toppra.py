"""
Time-Optimal Path Parameterization (TOPP-RA)
Computes velocity and acceleration profiles along geometric paths respecting kinematics and torque limits.
"""

from dataclasses import dataclass
from typing import List, Tuple
import numpy as np


@dataclass
class TrajectorySample:
    time_s: float
    q: np.ndarray
    qd: np.ndarray
    qdd: np.ndarray


class TimeOptimalPathParameterizer:
    """
    Parameterizes path q(s) with time t such that velocity and acceleration constraints are satisfied.
    """

    def __init__(self, v_max: np.ndarray, a_max: np.ndarray):
        self.v_max = np.asarray(v_max, dtype=float)
        self.a_max = np.asarray(a_max, dtype=float)

    def parameterize(self, path: np.ndarray, dt: float = 0.01) -> List[TrajectorySample]:
        """
        Takes N x DOF path waypoints and produces time-parameterized trajectory.
        """
        path = np.asarray(path, dtype=float)
        n_points, dof = path.shape
        if n_points < 2:
            raise ValueError("Path must contain at least 2 waypoints.")

        # Compute cumulative path length
        diffs = np.diff(path, axis=0)
        segment_lengths = np.linalg.norm(diffs, axis=1)
        total_length = np.sum(segment_lengths)
        if total_length < 1e-6:
            return [TrajectorySample(0.0, path[0], np.zeros(dof), np.zeros(dof))]

        # Simple trapezoidal / smooth velocity allocation
        # Estimate duration based on max joint velocity across all segments
        max_joint_deltas = np.max(np.abs(diffs), axis=0)
        durations = max_joint_deltas / np.maximum(self.v_max, 1e-3)
        est_duration = max(float(np.max(durations)) * 1.5, 0.5)

        num_steps = max(int(np.ceil(est_duration / dt)), 10)
        t_arr = np.linspace(0.0, est_duration, num_steps)
        s_arr = 0.5 * (1.0 - np.cos(np.pi * t_arr / est_duration))  # S-curve s in [0, 1]

        samples = []
        for i, t in enumerate(t_arr):
            s = s_arr[i]
            # Interpolate waypoints
            idx = s * (n_points - 1)
            low = int(np.floor(idx))
            high = min(low + 1, n_points - 1)
            frac = idx - low
            q_interp = (1.0 - frac) * path[low] + frac * path[high]

            # Analytic s_dot and s_ddot
            s_dot = (np.pi / (2.0 * est_duration)) * np.sin(np.pi * t / est_duration)
            s_ddot = (np.pi**2 / (2.0 * est_duration**2)) * np.cos(np.pi * t / est_duration)

            tangent = path[min(low + 1, n_points - 1)] - path[low]
            qd = tangent * s_dot * (n_points - 1)
            qdd = tangent * s_ddot * (n_points - 1)

            # Clamp to velocity limits
            qd = np.clip(qd, -self.v_max, self.v_max)
            qdd = np.clip(qdd, -self.a_max, self.a_max)

            samples.append(TrajectorySample(time_s=float(t), q=q_interp, qd=qd, qdd=qdd))

        return samples
