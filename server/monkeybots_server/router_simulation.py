"""
Simulation Lifecycle Router
Exposes simulation control and status endpoints.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from server.monkeybots_server.schemas.commands import SimControlAction
from server.monkeybots_server.utils.logger import get_logger

router = APIRouter(prefix="/api/v1/simulation", tags=["Simulation Control"])
logger = get_logger("router_simulation")


class SimStatus(BaseModel):
    is_active: bool
    status: str  # STOPPED, RUNNING, PAUSED
    model_name: str
    timestep: float
    sim_time: float
    step_count: int


# Global simulation state container
_CURRENT_STATE = {
    "is_active": True,
    "status": "RUNNING",
    "model_name": "Industrial 6-DOF Robotic Arm",
    "timestep": 0.002,
    "sim_time": 0.0,
    "step_count": 0,
}


@router.get("/status", response_model=SimStatus)
async def get_simulation_status():
    """Returns current execution state of the simulation engine."""
    return SimStatus(**_CURRENT_STATE)


@router.post("/control")
async def control_simulation(action: SimControlAction):
    """Start, pause, step, or reset simulation."""
    act = action.action.upper()
    logger.info(f"Simulation control received: {act}")
    
    if act == "PAUSE":
        _CURRENT_STATE["status"] = "PAUSED"
    elif act == "START":
        _CURRENT_STATE["status"] = "RUNNING"
    elif act == "RESET":
        _CURRENT_STATE["status"] = "RUNNING"
        _CURRENT_STATE["sim_time"] = 0.0
        _CURRENT_STATE["step_count"] = 0
    elif act == "STEP":
        step_dt = action.step_size or _CURRENT_STATE["timestep"]
        _CURRENT_STATE["sim_time"] += step_dt
        _CURRENT_STATE["step_count"] += 1

    return {"message": f"Simulation set to {_CURRENT_STATE['status']}", "state": _CURRENT_STATE}
