"""
Unit tests for MonkeyBots IPC and Project Schemas.
"""

import json
from pathlib import Path
from server.monkeybots_server.schemas.telemetry import TelemetryFrame, Pose3D, ContactInfo
from server.monkeybots_server.schemas.commands import (
    SimControlAction,
    JointPositionCommand,
    CartesianTargetCommand,
)
from server.monkeybots_server.schemas.project import ProjectManifest


def test_telemetry_frame_validation():
    """Verify TelemetryFrame serialization and field constraints."""
    frame = TelemetryFrame(
        sim_time=0.125,
        real_time_factor=1.002,
        step_count=62,
        joint_names=["j1", "j2", "j3", "j4", "j5", "j6"],
        qpos=[0.0, 0.5, -0.5, 0.0, 0.0, 0.0],
        qvel=[0.0] * 6,
        qtorque=[0.0] * 6,
        end_effector=Pose3D(position=[0.5, 0.1, 0.6], quaternion=[1.0, 0.0, 0.0, 0.0]),
        contacts=[
            ContactInfo(geom1="finger_l", geom2="box", force=5.4, distance=0.0)
        ],
        status="RUNNING",
    )
    assert frame.type == "telemetry"
    assert frame.sim_time == 0.125
    assert len(frame.qpos) == 6
    assert frame.contacts[0].force == 5.4


def test_commands_validation():
    """Verify Command schemas."""
    cmd = JointPositionCommand(targets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6], gripper=0.04)
    assert cmd.mode == "joint_position"
    assert len(cmd.targets) == 6

    cart_cmd = CartesianTargetCommand(
        target_pose=Pose3D(position=[0.4, 0.0, 0.5], quaternion=[1.0, 0.0, 0.0, 0.0])
    )
    assert cart_cmd.mode == "cartesian_target"

    ctrl = SimControlAction(action="PAUSE")
    assert ctrl.action == "PAUSE"


def test_project_manifest_loading():
    """Verify loading of the default 6-DOF arm project.json."""
    manifest_path = Path("projects/default_6dof_arm/project.json")
    assert manifest_path.exists()
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    manifest = ProjectManifest.model_validate(data)
    assert manifest.version == "1.0.0"
    assert manifest.robot.dof == 6
    assert len(manifest.controllers.gains) == 6
    assert manifest.physics.timestep == 0.002
