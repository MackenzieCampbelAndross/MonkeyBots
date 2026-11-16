"""
MonkeyBots Project Manifest Schemas
Defines the local project.json file structure.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class JointControllerGain(BaseModel):
    joint: str
    kp: float = Field(default=100.0, description="Proportional gain")
    ki: float = Field(default=0.0, description="Integral gain")
    kd: float = Field(default=10.0, description="Derivative gain")
    max_torque: float = Field(default=150.0, description="Max actuator torque in Nm")


class ProjectMetadata(BaseModel):
    name: str
    description: str = ""
    created_at: str
    updated_at: str
    author: str = "MonkeyBots User"


class RobotDefinition(BaseModel):
    model_file: str = "robot.mjcf"
    urdf_file: Optional[str] = "robot.urdf"
    dof: int = Field(default=6, description="Degrees of freedom")
    end_effector_site: str = "flange_site"
    default_qpos: List[float] = Field(default_factory=list)


class PhysicsConfig(BaseModel):
    timestep: float = Field(default=0.002, description="Simulation integration timestep in seconds")
    integrator: str = Field(default="RK4", description="Numerical integrator (Euler, RK4, implicit)")
    gravity: List[float] = Field(default=[-0.0, 0.0, -9.81])
    collision_tolerance: float = 0.001


class ControllerConfig(BaseModel):
    default_mode: str = "position"
    gains: List[JointControllerGain] = Field(default_factory=list)


class ProjectManifest(BaseModel):
    version: str = "1.0.0"
    metadata: ProjectMetadata
    robot: RobotDefinition
    physics: PhysicsConfig
    controllers: ControllerConfig
