"""
Rapidly-exploring Random Tree (RRT and RRT*) Motion Planning Engine
"""

import time
import numpy as np
from typing import List, Optional, Tuple, Dict, Any
from .cspace import ConfigurationSpace
from .collision_checker import MotionCollisionChecker


class RRTNode:
    def __init__(self, config: np.ndarray, parent: Optional["RRTNode"] = None, cost: float = 0.0):
        self.config = np.array(config)
        self.parent = parent
        self.cost = cost


class RRTPlanner:
    """Single-query Rapidly-exploring Random Tree planner."""

    def __init__(
        self,
        cspace: ConfigurationSpace,
        checker: MotionCollisionChecker,
        step_size: float = 0.15,
        goal_bias: float = 0.10,
        max_iterations: int = 2000,
    ):
        self.cspace = cspace
        self.checker = checker
        self.step_size = step_size
        self.goal_bias = goal_bias
        self.max_iterations = max_iterations

    def plan(self, q_start: np.ndarray, q_goal: np.ndarray) -> Optional[List[np.ndarray]]:
        """Plans a collision-free path from start to goal configuration."""
        if not self.checker.is_state_valid(q_start) or not self.checker.is_state_valid(q_goal):
            return None

        nodes = [RRTNode(q_start, cost=0.0)]

        for _ in range(self.max_iterations):
            # Goal biasing
            if np.random.rand() < self.goal_bias:
                q_rand = np.array(q_goal)
            else:
                q_rand = self.cspace.sample_uniform()

            # Nearest neighbor
            nearest = min(nodes, key=lambda n: self.cspace.distance(n.config, q_rand))

            # Step towards rand
            dist = self.cspace.distance(nearest.config, q_rand)
            if dist <= self.step_size:
                q_new = q_rand
            else:
                q_new = nearest.config + (q_rand - nearest.config) * (self.step_size / dist)

            # Check segment validity
            seg = self.cspace.interpolate(nearest.config, q_new)
            if self.checker.is_path_valid(seg):
                new_node = RRTNode(q_new, parent=nearest, cost=nearest.cost + dist)
                nodes.append(new_node)

                # Check if goal reached
                if self.cspace.distance(q_new, q_goal) <= self.step_size:
                    final_seg = self.cspace.interpolate(q_new, q_goal)
                    if self.checker.is_path_valid(final_seg):
                        goal_node = RRTNode(q_goal, parent=new_node)
                        return self._extract_path(goal_node)

        return None

    def _extract_path(self, node: RRTNode) -> List[np.ndarray]:
        path = []
        curr = node
        while curr:
            path.append(curr.config)
            curr = curr.parent
        return path[::-1]
