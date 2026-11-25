"""
MonkeyBots Motion Planning & Robot Control REST API Router.

Endpoints for multi-joint trajectory planning, closed-loop execution in MuJoCo,
PID parameter tuning, and automated step response stability analysis.
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.monkeybots.planning import (
    JointTrajectory,
    CartesianTrajectory,
    InterpolationType,
)
from core.monkeybots.control import (
    RobotMotionController,
    evaluate_step_response,
)
from core.monkeybots.kinematics import KinematicChain
from core.monkeybots.models.assets.sample_6dof_arm import create_sample_6dof_arm
from .router_simulation import live_engine
from .utils.logger import get_logger

import numpy as np
import time
from core.monkeybots.planning.cspace import ConfigurationSpace
from core.monkeybots.planning.collision_checker import MotionCollisionChecker
from core.monkeybots.planning.rrt import RRTPlanner
from core.monkeybots.planning.smoother import shortcut_path

router = APIRouter(prefix="/api/v1/motion", tags=["Motion Planning & Control"])
logger = get_logger("router_motion")


class RRTPlanRequest(BaseModel):
    robot_id: str = "default_6dof_arm"
    q_start: List[float] = Field(default_factory=lambda: [0.0] * 6)
    q_goal: List[float] = Field(default_factory=lambda: [0.5, -0.4, 1.2, 0.0, 0.6, 0.2])
    step_size: float = Field(default=0.15, gt=0.01, le=1.0)
    goal_bias: float = Field(default=0.15, ge=0.0, le=0.5)
    max_iterations: int = Field(default=1500, le=5000)


@router.post("/plan/rrt")
async def plan_rrt_path(req: RRTPlanRequest):
    """Computes a collision-free sampling-based trajectory using RRT and B-spline shortcutting."""
    dof = len(req.q_start)
    cspace = ConfigurationSpace([(-3.14, 3.14) for _ in range(dof)])
    checker = MotionCollisionChecker()
    planner = RRTPlanner(
        cspace,
        checker,
        step_size=req.step_size,
        goal_bias=req.goal_bias,
        max_iterations=req.max_iterations,
    )

    t0 = time.perf_counter()
    raw_path = planner.plan(np.array(req.q_start), np.array(req.q_goal))
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    if raw_path is None:
        raise HTTPException(
            status_code=422,
            detail="RRT planner failed to find a valid collision-free path within the iteration budget.",
        )

    smoothed = shortcut_path(raw_path, cspace, checker, max_iters=50)

    return {
        "success": True,
        "planning_time_ms": round(elapsed_ms, 2),
        "raw_waypoints_count": len(raw_path),
        "smoothed_waypoints_count": len(smoothed),
        "waypoints": [[round(float(v), 4) for v in pt] for pt in smoothed],
    }



class PlanTrajectoryRequest(BaseModel):
    robot_id: str = "default_6dof_arm"
    waypoints: List[List[float]] = Field(..., description="List of joint waypoints [q1..qN] in radians")
    interpolation: str = Field(default="quintic", description="quintic, cubic, trapezoidal")
    v_max: float = Field(default=2.5, description="Maximum joint velocity [rad/s]")
    a_max: float = Field(default=5.0, description="Maximum joint acceleration [rad/s^2]")
    sample_dt: float = Field(default=0.02, description="Sampling time interval [s] (e.g. 0.02 for 50 Hz preview)")


class ExecuteTrajectoryRequest(BaseModel):
    robot_id: str = "default_6dof_arm"
    waypoints: List[List[float]] = Field(..., description="List of joint waypoints [q1..qN] in radians")
    interpolation: str = Field(default="quintic", description="quintic, cubic, trapezoidal")
    v_max: float = Field(default=2.5, description="Maximum joint velocity [rad/s]")
    a_max: float = Field(default=5.0, description="Maximum joint acceleration [rad/s^2]")


class StepResponseRequest(BaseModel):
    joint_index: int = Field(default=1, ge=0, le=5, description="Joint index (0-based)")
    step_amplitude_rad: float = Field(default=0.35, description="Step change amplitude in radians (~20 deg)")
    test_duration: float = Field(default=2.0, ge=0.5, le=10.0, description="Duration of test in seconds")
    kp: float = Field(default=250.0, gt=0.0)
    ki: float = Field(default=2.0, ge=0.0)
    kd: float = Field(default=25.0, ge=0.0)


@router.post("/plan")
async def plan_trajectory(req: PlanTrajectoryRequest):
    """Generates continuous time-parameterized trajectory respecting physical limits."""
    if len(req.waypoints) < 2:
        raise HTTPException(status_code=400, detail="Planning requires at least 2 waypoints.")

    interp_map = {
        "quintic": InterpolationType.QUINTIC,
        "cubic": InterpolationType.CUBIC,
        "trapezoidal": InterpolationType.TRAPEZOIDAL,
    }
    interp_type = interp_map.get(req.interpolation.lower(), InterpolationType.QUINTIC)

    try:
        robot = create_sample_6dof_arm()
        chain = KinematicChain(robot)
        traj = JointTrajectory(
            waypoints=req.waypoints,
            interpolation=interp_type,
            v_max=req.v_max,
            a_max=req.a_max,
            chain=chain,
        )
        samples = traj.sample_all(dt=req.sample_dt)
    except Exception as e:
        logger.error(f"Trajectory planning error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "total_duration": traj.total_duration,
        "num_segments": traj.num_segments,
        "num_samples": len(samples),
        "interpolation": interp_type.value,
        "samples": [s.to_dict() for s in samples],
    }


@router.post("/execute")
async def execute_trajectory(req: ExecuteTrajectoryRequest):
    """Executes a planned trajectory in live MuJoCo simulation with closed-loop PID control."""
    if live_engine.model is None:
        raise HTTPException(status_code=400, detail="MuJoCo simulation model is not loaded.")

    interp_map = {
        "quintic": InterpolationType.QUINTIC,
        "cubic": InterpolationType.CUBIC,
        "trapezoidal": InterpolationType.TRAPEZOIDAL,
    }
    interp_type = interp_map.get(req.interpolation.lower(), InterpolationType.QUINTIC)

    try:
        robot = create_sample_6dof_arm()
        chain = KinematicChain(robot)
        traj = JointTrajectory(
            waypoints=req.waypoints,
            interpolation=interp_type,
            v_max=req.v_max,
            a_max=req.a_max,
            chain=chain,
        )
        controller = RobotMotionController(live_engine, dof=chain.dof)
        perf_data = controller.execute_trajectory(traj)
    except Exception as e:
        logger.error(f"Execution error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    return perf_data


@router.post("/step_response")
async def run_step_response_test(req: StepResponseRequest):
    """Executes closed-loop step response test in MuJoCo and returns classical control metrics."""
    if live_engine.model is None:
        raise HTTPException(status_code=400, detail="MuJoCo simulation model is not loaded.")

    try:
        results = evaluate_step_response(
            sim=live_engine,
            joint_idx=req.joint_index,
            step_amplitude=req.step_amplitude_rad,
            test_duration=req.test_duration,
            kp=req.kp,
            ki=req.ki,
            kd=req.kd,
        )
    except Exception as e:
        logger.error(f"Step response evaluation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    return results


@router.get("/presets")
async def get_trajectory_presets():
    """Provides standard multi-point industrial trajectories for testing."""
    return {
        "trajectories": [
            {
                "name": "Pick & Place Workcell Cycle",
                "description": "Standard 4-waypoint industrial pick and place sweep",
                "waypoints": [
                    [0.0, -0.785, 1.57, 0.0, 0.785, 0.0],
                    [0.5, -0.4, 1.2, 0.0, 0.6, 0.2],
                    [0.5, 0.1, 0.9, 0.0, 0.3, 0.2],
                    [-0.5, -0.2, 1.3, 0.0, 0.7, -0.2],
                    [0.0, -0.785, 1.57, 0.0, 0.785, 0.0],
                ],
            },
            {
                "name": "Multi-Axis Calibration Sweep",
                "description": "Sequentially exercises each joint through operational range",
                "waypoints": [
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.785, -0.5, 0.5, -0.5, 0.5, 0.5],
                    [-0.785, 0.5, -0.5, 0.5, -0.5, -0.5],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                ],
            },
        ]
    }
