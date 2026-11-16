"""
Integration tests for MonkeyBots FastAPI server endpoints and WebSocket communication.
"""

from fastapi.testclient import TestClient
from server.monkeybots_server.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify backend root status."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "MonkeyBots"
    assert data["status"] == "ONLINE"


def test_health_check_endpoint():
    """Verify health check response and system metrics."""
    response = client.get("/api/v1/system/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["app"] == "MonkeyBots"
    assert "uptime_seconds" in data
    assert "cpu_percent" in data
    assert "memory_percent" in data


def test_list_projects_endpoint():
    """Verify local filesystem project scanning."""
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    default_arm = next((p for p in data if p["id"] == "default_6dof_arm"), None)
    assert default_arm is not None
    assert default_arm["dof"] == 6


def test_simulation_status_and_control():
    """Verify simulation control lifecycle endpoints."""
    # Check status
    res = client.get("/api/v1/simulation/status")
    assert res.status_code == 200
    assert res.json()["status"] in ("RUNNING", "PAUSED")

    # Send Pause
    res = client.post("/api/v1/simulation/control", json={"action": "PAUSE"})
    assert res.status_code == 200
    assert res.json()["state"]["status"] == "PAUSED"

    # Send Start
    res = client.post("/api/v1/simulation/control", json={"action": "START"})
    assert res.status_code == 200
    assert res.json()["state"]["status"] == "RUNNING"


def test_websocket_telemetry_streaming():
    """Verify WebSocket connection and reception of TelemetryFrame."""
    with client.websocket_connect("/ws/simulation") as websocket:
        # Receive first telemetry frame
        data = websocket.receive_json()
        assert data["type"] == "telemetry"
        assert "sim_time" in data
        assert len(data["joint_names"]) == 6
        assert len(data["qpos"]) == 6

        # Send joint jog command over WebSocket
        websocket.send_json({
            "type": "command",
            "mode": "joint_position",
            "targets": [0.2, -0.6, 1.4, 0.1, 0.7, -0.2]
        })

        # Receive next telemetry frame verifying updated state
        frame_2 = websocket.receive_json()
        assert frame_2["type"] == "telemetry"
