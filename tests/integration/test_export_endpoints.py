"""
Integration tests for Model Exporters REST API
"""
import pytest
from fastapi.testclient import TestClient
from server.monkeybots_server.main import app

client = TestClient(app)


def test_export_urdf_endpoint():
    res = client.get("/api/v1/models/export/urdf?robot_id=ur5e")
    assert res.status_code == 200
    assert "application/xml" in res.headers["content-type"]
    assert "<robot" in res.text
    assert 'name="ur5e_robot"' in res.text


def test_export_mjcf_endpoint():
    res = client.get("/api/v1/models/export/mjcf?robot_id=franka_panda")
    assert res.status_code == 200
    assert "application/xml" in res.headers["content-type"]
    assert "<mujoco" in res.text
    assert 'model="franka_panda"' in res.text


def test_export_invalid_format():
    res = client.get("/api/v1/models/export/step?robot_id=ur5e")
    assert res.status_code == 400
