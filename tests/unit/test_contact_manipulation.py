"""
Unit and Integration Tests for MonkeyBots Stage 09: Collision Detection, Contact Physics & Object Manipulation
Verifies contact manifolds, friction dynamics, bilateral grasping, unparented lifting, obstacle impact,
and FastAPI simulation manipulation endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from core.monkeybots.models.assets.workcell_model import generate_workcell_mjcf
from core.monkeybots.simulation.engine import SimulationEngine
from core.monkeybots.simulation.collision import (
    CollisionTracker,
    ContactCategory,
)
from core.monkeybots.simulation.manipulation import (
    ManipulationController,
    PickAndPlaceRequest,
)
from core.monkeybots.simulation.manipulation_benchmarks import (
    run_touch_benchmark,
    run_obstacle_collision_benchmark,
    run_bilateral_grasp_benchmark,
    run_friction_lift_benchmark,
    run_release_and_fall_benchmark,
    run_all_manipulation_benchmarks,
)
from server.monkeybots_server.main import app

client = TestClient(app)


def test_collision_tracker_categorization():
    """Verify contact pair role categorization logic."""
    tracker = CollisionTracker()

    assert tracker.categorize_pair("base_link", "link_1", "base_geom", "link_geom") == ContactCategory.SELF_COLLISION
    assert tracker.categorize_pair("left_finger", "manipulable_box", "left_finger_geom", "box_geom") == ContactCategory.ROBOT_OBJECT
    assert tracker.categorize_pair("link_3", "obstacle_pillar", "link_3_geom", "obstacle_geom") == ContactCategory.ROBOT_ENVIRONMENT
    assert tracker.categorize_pair("manipulable_box", "work_table", "box_geom", "table_geom") == ContactCategory.OBJECT_ENVIRONMENT


def test_benchmark_1_robot_touching_object():
    """Experiment 1: Robot touching an object (contact onset, Fn > 0, spatial accuracy)."""
    res = run_touch_benchmark()
    assert res["passed"] is True
    assert res["contact_detected"] is True
    assert res["normal_force_n"] >= 0.0
    assert len(res["contact_position"]) == 3
    assert len(res["contact_normal"]) == 3


def test_benchmark_2_obstacle_collision_and_stability():
    """Experiment 2: Robot colliding with obstacle (impulse logged, peak force, numerical stability)."""
    res = run_obstacle_collision_benchmark()
    assert res["passed"] is True
    assert res["collision_detected"] is True
    assert res["peak_normal_force_n"] > 10.0
    assert res["numerical_stability"] is True
    assert res["impulse_ns"] >= 0.0


def test_benchmark_3_bilateral_contact_grasping():
    """Experiment 3: Bilateral contact grasping (both jaws contact, friction > weight)."""
    res = run_bilateral_grasp_benchmark()
    assert res["passed"] is True
    assert res["bilateral_contact_established"] is True
    assert res["left_finger_fn_n"] > 0.5
    assert res["right_finger_fn_n"] > 0.5
    assert res["total_normal_force_n"] > 10.0
    assert res["friction_exceeds_weight"] is True


def test_benchmark_4_pure_friction_lifting():
    """Experiment 4: Lifting free-floating object strictly via Coulomb friction (zero fake parenting)."""
    res = run_friction_lift_benchmark()
    assert res["passed"] is True
    assert res["fake_parenting_used"] is False
    assert res["vertical_lift_delta_m"] >= 0.10  # Must rise at least 10 cm


def test_benchmark_5_controlled_release_and_freefall():
    """Experiment 5: Gripper release drops Fn to 0, object free-falls under gravity to table."""
    res = run_release_and_fall_benchmark()
    assert res["passed"] is True
    assert res["settled_stably_on_table"] is True
    assert res["drop_distance_m"] > 0.08
    assert res["residual_gripper_force_n"] < 0.01


def test_run_all_manipulation_benchmarks_suite():
    """Verifies that all 5 controlled experiments pass in the aggregator."""
    suite = run_all_manipulation_benchmarks()
    assert suite["all_passed"] is True
    assert suite["passed_count"] == 5
    assert suite["failed_count"] == 0
    assert len(suite["results"]) == 5


def test_api_gripper_and_contacts_endpoints():
    """Tests FastAPI gripper commands, contact extraction, and collision event log."""
    # 1. Gripper Close Command
    resp = client.post("/api/v1/simulation/gripper/command", json={"action": "CLOSE", "force_n": 15.0})
    assert resp.status_code == 200
    data = resp.json()
    assert "gripper" in data
    assert "width" in data["gripper"]

    # 2. Gripper Status
    resp = client.get("/api/v1/simulation/gripper/status")
    assert resp.status_code == 200
    st = resp.json()
    assert "is_grasping" in st
    assert "left_force" in st
    assert "right_force" in st

    # 3. Active Contacts
    resp = client.get("/api/v1/simulation/contacts")
    assert resp.status_code == 200
    contacts_data = resp.json()
    assert "count" in contacts_data
    assert "contacts" in contacts_data

    # 4. Collision Events
    resp = client.get("/api/v1/simulation/collision_events")
    assert resp.status_code == 200
    ev_data = resp.json()
    assert "events" in ev_data

    # 5. Gripper Open Command
    resp = client.post("/api/v1/simulation/gripper/command", json={"action": "OPEN", "force_n": 0.0})
    assert resp.status_code == 200

    # 6. Manipulation Benchmarks Endpoint
    resp = client.get("/api/v1/simulation/manipulation_benchmarks")
    assert resp.status_code == 200
    bench_data = resp.json()
    assert bench_data["all_passed"] is True
    assert bench_data["passed_count"] == 5
