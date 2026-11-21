"""
Probabilistic Roadmap (PRM) Multi-Query Motion Planning
"""

import numpy as np
from typing import List, Optional, Dict
from .cspace import ConfigurationSpace
from .collision_checker import MotionCollisionChecker


class PRMPlanner:
    """Constructs a roadmap graph in C-space for repeated rapid queries."""

    def __init__(self, cspace: ConfigurationSpace, checker: MotionCollisionChecker, num_samples: int = 150, k_neighbors: int = 8):
        self.cspace = cspace
        self.checker = checker
        self.num_samples = num_samples
        self.k_neighbors = k_neighbors
        self.nodes: List[np.ndarray] = []
        self.edges: Dict[int, List[int]] = {}

    def build_roadmap(self):
        """Samples collision-free configurations and connects k-nearest neighbors."""
        while len(self.nodes) < self.num_samples:
            q = self.cspace.sample_uniform()
            if self.checker.is_state_valid(q):
                self.nodes.append(q)

        for i, q1 in enumerate(self.nodes):
            self.edges[i] = []
            distances = [(j, self.cspace.distance(q1, q2)) for j, q2 in enumerate(self.nodes) if i != j]
            distances.sort(key=lambda x: x[1])
            for j, _ in distances[:self.k_neighbors]:
                seg = self.cspace.interpolate(q1, self.nodes[j])
                if self.checker.is_path_valid(seg):
                    self.edges[i].append(j)
