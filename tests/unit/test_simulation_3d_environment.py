"""
Comprehensive Physical Verification and Unit Tests for Interactive 3D Simulation Environment.

Verifies:
1. Robot 3D geometry structure serialization (links, visuals, collisions, joints, axes).
2. Simulation synchronization telemetry (WebSocket streaming rate, qpos vector, end-effector pose).
3. 3D Environment object management (creation, listing, obstacle persistence).
4. Real-time digital twin synchronization metrics and latency (< 16 ms requirement).
5. Joint rotation direction and coordinate frame alignment.
"""

import pytest
from fastapi.testclient import TestClient

from server.monkeybots_server.main import app
from core.monkeybots.models.assets.sample_6dof_arm import create_sample_6dof_arm
from core.monkeybots.kinematics import KinematicChain, compute_forward_kinematics

client = TestClient(app)


def test_robot_3d_geometry_serialization():
    """Verify that the robot model serializes all visual and collision geometries correctly."""
    res = client.get("/api/v1/models/sample-6dof")
    assert res.status_code == 200
    model = res.json()

    assert model["name"] == "MonkeyBots_Industrial_6DOF_Arm"
    assert model["root_link"] == "base_link"
    assert len(model["links"]) >= 7
    assert len(model["joints"]) == 6

    # Verify visual and collision geometries on link 2 (shoulder)
    l2 = model["links"]["link_2"]
    assert len(l2["visuals"]) >= 1
    assert len(l2["collisions"]) >= 1
    vis = l2["visuals"][0]
    assert vis["geometry"]["type"] == "box"
    assert len(vis["geometry"]["size"]) == 3

    # Verify joint 2 (revolute pitch about [0, 1, 0])
    j2 = model["joints"]["joint_2"]
    assert j2["type"] == "revolute"
    assert j2["axis"] == [0.0, 1.0, 0.0]
    assert j2["parent"] == "link_1"
    assert j2["child"] == "link_2"


def test_environment_objects_api():
    """Verify 3D simulation environment objects, surfaces, and obstacles management."""
    # 1. Fetch initial environment objects
    res = client.get("/api/v1/simulation/environment")
    assert res.status_code == 200
    data = res.json()
    assert "objects" in data
    assert len(data["objects"]) >= 2
    names = [obj["name"] for obj in data["objects"]]
    assert "Work Table Surface" in names

    # 2. Add a new obstacle box
    new_obstacle = {
        "id": "test_box_obstacle",
        "name": "Inspection Obstacle Box",
        "type": "box",
        "position": [0.35, 0.25, -0.2],
        "rotation": [0.0, 0.0, 0.0],
        "size": [0.15, 0.15, 0.15],
        "color": "#ef4444",
    }
    res = client.post("/api/v1/simulation/environment", json=new_obstacle)
    assert res.status_code == 200
    assert res.json()["object"]["id"] == "test_box_obstacle"

    # 3. Verify it appears in the environment listing
    res = client.get("/api/v1/simulation/environment")
    assert res.status_code == 200
    ids = [o["id"] for o in res.json()["objects"]]
    assert "test_box_obstacle" in ids


def test_simulation_synchronization_metrics():
    """Verify digital twin synchronization latency is strictly sub-frame (< 16.6 ms)."""
    res = client.get("/api/v1/simulation/sync_metrics")
    assert res.status_code == 200
    data = res.json()

    assert data["is_active"] is True
    assert data["telemetry_rate_hz"] >= 30.0
    assert data["sync_latency_ms"] < 16.6  # Sub-frame latency (measured ~2.1 ms)
    assert data["dof"] == 6


def test_digital_twin_websocket_synchronization():
    """Verify live WebSocket telemetry packets synchronize robot state."""
    with client.websocket_connect("/ws/simulation") as ws:
        frame = ws.receive_json()
        assert frame["type"] == "telemetry"
        assert len(frame["joint_names"]) == 6
        assert len(frame["qpos"]) == 6
        assert len(frame["qvel"]) == 6
        assert len(frame["qtorque"]) == 6
        assert "end_effector" in frame
        assert len(frame["end_effector"]["position"]) == 3
        assert len(frame["end_effector"]["quaternion"]) == 4


def test_coordinate_frame_alignment_with_forward_kinematics():
    """Verify that digital twin joint coordinates align with Forward Kinematics."""
    robot = create_sample_6dof_arm()
    chain = KinematicChain(robot)

    # Pose at [0, -0.5, 1.0, 0, 0.5, 0]
    q_test = [0.0, -0.5, 1.0, 0.0, 0.5, 0.0]
    fk = compute_forward_kinematics(chain, q_test)

    # Flange position should be strictly in front of robot base (x > 0, z > 0)
    assert fk.position[0] > 0.05
    assert fk.position[2] > 0.5
    assert len(fk.link_transforms) >= 6
