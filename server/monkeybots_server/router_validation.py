"""
MonkeyBots Engineering Validation & Benchmarking REST API Router.

Endpoints for running the 10 core capability benchmarks, executing the full suite,
exporting formal markdown reports, and running/persisting/comparing repeatable simulation experiments.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from core.monkeybots.validation import (
    ValidationStatus,
    ValidationMetric,
    ValidationTestCase,
    ValidationSuiteReport,
    ValidationLaboratory,
    CAPABILITY_RUNNERS,
    CAPABILITY_ALIASES,
    ExperimentConfig,
    ExperimentResult,
    ExperimentComparison,
    ExperimentManager,
)
from .utils.logger import get_logger

router = APIRouter(prefix="/api/v1/validation", tags=["Validation & Benchmarking"])
logger = get_logger("router_validation")

# Global laboratory instance and experiment manager
laboratory = ValidationLaboratory()
experiment_manager = ExperimentManager()


class CompareExperimentsRequest(BaseModel):
    experiment_ids: List[str] = Field(..., min_length=1, description="List of saved experiment IDs to compare")


@router.get("/suite", response_model=ValidationSuiteReport)
async def run_full_validation_suite():
    """
    Executes all 10 core engineering validation benchmarks across model integrity,
    joint limits, kinematics, physics, trajectories, contacts, stability, repeatability,
    controllers, and numerical error analysis.
    """
    try:
        logger.info("Executing comprehensive engineering validation suite...")
        report = laboratory.run_suite()
        logger.info(
            f"Validation suite complete. Status: {report.overall_status}, Compliance: {report.compliance_percentage}%"
        )
        return report
    except Exception as e:
        logger.error(f"Validation suite failed: {e}")
        raise HTTPException(status_code=500, detail=f"Suite execution error: {str(e)}")


@router.get("/capabilities")
async def list_capabilities():
    """Returns metadata for all 10 supported engineering validation capabilities."""
    caps = [
        {
            "id": "VAL_CAP_01",
            "name": "Robot Model Structural & Mass Integrity",
            "category": "Model Integrity",
            "standard": "Classical Rigid-Body Mechanics / ISO 9283",
            "alias": "model",
        },
        {
            "id": "VAL_CAP_02",
            "name": "Joint Limits Enforcement & Bound Clamping",
            "category": "Kinematic Limits",
            "standard": "ISO 10218-1 Safety Requirements for Industrial Robots",
            "alias": "joint_limits",
        },
        {
            "id": "VAL_CAP_03",
            "name": "Kinematics Precision & Closed-Loop Convergence",
            "category": "Kinematics",
            "standard": "Denavit-Hartenberg / Lie Algebra / DLS Inversion",
            "alias": "kinematics",
        },
        {
            "id": "VAL_CAP_04",
            "name": "Physics Dynamics & Energy Conservation Laws",
            "category": "Physics Dynamics",
            "standard": "Galilean Mechanics & Hamiltonian Invariant Preservation",
            "alias": "physics",
        },
        {
            "id": "VAL_CAP_05",
            "name": "Polynomial Trajectory Continuity & Bounds",
            "category": "Motion Planning",
            "standard": "ISO 9283 Trajectory Accuracy & C2 Continuity",
            "alias": "trajectory",
        },
        {
            "id": "VAL_CAP_06",
            "name": "Contact Physics & Coulomb Friction Cone Integrity",
            "category": "Contact Physics",
            "standard": "Signorini Non-Penetration & Coulomb Friction Cones",
            "alias": "collision",
        },
        {
            "id": "VAL_CAP_07",
            "name": "Numerical Stability & Finite Energy Boundedness",
            "category": "Numerical Stability",
            "standard": "Lyapunov Stability Criterion & IEEE 754 Arithmetic",
            "alias": "stability",
        },
        {
            "id": "VAL_CAP_08",
            "name": "Bit-Level Repeatability & Simulation Determinism",
            "category": "Determinism",
            "standard": "ISO 9283 Multi-Cycle Determinism & Numerical Reproducibility",
            "alias": "repeatability",
        },
        {
            "id": "VAL_CAP_09",
            "name": "Controller Step Response & Stability Margins",
            "category": "Control Systems",
            "standard": "ANSI/ISA Control Performance & Second-Order Step Response Criteria",
            "alias": "controller",
        },
        {
            "id": "VAL_CAP_10",
            "name": "Numerical Error, Solver Residuals & Timestep Convergence",
            "category": "Numerical Analysis",
            "standard": "Euler-Richardson Extrapolation & KKT Constraint Solvers",
            "alias": "numerical_error",
        },
    ]
    return {"capabilities": caps}


@router.get("/capability/{capability_id}", response_model=ValidationTestCase)
async def run_single_capability(capability_id: str):
    """Executes a single validation capability benchmark by ID (e.g. 'VAL_CAP_01') or alias."""
    try:
        test_case = laboratory.run_capability(capability_id)
        return test_case
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Error running capability '{capability_id}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/markdown", response_class=PlainTextResponse)
async def get_validation_markdown_report():
    """Generates and returns an authoritative engineering Markdown validation report."""
    try:
        report_text = laboratory.generate_markdown_report()
        return PlainTextResponse(content=report_text, media_type="text/markdown")
    except Exception as e:
        logger.error(f"Failed to generate Markdown report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiments")
async def list_saved_experiments():
    """Lists all locally persisted repeatable simulation experiments."""
    try:
        return {"experiments": experiment_manager.list_experiments()}
    except Exception as e:
        logger.error(f"Failed to list experiments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/experiments/run", response_model=ExperimentResult)
async def run_repeatable_experiment(config: ExperimentConfig):
    """
    Executes a configured simulation experiment with live MuJoCo physics,
    evaluates tracking, torque and energy metrics, downsamples trajectories, and saves locally to JSON.
    """
    try:
        logger.info(f"Executing repeatable experiment '{config.name}' (ID: {config.id})...")
        result = experiment_manager.run_experiment(config)
        logger.info(
            f"Experiment complete. RMSE: {result.metrics.position_rmse_rad*1000:.2f} mrad, RTF: {result.metrics.real_time_factor}x"
        )
        return result
    except Exception as e:
        logger.error(f"Experiment execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Experiment failed: {str(e)}")


@router.get("/experiments/{experiment_id}", response_model=ExperimentResult)
async def get_experiment_details(experiment_id: str):
    """Retrieves full experiment configuration, metrics, and recorded time-series."""
    result = experiment_manager.load_experiment(experiment_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found.")
    return result


@router.post("/experiments/compare", response_model=ExperimentComparison)
async def compare_experiments(req: CompareExperimentsRequest):
    """Compares multiple saved experiments and calculates metric deltas and improvement percentages."""
    try:
        return experiment_manager.compare_experiments(req.experiment_ids)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Comparison error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
