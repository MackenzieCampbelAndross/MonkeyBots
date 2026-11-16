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
from core.monkeybots.simulation.manipulation import (
    GripperCommand,
    PickAndPlaceRequest,
    ManipulationController,
)
from core.monkeybots.simulation.manipulation_benchmarks import run_all_manipulation_benchmarks
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


# Environment Objects Cache
_environment_objects: List[Dict[str, Any]] = [
    {
        "id": "work_table",
        "name": "Work Table Surface",
        "type": "table",
        "position": [0.45, 0.15, 0.0],
        "rotation": [0.0, 0.0, 0.0],
        "size": [0.6, 0.3, 0.8],
        "color": "#334155",
    },
    {
        "id": "target_part",
        "name": "Pick Target Part",
        "type": "box",
        "position": [0.45, 0.33, 0.0],
        "rotation": [0.0, 0.0, 0.0],
        "size": [0.06, 0.06, 0.06],
        "color": "#f59e0b",
    },
]


@router.get("/environment")
async def get_environment_objects():
    """Returns active 3D simulation environment objects, surfaces, and obstacles."""
    return {"objects": _environment_objects}


@router.post("/environment")
async def add_environment_object(obj: Dict[str, Any]):
    """Adds or updates a 3D simulation environment object."""
    # Replace if ID exists, otherwise append
    obj_id = obj.get("id", f"obj_{len(_environment_objects) + 1}")
    obj["id"] = obj_id
    idx = next((i for i, o in enumerate(_environment_objects) if o["id"] == obj_id), None)
    if idx is not None:
        _environment_objects[idx] = obj
    else:
        _environment_objects.append(obj)
    logger.info(f"Environment object updated: {obj.get('name', obj_id)}")
    return {"message": "Environment object updated", "object": obj}


@router.get("/sync_metrics")
async def get_synchronization_metrics():
    """
    Returns high-frequency simulation synchronization metrics:
    Sim time, step count, real-time factor, measured loop latency, and contact states.
    """
    contacts_count = int(live_engine.data.ncon) if live_engine.data else 0
    return {
        "is_active": live_engine.model is not None,
        "status": live_engine.status,
        "sim_time": round(live_engine.sim_time, 4),
        "step_count": live_engine.step_count,
        "real_time_factor": round(live_engine.real_time_factor, 2),
        "telemetry_rate_hz": 60.0,
        "sync_latency_ms": round(live_engine.last_step_latency_ms, 2),
        "contacts_count": contacts_count,
        "dof": live_engine.model.nv if live_engine.model else 0,
    }


@router.post("/gripper/command")
async def command_gripper(cmd: GripperCommand):
    """Actuates the parallel-jaw gripper fingers or sets grasping squeeze force."""
    act = cmd.action.upper()
    if act == "OPEN":
        live_engine.set_gripper_force(0.0)
    elif act == "CLOSE":
        live_engine.set_gripper_force(cmd.force_n)
    elif act == "SET_FORCE":
        live_engine.set_gripper_force(cmd.force_n)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown gripper action: {cmd.action}",
        )

    # Step physics slightly to update contact manifolds
    live_engine.step(10)
    state = live_engine.get_gripper_state()
    logger.info(f"Gripper commanded: {act} (force={cmd.force_n}N, state={state})")
    return {"message": f"Gripper command {act} executed", "gripper": state}


@router.get("/gripper/status")
async def get_gripper_status():
    """Returns current gripper aperture, finger normal forces, and grasping status."""
    return live_engine.get_gripper_state()


@router.get("/contacts")
async def get_active_contacts():
    """Returns active contact points, normal forces, friction forces, and contact categories."""
    contacts = live_engine.get_contact_dynamics()
    return {
        "count": len(contacts),
        "contacts": [c.model_dump() for c in contacts],
    }


@router.get("/collision_events")
async def get_collision_events(limit: int = 50):
    """Returns recent discrete collision events (impacts, impulses, onsets)."""
    events = live_engine.get_collision_events(limit=limit)
    return {
        "count": len(events),
        "events": [e.model_dump() for e in events],
    }


@router.post("/manipulation/pick_and_place")
async def execute_pick_and_place(plan: PickAndPlaceRequest):
    """Executes an autonomous pick-and-place sequence using contact physics and IK."""
    engine = live_engine
    # If the live engine is running robot-only model, run pick-and-place with the workcell model
    workcell_path = Path("projects/default_6dof_arm/workcell.mjcf")
    if engine.model is not None and "gripper" not in str(engine.model.names).lower() and workcell_path.exists():
        engine = SimulationEngine()
        engine.load_from_xml(workcell_path.read_text(encoding="utf-8"))

    controller = ManipulationController(engine)
    report = controller.execute_pick_and_place(plan)
    return report


@router.get("/manipulation_benchmarks")
async def get_manipulation_benchmarks():
    """Runs all 5 controlled physical verification experiments and returns report."""
    report = run_all_manipulation_benchmarks()
    return report
