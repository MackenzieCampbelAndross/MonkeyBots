"""
Configuration Space (C-Space) Representation and Sampling
Defines joint-space boundaries, weighted distance metrics, and sampling distributions.
"""

import numpy as np
from typing import List, Tuple, Optional


class ConfigurationSpace:
    """Represents an n-dimensional robotic joint configuration space."""

    def __init__(self, joint_limits: List[Tuple[float, float]], weights: Optional[List[float]] = None):
        self.limits = np.array(joint_limits)
        self.dof = len(joint_limits)
        self.weights = np.array(weights) if weights is not None else np.ones(self.dof)

    def sample_uniform(self) -> np.ndarray:
        """Samples a uniform random configuration within joint bounds."""
        lows = self.limits[:, 0]
        highs = self.limits[:, 1]
        return np.random.uniform(lows, highs)

    def sample_gaussian(self, mean: np.ndarray, std: float = 0.1) -> np.ndarray:
        """Samples a Gaussian perturbation clamped to joint bounds."""
        sample = np.random.normal(mean, std)
        return np.clip(sample, self.limits[:, 0], self.limits[:, 1])

    def distance(self, q1: np.ndarray, q2: np.ndarray) -> float:
        """Computes weighted Euclidean distance between two joint configurations."""
        diff = q1 - q2
        return float(np.sqrt(np.sum(self.weights * (diff ** 2))))

    def interpolate(self, q_from: np.ndarray, q_to: np.ndarray, step_size: float = 0.05) -> List[np.ndarray]:
        """Discretizes a straight line in C-space into discrete waypoint configurations."""
        dist = self.distance(q_from, q_to)
        steps = max(2, int(np.ceil(dist / step_size)))
        return [q_from + (q_to - q_from) * (i / (steps - 1)) for i in range(steps)]
