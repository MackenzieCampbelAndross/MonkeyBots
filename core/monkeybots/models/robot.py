"""
MonkeyBots Core Robot Data Model
Comprehensive representation of hierarchical robotic structures, links, joints, and physical properties.
"""

from enum import Enum
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, Field, model_validator


class JointType(str, Enum):
    REVOLUTE = "revolute"
    CONTINUOUS = "continuous"
    PRISMATIC = "prismatic"
    FIXED = "fixed"


class GeometryType(str, Enum):
    BOX = "box"
    CYLINDER = "cylinder"
    SPHERE = "sphere"
    MESH = "mesh"


class Origin(BaseModel):
    """Position [x, y, z] in meters and orientation [r, p, y] in radians."""
    xyz: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    rpy: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])


class InertiaTensor(BaseModel):
    """
    3x3 Symmetric Moment of Inertia Tensor:
    [[ixx, ixy, ixz],
     [ixy, iyy, iyz],
     [ixz, iyz, izz]]
    """
    ixx: float = Field(..., gt=0.0, description="Moment about X axis (kg*m^2)")
    iyy: float = Field(..., gt=0.0, description="Moment about Y axis (kg*m^2)")
    izz: float = Field(..., gt=0.0, description="Moment about Z axis (kg*m^2)")
    ixy: float = Field(default=0.0, description="Product of inertia XY")
    ixz: float = Field(default=0.0, description="Product of inertia XZ")
    iyz: float = Field(default=0.0, description="Product of inertia YZ")

    def satisfies_triangle_inequalities(self) -> bool:
        """Physical rigid bodies must satisfy triangle inequalities on principal axes."""
        return (
            (self.ixx + self.iyy >= self.izz - 1e-7)
            and (self.ixx + self.izz >= self.iyy - 1e-7)
            and (self.iyy + self.izz >= self.ixx - 1e-7)
        )


class Inertial(BaseModel):
    mass: float = Field(..., gt=0.0, description="Mass in kilograms")
    origin: Origin = Field(default_factory=Origin, description="Center of Mass location")
    inertia: InertiaTensor


class Geometry(BaseModel):
    type: GeometryType
    # Parameters depending on type:
    # box: size = [x, y, z]
    # cylinder: radius, length
    # sphere: radius
    # mesh: filename, scale = [sx, sy, sz]
    size: Optional[List[float]] = None
    radius: Optional[float] = None
    length: Optional[float] = None
    filename: Optional[str] = None
    scale: Optional[List[float]] = None


class Material(BaseModel):
    name: str = "default_mat"
    rgba: List[float] = Field(default_factory=lambda: [0.8, 0.8, 0.8, 1.0])
    friction: float = Field(default=0.8, ge=0.0, description="Coulomb friction coefficient")
    restitution: float = Field(default=0.0, ge=0.0, le=1.0, description="Coefficient of restitution")


class Visual(BaseModel):
    name: Optional[str] = None
    origin: Origin = Field(default_factory=Origin)
    geometry: Geometry
    material: Optional[Material] = None


class Collision(BaseModel):
    name: Optional[str] = None
    origin: Origin = Field(default_factory=Origin)
    geometry: Geometry


class Link(BaseModel):
    name: str
    inertial: Optional[Inertial] = None
    visuals: List[Visual] = Field(default_factory=list)
    collisions: List[Collision] = Field(default_factory=list)


class JointLimits(BaseModel):
    lower: float = Field(default=-3.14159, description="Lower limit (rad or m)")
    upper: float = Field(default=3.14159, description="Upper limit (rad or m)")
    effort: float = Field(default=150.0, gt=0.0, description="Max joint torque or force (Nm or N)")
    velocity: float = Field(default=3.14159, gt=0.0, description="Max joint velocity (rad/s or m/s)")


class JointDynamics(BaseModel):
    damping: float = Field(default=0.1, ge=0.0, description="Viscous damping (Nms/rad)")
    friction: float = Field(default=0.05, ge=0.0, description="Dry Coulomb friction (Nm)")
    armature: float = Field(default=0.01, ge=0.0, description="Rotor inertia (kg*m^2)")


class Joint(BaseModel):
    name: str
    type: JointType
    parent: str = Field(..., description="Parent link name")
    child: str = Field(..., description="Child link name")
    origin: Origin = Field(default_factory=Origin, description="Transform from parent link to joint origin")
    axis: List[float] = Field(default_factory=lambda: [0.0, 0.0, 1.0], description="Unit rotation/translation axis")
    limits: Optional[JointLimits] = None
    dynamics: Optional[JointDynamics] = None


class RobotModel(BaseModel):
    name: str
    root_link: str
    links: Dict[str, Link] = Field(default_factory=dict)
    joints: Dict[str, Joint] = Field(default_factory=dict)

    def get_dof(self) -> int:
        """Count active degrees of freedom (revolute, continuous, prismatic)."""
        return sum(
            1 for j in self.joints.values()
            if j.type in (JointType.REVOLUTE, JointType.CONTINUOUS, JointType.PRISMATIC)
        )

    def get_children_of(self, link_name: str) -> List[Tuple[Joint, str]]:
        """Return list of (joint, child_link_name) connected to the specified link."""
        res = []
        for j in self.joints.values():
            if j.parent == link_name:
                res.append((j, j.child))
        return res
