"""
Robot Modelling & Mechanical Configuration API Router
Exposes endpoints for robot model validation, URDF/MJCF import/export, and inertia computation.
"""

from fastapi import APIRouter, HTTPException, status, Body
from pydantic import BaseModel
from typing import List, Optional
from core.monkeybots.models.robot import RobotModel, Geometry, InertiaTensor
from core.monkeybots.models.validator import validate_robot_model, ValidationReport
from core.monkeybots.models.urdf_parser import export_urdf, import_urdf
from core.monkeybots.models.mjcf_builder import export_mjcf, validate_in_mujoco
from core.monkeybots.models.inertia_calculator import compute_geometry_inertia
from core.monkeybots.models.assets.sample_6dof_arm import create_sample_6dof_arm
from core.monkeybots.models.registry import ROBOT_REGISTRY, list_available_robots, get_robot_model
from server.monkeybots_server.utils.logger import get_logger

router = APIRouter(prefix="/api/v1/models", tags=["Robot Modelling & Mechanical Config"])
logger = get_logger("router_models")


@router.get("/registry")
async def get_robot_registry():
    """Lists all registered robot models and their mechanical properties."""
    items = []
    for key in list_available_robots():
        try:
            m = get_robot_model(key)
            items.append({
                "id": key,
                "name": m.name,
                "dof": m.get_dof(),
                "link_count": len(m.links),
                "joint_count": len(m.joints),
                "root_link": m.root_link,
            })
        except Exception as e:
            logger.warning(f"Failed to load metadata for robot '{key}': {e}")
    return {"robots": items}


@router.get("/registry/{robot_id}", response_model=RobotModel)
async def get_registered_robot_by_id(robot_id: str):
    """Instantiates and returns the full RobotModel for a registered robot."""
    try:
        return get_robot_model(robot_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Robot '{robot_id}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class XMLPayload(BaseModel):
    xml_content: str


class ExportResponse(BaseModel):
    format: str
    content: str
    mujoco_verified: bool = False
    verification_message: str = ""


class InertiaCalcRequest(BaseModel):
    geometry: Geometry
    mass: float


@router.get("/sample-6dof", response_model=RobotModel)
async def get_sample_6dof_model():
    """Returns the verified 6-DOF industrial robot arm description."""
    return create_sample_6dof_arm()


@router.post("/validate", response_model=ValidationReport)
async def validate_model(model: RobotModel):
    """Deep structural and physical validation of a robot model."""
    report = validate_robot_model(model)
    logger.info(f"Validated robot '{model.name}': valid={report.is_valid}, errors={len(report.errors)}, warnings={len(report.warnings)}")
    return report


@router.post("/export/urdf", response_model=ExportResponse)
async def export_robot_urdf(model: RobotModel):
    """Exports a RobotModel into standard ROS URDF XML format."""
    try:
        urdf_str = export_urdf(model)
        return ExportResponse(format="URDF", content=urdf_str, mujoco_verified=False)
    except Exception as e:
        logger.error(f"Failed to export URDF: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/export/mjcf", response_model=ExportResponse)
async def export_robot_mjcf(model: RobotModel):
    """Exports a RobotModel into native MuJoCo XML (MJCF) and verifies engine compilation."""
    try:
        mjcf_str = export_mjcf(model)
        is_valid, msg = validate_in_mujoco(mjcf_str)
        return ExportResponse(
            format="MJCF",
            content=mjcf_str,
            mujoco_verified=is_valid,
            verification_message=msg,
        )
    except Exception as e:
        logger.error(f"Failed to export MJCF: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/import/urdf", response_model=RobotModel)
async def import_robot_urdf(payload: XMLPayload):
    """Parses standard ROS URDF XML into an internal RobotModel."""
    try:
        model = import_urdf(payload.xml_content)
        return model
    except Exception as e:
        logger.error(f"Failed to import URDF: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"URDF Parsing error: {e}")


@router.post("/calculate-inertia", response_model=InertiaTensor)
async def calculate_inertia(req: InertiaCalcRequest):
    """Computes analytical moment of inertia tensor for primitive geometries."""
    return compute_geometry_inertia(req.geometry, req.mass)
