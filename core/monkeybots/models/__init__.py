"""
MonkeyBots Robot Description and Mechanical Configuration Module
"""

from .robot import (
    RobotModel,
    Link,
    Joint,
    Inertial,
    InertiaTensor,
    Origin,
    Geometry,
    GeometryType,
    Material,
    Visual,
    Collision,
    JointType,
    JointLimits,
    JointDynamics,
)
from .inertia_calculator import (
    calculate_box_inertia,
    calculate_cylinder_inertia,
    calculate_sphere_inertia,
    compute_geometry_inertia,
)
from .validator import validate_robot_model, ValidationReport, ValidationError
from .urdf_parser import export_urdf, import_urdf
from .mjcf_builder import export_mjcf, validate_in_mujoco
from .assets.sample_6dof_arm import create_sample_6dof_arm

__all__ = [
    "RobotModel",
    "Link",
    "Joint",
    "Inertial",
    "InertiaTensor",
    "Origin",
    "Geometry",
    "GeometryType",
    "Material",
    "Visual",
    "Collision",
    "JointType",
    "JointLimits",
    "JointDynamics",
    "calculate_box_inertia",
    "calculate_cylinder_inertia",
    "calculate_sphere_inertia",
    "compute_geometry_inertia",
    "validate_robot_model",
    "ValidationReport",
    "ValidationError",
    "export_urdf",
    "import_urdf",
    "export_mjcf",
    "validate_in_mujoco",
    "create_sample_6dof_arm",
]
