"""
MonkeyBots Telemetry Schemas
Defines high-frequency simulation state frames emitted to the frontend.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Pose3D(BaseModel):
    """3D Position and orientation quaternion [w, x, y, z]."""
    position: List[float] = Field(..., min_length=3, max_length=3, description="[x, y, z] in meters")
    quaternion: List[float] = Field(..., min_length=4, max_length=4, description="[w, x, y, z] normalized quaternion")


class ContactInfo(BaseModel):
    """Details of a collision / contact manifold between two geoms."""
    geom1: str
    geom2: str
    force: float = Field(..., description="Normal contact force magnitude in Newtons")
    distance: float = Field(default=0.0, description="Penetration depth or distance")
    position: Optional[List[float]] = Field(default=None, description="Contact point [x, y, z]")


class TelemetryFrame(BaseModel):
    """High-frequency (60-120 Hz) physics telemetry frame streamed over WebSockets."""
    type: str = "telemetry"
    sim_time: float = Field(..., description="Simulation timestamp in seconds")
    real_time_factor: float = Field(default=1.0, description="Ratio of simulation time to wall-clock time")
    step_count: int = Field(default=0, description="Total integration steps executed")
    joint_names: List[str] = Field(default_factory=list, description="Names of active actuated joints")
    qpos: List[float] = Field(default_factory=list, description="Generalized joint positions (rad or m)")
    qvel: List[float] = Field(default_factory=list, description="Generalized joint velocities (rad/s or m/s)")
    qtorque: List[float] = Field(default_factory=list, description="Actual joint actuator torques (Nm)")
    end_effector: Optional[Pose3D] = None
    contacts: List[ContactInfo] = Field(default_factory=list, description="Active contact manifolds")
    status: str = Field(default="RUNNING", description="RUNNING, PAUSED, or ERROR")
