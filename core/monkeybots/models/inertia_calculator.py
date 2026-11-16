"""
Analytical Moment of Inertia Calculator
Calculates exact positive-definite inertia tensors for standard primitive mechanical shapes.
"""

import math
from typing import List, Optional
from .robot import InertiaTensor, Geometry, GeometryType


def calculate_box_inertia(size: List[float], mass: float) -> InertiaTensor:
    """
    Inertia of a solid rectangular cuboid of dimensions [x, y, z] centered at origin.
    Ixx = (1/12) * m * (y^2 + z^2)
    Iyy = (1/12) * m * (x^2 + z^2)
    Izz = (1/12) * m * (x^2 + y^2)
    """
    x, y, z = size[0], size[1], size[2]
    m12 = mass / 12.0
    ixx = m12 * (y * y + z * z)
    iyy = m12 * (x * x + z * z)
    izz = m12 * (x * x + y * y)
    return InertiaTensor(ixx=round(ixx, 6), iyy=round(iyy, 6), izz=round(izz, 6))


def calculate_cylinder_inertia(radius: float, length: float, mass: float) -> InertiaTensor:
    """
    Inertia of a solid cylinder aligned along Z-axis.
    Ixx = Iyy = (1/12) * m * (3*r^2 + h^2)
    Izz = (1/2) * m * r^2
    """
    ixx = (1.0 / 12.0) * mass * (3 * radius * radius + length * length)
    iyy = ixx
    izz = 0.5 * mass * radius * radius
    return InertiaTensor(ixx=round(ixx, 6), iyy=round(iyy, 6), izz=round(izz, 6))


def calculate_sphere_inertia(radius: float, mass: float) -> InertiaTensor:
    """
    Inertia of a solid sphere centered at origin.
    Ixx = Iyy = Izz = (2/5) * m * r^2
    """
    i = 0.4 * mass * radius * radius
    return InertiaTensor(ixx=round(i, 6), iyy=round(i, 6), izz=round(i, 6))


def compute_geometry_inertia(geom: Geometry, mass: float) -> InertiaTensor:
    """Compute analytical inertia tensor for any primitive geometry."""
    if geom.type == GeometryType.BOX:
        size = geom.size or [0.1, 0.1, 0.1]
        return calculate_box_inertia(size, mass)
    elif geom.type == GeometryType.CYLINDER:
        radius = geom.radius or 0.05
        length = geom.length or 0.2
        return calculate_cylinder_inertia(radius, length, mass)
    elif geom.type == GeometryType.SPHERE:
        radius = geom.radius or 0.05
        return calculate_sphere_inertia(radius, mass)
    else:
        # Fallback bounding box approximation for mesh
        return calculate_box_inertia([0.1, 0.1, 0.1], mass)
