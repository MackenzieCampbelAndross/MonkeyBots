"""
Unit Tests for RRT Motion Planner
"""

import numpy as np
from core.monkeybots.planning.cspace import ConfigurationSpace
from core.monkeybots.planning.collision_checker import MotionCollisionChecker
from core.monkeybots.planning.rrt import RRTPlanner


def test_rrt_obstacle_free_planning():
    cspace = ConfigurationSpace([(-3.14, 3.14) for _ in range(6)])
    checker = MotionCollisionChecker()
    planner = RRTPlanner(cspace, checker, step_size=0.2, goal_bias=0.2, max_iterations=500)

    q_start = np.zeros(6)
    q_goal = np.array([0.5, -0.5, 0.5, -0.5, 0.2, -0.2])

    path = planner.plan(q_start, q_goal)
    assert path is not None
    assert len(path) >= 2
    assert np.allclose(path[0], q_start)
    assert np.allclose(path[-1], q_goal)
