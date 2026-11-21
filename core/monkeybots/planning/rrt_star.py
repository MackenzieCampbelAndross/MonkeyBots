"""
Optimal RRT* Motion Planner with Asymptotic Optimality Guarantee
"""

import numpy as np
from typing import List, Optional
from .cspace import ConfigurationSpace
from .collision_checker import MotionCollisionChecker
from .rrt import RRTNode, RRTPlanner


class RRTStarPlanner(RRTPlanner):
    """RRT* planner with near-neighbor reconnection and tree rewiring."""

    def __init__(self, cspace: ConfigurationSpace, checker: MotionCollisionChecker, search_radius: float = 0.4, **kwargs):
        super().__init__(cspace, checker, **kwargs)
        self.search_radius = search_radius
