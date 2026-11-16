"""
MonkeyBots Project Manifest & Configuration Schemas
Defines structured filesystem project metadata, robot definitions, physics parameters,
material properties, geometry references, trajectories, and experiment indices.
100% database-free, local-first JSON serialization.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class JointControllerGain(BaseModel):
    joint: str
    kp: float = Field(default=100.0, description="Proportional gain")
    ki: float = Field(default=0.0, description="Integral gain")
    kd: float = Field(default=10.0, description="Derivative gain")
    max_torque: float = Field(default=150.0, description="Max actuator torque in Nm")


class ProjectMetadata(BaseModel):
    id: Optional[str] = Field(default=None, description="Unique slug identifier (matches project directory name)")
    name: str = Field(..., description="Display title")
    description: str = Field(default="", description="Engineering notes or project summary")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    author: str = Field(default="MonkeyBots Engineer")
    robot_type: str = Field(default="Articulated Arm", description="'Articulated Arm', 'SCARA', 'Delta', 'Mobile Manipulator', 'Custom'")
    tags: List[str] = Field(default_factory=lambda: ["robotics", "simulation"])
    version_tag: str = Field(default="v1.0.0")


class RobotDefinition(BaseModel):
    model_file: str = Field(default="robot.mjcf", description="Relative path to primary MJCF model")
    urdf_file: Optional[str] = Field(default="robot.urdf", description="Relative path to URDF model")
    dof: int = Field(default=6, description="Degrees of freedom")
    end_effector_site: str = Field(default="flange_site", description="Primary tool flange site name")
    default_qpos: List[float] = Field(default_factory=list, description="Home configuration in radians")
    base_link: str = Field(default="base_link")
    flange_link: str = Field(default="link_6")


class MaterialProperty(BaseModel):
    name: str
    rgba: List[float] = Field(default_factory=lambda: [0.7, 0.7, 0.7, 1.0])
    friction: List[float] = Field(default_factory=lambda: [0.8, 0.005, 0.0001], description="[sliding, torsional, rolling]")
    density: float = Field(default=2700.0, description="Density in kg/m^3 (e.g. Aluminum 2700)")
    roughness: float = Field(default=0.5)


class GeometryAssetReference(BaseModel):
    name: str
    relative_path: str = Field(..., description="Relative path within assets/ folder (e.g. 'assets/flange.stl')")
    format: str = Field(default="stl", description="'stl', 'obj', 'dae'")
    scale: List[float] = Field(default_factory=lambda: [1.0, 1.0, 1.0])


class PhysicsConfig(BaseModel):
    timestep: float = Field(default=0.002, description="Simulation integration timestep in seconds (e.g. 0.002 for 500 Hz)")
    integrator: str = Field(default="RK4", description="Numerical integrator: 'Euler', 'RK4', 'implicit'")
    gravity: List[float] = Field(default_factory=lambda: [0.0, 0.0, -9.81])
    collision_tolerance: float = Field(default=0.001)
    solver: str = Field(default="Newton", description="'PGS', 'CG', 'Newton'")
    iterations: int = Field(default=50)


class ControllerConfig(BaseModel):
    default_mode: str = Field(default="position", description="'position', 'velocity', 'torque'")
    gains: List[JointControllerGain] = Field(default_factory=list)


class TrajectoryMetadata(BaseModel):
    id: str
    name: str
    relative_path: str
    interpolation: str = "quintic"
    waypoints_count: int = 0
    duration_s: float = 0.0


class ProjectManifest(BaseModel):
    """
    Complete root manifest saved as project.json inside each project directory.
    Guarantees portable, relative asset referencing and full offline reconstruction.
    """
    version: str = "1.1.0"
    metadata: ProjectMetadata
    robot: RobotDefinition
    physics: PhysicsConfig = Field(default_factory=PhysicsConfig)
    controllers: ControllerConfig = Field(default_factory=ControllerConfig)
    materials: Dict[str, MaterialProperty] = Field(default_factory=dict)
    assets: List[GeometryAssetReference] = Field(default_factory=list)
    trajectories: List[TrajectoryMetadata] = Field(default_factory=list)
    experiments: List[str] = Field(default_factory=list, description="IDs of stored experiments")
    reports: List[str] = Field(default_factory=list, description="Relative paths to markdown/pdf reports")
