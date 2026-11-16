"""
Simulation Lifecycle Router
Controls the live MuJoCo physics simulation engine and exposes verification benchmarks.
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from core.monkeybots.simulation.engine import SimulationEngine, SimulationConfig
from core.monkeybots.simulation.benchmarks import run_all_physics_benchmarks
from server.monkeybots_server.schemas.commands import SimControlAction
from server.monkeybots_server.utils.logger import get_logger

router = APIRouter(prefix="/api/v1/simulation", tags=["Simulation Control"])
logger = get_logger("router_simulation")

# Singleton simulation engine instance
live_engine = SimulationEngine()

# Automatically load default 6-DOF arm model if present
default_mjcf_path = Path("projects/default_6dof_arm/robot.mjcf")
if default_mjcf_path.exists():
    try:
        live_engine.load_from_xml(default_mjcf_path.read_text(encoding="utf-8"))
        logger.info(f"Loaded default 6-DOF arm model into simulation engine from {default_mjcf_path}")
    except Exception as e:
        logger.warning(f"Could not preload default arm model: {e}")


class SimStatusResponse(BaseModel):
    is_active: bool
    status: str
    timestep: float
    sim_time: float
    step_count: int
    real_time_factor: float
    dof: int
    energy: Dict[str, float]


@router.get("/status", response_model=SimStatusResponse)
async def get_simulation_status():
    """Returns real-time execution state of the physics engine."""
    energy = live_engine.compute_energy()
    dof = live_engine.model.nv if live_engine.model else 0

    return SimStatusResponse(
        is_active=live_engine.model is not None,
        status=live_engine.status,
        timestep=live_engine.config.timestep,
        sim_time=round(live_engine.sim_time, 4),
        step_count=live_engine.step_count,
        real_time_factor=round(live_engine.real_time_factor, 2),
        dof=dof,
        energy=energy,
    )


@router.post("/control")
async def control_simulation(action: SimControlAction):
    """Start, pause, step, or reset live simulation."""
    act = action.action.upper()
    logger.info(f"Simulation control received: {act}")

    if act == "PAUSE":
        live_engine.pause()
    elif act == "START":
        live_engine.start()
    elif act == "RESET":
        live_engine.reset()
    elif act == "STEP":
        n_steps = int(action.step_size / live_engine.config.timestep) if action.step_size else 1
        live_engine.step(max(1, n_steps))

    return {
        "message": f"Simulation set to {live_engine.status}",
        "status": live_engine.status,
        "state": {"status": live_engine.status},
        "sim_time": live_engine.sim_time,
        "step_count": live_engine.step_count,
    }


@router.post("/config")
async def configure_simulation(config: SimulationConfig):
    """Updates simulation parameters (timestep, gravity, integrator, solver iterations)."""
    live_engine.config = config
    if live_engine.model:
        live_engine.model.opt.timestep = config.timestep
        live_engine.model.opt.gravity[:] = config.gravity
    logger.info(f"Simulation configured: timestep={config.timestep}, gravity={config.gravity}")
    return {"message": "Configuration updated successfully", "config": live_engine.config}


@router.get("/benchmarks")
async def get_physics_benchmarks():
    """Runs all 5 controlled physical verification benchmarks and returns analytical results."""
    logger.info("Executing 5 controlled physics verification benchmarks...")
    report = run_all_physics_benchmarks()
    return report
