"""
Unit Tests for PRM Roadmap Planner
"""

from core.monkeybots.planning.cspace import ConfigurationSpace
from core.monkeybots.planning.collision_checker import MotionCollisionChecker
from core.monkeybots.planning.prm import PRMPlanner


def test_prm_roadmap_construction():
    cspace = ConfigurationSpace([(-3.14, 3.14) for _ in range(6)])
    checker = MotionCollisionChecker()
    prm = PRMPlanner(cspace, checker, num_samples=30, k_neighbors=4)
    prm.build_roadmap()
    assert len(prm.nodes) == 30
    assert len(prm.edges) == 30
