"""
Integration test for System Diagnostics API
"""
import pytest
from fastapi.testclient import TestClient
from server.monkeybots_server.main import app

client = TestClient(app)


def test_diagnostics_system_endpoint():
    res = client.get("/api/v1/diagnostics/system")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert data["physics_engine"] == "MuJoCo 3.x C-Engine"
    assert data["registered_robots_count"] >= 7
