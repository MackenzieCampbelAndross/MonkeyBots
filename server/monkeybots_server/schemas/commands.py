"""
MonkeyBots Command Schemas
Defines client-to-server commands sent over WebSockets and REST.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from .telemetry import Pose3D


class SimControlAction(BaseModel):
    """Simulation lifecycle control actions."""
    type: Literal["control"] = "control"
    action: Literal["START", "PAUSE", "STEP", "RESET"]
    step_size: Optional[float] = Field(default=None, description="Custom step size in seconds when action=STEP")


class JointPositionCommand(BaseModel):
    """Direct joint position targets (jogging or setpoints)."""
    type: Literal["command"] = "command"
    mode: Literal["joint_position"] = "joint_position"
    targets: List[float] = Field(..., description="Target joint positions in radians")
    gripper: Optional[float] = Field(default=None, description="Gripper opening distance (meters)")


class CartesianTargetCommand(BaseModel):
    """Cartesian 6D target for real-time Inverse Kinematics resolution."""
    type: Literal["command"] = "command"
    mode: Literal["cartesian_target"] = "cartesian_target"
    target_pose: Pose3D
    ik_tolerance: float = Field(default=1e-3, description="IK position error tolerance in meters")
    gripper: Optional[float] = Field(default=None, description="Gripper opening distance (meters)")
