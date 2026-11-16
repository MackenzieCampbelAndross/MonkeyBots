"""
MonkeyBots Kinematics REST API Router.

Endpoints for Forward Kinematics, Inverse Kinematics, Jacobian,
Kinematic Chain inspection, and standard engineering poses.
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.monkeybots.models.assets.sample_6dof_arm import create_sample_6dof_arm
from core.monkeybots.kinematics import (
    KinematicChain,
    compute_forward_kinematics,
    compute_geometric_jacobian,
    IKSolver,
    IKSolverMethod,
)
from server.monkeybots_server.utils.logger import get_logger

router = APIRouter(prefix="/api/v1/kinematics", tags=["Kinematics Engine"])
logger = get_logger("router_kinematics")

# Cache default kinematic chains by robot identifier
_cached_chains: Dict[str, KinematicChain] = {}


def get_or_create_chain(robot_id: str = "default_6dof_arm", ee_link: Optional[str] = None) -> KinematicChain:
    """Retrieves or builds the KinematicChain for the requested robot."""
    cache_key = f"{robot_id}_{ee_link or 'default'}"
    if cache_key not in _cached_chains:
        # Load sample 6-DOF arm or user robot
        robot = create_sample_6dof_arm()
        chain = KinematicChain(robot, end_effector_link=ee_link)
        _cached_chains[cache_key] = chain
    return _cached_chains[cache_key]


# --- Pydantic Request & Response Schemas ---

class FKRequest(BaseModel):
    robot_id: str = "default_6dof_arm"
    joint_positions: List[float] = Field(default_factory=lambda: [0.0] * 6)
    end_effector_link: Optional[str] = None


class IKRequest(BaseModel):
    robot_id: str = "default_6dof_arm"
    target_position: List[float] = Field(..., description="Target [x, y, z] in meters")
    target_rpy_deg: Optional[List[float]] = Field(None, description="Target Roll-Pitch-Yaw in degrees")
    target_rpy_rad: Optional[List[float]] = Field(None, description="Target Roll-Pitch-Yaw in radians")
    target_quaternion: Optional[List[float]] = Field(None, description="Target [w, x, y, z] unit quaternion")
    initial_seed: Optional[List[float]] = Field(None, description="Initial joint coordinates seed [rad]")
    method: str = Field(default="damped_least_squares", description="dls, pseudo_inverse, jacobian_transpose")
    pos_tolerance_m: float = Field(default=1e-4, description="Position tolerance in meters (0.1 mm)")
    rot_tolerance_rad: float = Field(default=1e-3, description="Orientation tolerance in radians")
    max_iterations: int = Field(default=150, description="Maximum solver iterations")


# --- Endpoints ---

@router.get("/chain")
async def get_kinematic_chain(robot_id: str = "default_6dof_arm", ee_link: Optional[str] = None):
    """Returns the kinematic chain structure, joint limits, axes, and DOF."""
    chain = get_or_create_chain(robot_id, ee_link)
    return {
        "robot_id": robot_id,
        "base_link": chain.base_link,
        "end_effector_link": chain.end_effector_link,
        "dof": chain.dof,
        "joints": [
            {
                "name": elem.name,
                "type": elem.joint_type.value,
                "parent_link": elem.parent_link_name,
                "child_link": elem.child_link_name,
                "lower_limit_rad": round(elem.lower_limit, 4),
                "upper_limit_rad": round(elem.upper_limit, 4),
                "lower_limit_deg": round(float(elem.lower_limit * 180.0 / 3.14159265), 1),
                "upper_limit_deg": round(float(elem.upper_limit * 180.0 / 3.14159265), 1),
                "axis": [round(float(a), 4) for a in elem.axis],
                "origin_xyz": elem.joint.origin.xyz if elem.joint.origin else [0.0, 0.0, 0.0],
            }
            for elem in chain.active_elements
        ],
        "links": [elem.child_link_name for elem in chain.elements],
    }


@router.post("/fk")
async def forward_kinematics(req: FKRequest):
    """
    Computes forward kinematics for given joint positions.
    Returns end-effector position, orientation, transformation matrix, and Jacobian.
    """
    chain = get_or_create_chain(req.robot_id, req.end_effector_link)
    if len(req.joint_positions) != chain.dof:
        raise HTTPException(
            status_code=400,
            detail=f"Expected {chain.dof} joint coordinates, got {len(req.joint_positions)}.",
        )

    fk = compute_forward_kinematics(chain, req.joint_positions)
    jac = compute_geometric_jacobian(chain, req.joint_positions)
    diag_warnings = jac.diagnose_singularity(req.joint_positions, chain)

    fk_dict = fk.to_dict()
    jac_dict = jac.to_dict()

    return {
        **fk_dict,
        "jacobian_analysis": jac_dict,
        "warnings": diag_warnings,
        "dof": chain.dof,
    }


@router.post("/ik")
async def inverse_kinematics(req: IKRequest):
    """
    Solves inverse kinematics for desired target position and orientation.
    """
    chain = get_or_create_chain(req.robot_id)

    # Determine target orientation format
    target_orientation = None
    if req.target_quaternion is not None:
        target_orientation = req.target_quaternion
    elif req.target_rpy_rad is not None:
        target_orientation = req.target_rpy_rad
    elif req.target_rpy_deg is not None:
        # Convert deg to rad
        target_orientation = [float(val * 3.141592653589793 / 180.0) for val in req.target_rpy_deg]

    method_map = {
        "damped_least_squares": IKSolverMethod.DLS,
        "dls": IKSolverMethod.DLS,
        "pseudo_inverse": IKSolverMethod.PSEUDO_INVERSE,
        "pinv": IKSolverMethod.PSEUDO_INVERSE,
        "jacobian_transpose": IKSolverMethod.JACOBIAN_TRANSPOSE,
    }
    solver_method = method_map.get(req.method.lower(), IKSolverMethod.DLS)

    solver = IKSolver(chain)
    result = solver.solve(
        target_position=req.target_position,
        target_orientation=target_orientation,
        initial_seed=req.initial_seed,
        method=solver_method,
        pos_tolerance_m=req.pos_tolerance_m,
        rot_tolerance_rad=req.rot_tolerance_rad,
        max_iterations=req.max_iterations,
    )

    return result.to_dict()


@router.get("/presets")
async def get_pose_presets(robot_id: str = "default_6dof_arm"):
    """Returns standard engineering postures and targets for benchmarking and inspection."""
    return {
        "presets": [
            {
                "name": "Zero Posture",
                "description": "All joint coordinates set to 0.0 radians",
                "joints_rad": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                "target_pos": [0.35, 0.0, 0.90],
            },
            {
                "name": "Home / Ready Pose",
                "description": "Standard industrial ready posture with elbow bent at 90 deg",
                "joints_rad": [0.0, -0.5, 1.2, 0.0, 0.8, 0.0],
                "target_pos": [0.45, 0.0, 0.55],
            },
            {
                "name": "Pick Pose (Table Left)",
                "description": "Reaching down to pick object at workbench left",
                "joints_rad": [0.785, 0.4, 0.9, 0.0, 0.3, 0.785],
                "target_pos": [0.35, 0.35, 0.25],
            },
            {
                "name": "Place Pose (Table Right)",
                "description": "Reaching down to place object at workbench right",
                "joints_rad": [-0.785, 0.4, 0.9, 0.0, 0.3, -0.785],
                "target_pos": [0.35, -0.35, 0.25],
            },
            {
                "name": "Wrist Singularity Test",
                "description": "Joint 5 set to 0.0 rad, aligning joint 4 and joint 6 axes",
                "joints_rad": [0.0, 0.2, 0.5, 0.0, 0.0, 0.0],
                "target_pos": [0.55, 0.0, 0.75],
            },
            {
                "name": "Full Outreach Singularity",
                "description": "Arm fully extended horizontally to boundary limit",
                "joints_rad": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                "target_pos": [0.85, 0.0, 0.60],
            },
        ]
    }
