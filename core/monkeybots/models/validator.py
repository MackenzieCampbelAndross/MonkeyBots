"""
MonkeyBots Robot Model Validator
Validates robotic kinematic structures, physical parameters, geometry, and connectivity.
"""

from typing import List, Dict, Set, Optional
from pydantic import BaseModel
from .robot import RobotModel, JointType, GeometryType


class ValidationError(BaseModel):
    code: str
    message: str
    element_id: Optional[str] = None
    severity: str = "ERROR"  # ERROR or WARNING


class ValidationReport(BaseModel):
    is_valid: bool
    errors: List[ValidationError] = []
    warnings: List[ValidationError] = []
    dof: int = 0
    link_count: int = 0
    joint_count: int = 0


def validate_robot_model(model: RobotModel) -> ValidationReport:
    """Performs deep mechanical and structural validation on a RobotModel."""
    errors: List[ValidationError] = []
    warnings: List[ValidationError] = []

    links = model.links
    joints = model.joints

    # 1. Check Root Link Existence
    if not model.root_link or model.root_link not in links:
        errors.append(
            ValidationError(
                code="ROOT_LINK_NOT_FOUND",
                message=f"Root link '{model.root_link}' does not exist in the links list.",
                element_id=model.root_link,
            )
        )

    # 2. Check Joint Relationships (Parent & Child Existence)
    child_to_parent: Dict[str, str] = {}
    for j_name, joint in joints.items():
        if joint.parent not in links:
            errors.append(
                ValidationError(
                    code="INVALID_JOINT_PARENT",
                    message=f"Joint '{j_name}' specifies parent link '{joint.parent}' which does not exist.",
                    element_id=j_name,
                )
            )

        if joint.child not in links:
            errors.append(
                ValidationError(
                    code="INVALID_JOINT_CHILD",
                    message=f"Joint '{j_name}' specifies child link '{joint.child}' which does not exist.",
                    element_id=j_name,
                )
            )

        # Check for multiple parents
        if joint.child in child_to_parent:
            errors.append(
                ValidationError(
                    code="MULTIPLE_PARENTS",
                    message=f"Link '{joint.child}' has multiple parent joints ('{child_to_parent[joint.child]}' and '{j_name}'). Kinematic tree must have exactly one parent per link.",
                    element_id=joint.child,
                )
            )
        else:
            child_to_parent[joint.child] = j_name

        # 3. Check Joint Limits
        if joint.type in (JointType.REVOLUTE, JointType.PRISMATIC):
            if not joint.limits:
                errors.append(
                    ValidationError(
                        code="MISSING_JOINT_LIMITS",
                        message=f"Actuated joint '{j_name}' ({joint.type}) requires defined upper/lower limits.",
                        element_id=j_name,
                    )
                )
            else:
                if joint.limits.lower >= joint.limits.upper:
                    errors.append(
                        ValidationError(
                            code="INVALID_JOINT_LIMIT_BOUNDS",
                            message=f"Joint '{j_name}' has lower limit ({joint.limits.lower}) >= upper limit ({joint.limits.upper}).",
                            element_id=j_name,
                        )
                    )
                if joint.limits.effort <= 0:
                    errors.append(
                        ValidationError(
                            code="NON_POSITIVE_EFFORT",
                            message=f"Joint '{j_name}' has non-positive effort limit ({joint.limits.effort} Nm/N).",
                            element_id=j_name,
                        )
                    )

    # 4. Check Kinematic Cycles & Reachability from Root Link
    if model.root_link in links:
        visited: Set[str] = set()
        queue = [model.root_link]

        while queue:
            curr = queue.pop(0)
            if curr in visited:
                errors.append(
                    ValidationError(
                        code="KINEMATIC_CYCLE_DETECTED",
                        message=f"Kinematic loop/cycle detected reaching link '{curr}'.",
                        element_id=curr,
                    )
                )
                break
            visited.add(curr)

            # Enqueue all children
            for child_j, child_link in model.get_children_of(curr):
                queue.append(child_link)

        # Check for Disconnected / Orphaned Links
        for l_name in links:
            if l_name not in visited:
                errors.append(
                    ValidationError(
                        code="DISCONNECTED_LINK",
                        message=f"Link '{l_name}' is disconnected from the root link '{model.root_link}'.",
                        element_id=l_name,
                    )
                )

    # 5. Check Physical Parameters & Geometry
    for l_name, link in links.items():
        if link.inertial:
            # Mass check
            if link.inertial.mass <= 0:
                errors.append(
                    ValidationError(
                        code="NON_POSITIVE_MASS",
                        message=f"Link '{l_name}' has invalid mass: {link.inertial.mass} kg.",
                        element_id=l_name,
                    )
                )

            # Inertia check
            it = link.inertial.inertia
            if it.ixx <= 0 or it.iyy <= 0 or it.izz <= 0:
                errors.append(
                    ValidationError(
                        code="NON_POSITIVE_INERTIA",
                        message=f"Link '{l_name}' has non-positive diagonal moments of inertia: [{it.ixx}, {it.iyy}, {it.izz}].",
                        element_id=l_name,
                    )
                )
            elif not it.satisfies_triangle_inequalities():
                warnings.append(
                    ValidationError(
                        code="TRIANGLE_INEQUALITY_VIOLATION",
                        message=f"Inertia tensor for link '{l_name}' violates physical triangle inequality.",
                        element_id=l_name,
                        severity="WARNING",
                    )
                )
        else:
            # Root link can be fixed/inertialless, but dynamic links should have inertia
            if l_name != model.root_link:
                warnings.append(
                    ValidationError(
                        code="MISSING_INERTIAL",
                        message=f"Link '{l_name}' does not define inertial properties.",
                        element_id=l_name,
                        severity="WARNING",
                    )
                )

        # Validate Visual and Collision Geometries
        for v in link.visuals + link.collisions:
            g = v.geometry
            if g.type == GeometryType.BOX:
                if not g.size or any(s <= 0 for s in g.size):
                    errors.append(
                        ValidationError(
                            code="INVALID_BOX_SIZE",
                            message=f"Box geometry in link '{l_name}' has invalid or non-positive size: {g.size}.",
                            element_id=l_name,
                        )
                    )
            elif g.type == GeometryType.CYLINDER:
                if not g.radius or g.radius <= 0 or not g.length or g.length <= 0:
                    errors.append(
                        ValidationError(
                            code="INVALID_CYLINDER_DIMENSIONS",
                            message=f"Cylinder geometry in link '{l_name}' has invalid radius/length.",
                            element_id=l_name,
                        )
                    )
            elif g.type == GeometryType.SPHERE:
                if not g.radius or g.radius <= 0:
                    errors.append(
                        ValidationError(
                            code="INVALID_SPHERE_RADIUS",
                            message=f"Sphere geometry in link '{l_name}' has non-positive radius.",
                            element_id=l_name,
                        )
                    )

    return ValidationReport(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        dof=model.get_dof(),
        link_count=len(links),
        joint_count=len(joints),
    )
