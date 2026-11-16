"""
MonkeyBots Validation Package
Exposes core validation standards, capability benchmarks, test suite orchestrator,
and repeatable simulation experiment management.
"""

from .standards import (
    ValidationStatus,
    ValidationMetric,
    ValidationTestCase,
    ValidationSuiteReport,
)
from .capabilities import (
    validate_robot_model_integrity,
    validate_joint_limits,
    validate_kinematics,
    validate_physics_engine,
    validate_trajectory_planning,
    validate_collision_and_contact,
    validate_numerical_stability,
    validate_repeatability_and_determinism,
    validate_controller_performance,
    validate_numerical_error_analysis,
)
from .suite import (
    ValidationLaboratory,
    CAPABILITY_RUNNERS,
    CAPABILITY_ALIASES,
)
from .experiments import (
    ExperimentConfig,
    ExperimentMetrics,
    ExperimentResult,
    ExperimentComparison,
    ExperimentManager,
)

__all__ = [
    "ValidationStatus",
    "ValidationMetric",
    "ValidationTestCase",
    "ValidationSuiteReport",
    "ValidationLaboratory",
    "CAPABILITY_RUNNERS",
    "CAPABILITY_ALIASES",
    "validate_robot_model_integrity",
    "validate_joint_limits",
    "validate_kinematics",
    "validate_physics_engine",
    "validate_trajectory_planning",
    "validate_collision_and_contact",
    "validate_numerical_stability",
    "validate_repeatability_and_determinism",
    "validate_controller_performance",
    "validate_numerical_error_analysis",
    "ExperimentConfig",
    "ExperimentMetrics",
    "ExperimentResult",
    "ExperimentComparison",
    "ExperimentManager",
]
