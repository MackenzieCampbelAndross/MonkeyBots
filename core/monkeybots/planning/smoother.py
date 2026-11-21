"""
Path Shortcutting and B-Spline Trajectory Smoothing
"""

import numpy as np
from typing import List
from .cspace import ConfigurationSpace
from .collision_checker import MotionCollisionChecker


def shortcut_path(path: List[np.ndarray], cspace: ConfigurationSpace, checker: MotionCollisionChecker, max_iters: int = 50) -> List[np.ndarray]:
    """Applies greedy randomized shortcutting to eliminate piecewise corners."""
    if len(path) <= 2:
        return path
    smoothed = list(path)
    for _ in range(max_iters):
        if len(smoothed) <= 2:
            break
        i = np.random.randint(0, len(smoothed) - 2)
        j = np.random.randint(i + 2, len(smoothed))
        seg = cspace.interpolate(smoothed[i], smoothed[j])
        if checker.is_path_valid(seg):
            smoothed = smoothed[:i + 1] + smoothed[j:]
    return smoothed
