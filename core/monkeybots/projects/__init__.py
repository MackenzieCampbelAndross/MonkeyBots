"""
MonkeyBots Projects Package
Local-first, database-independent project management, manifest persistence,
atomic I/O, integrity validation, and backup services.
"""

from .schema import (
    ProjectManifest,
    ProjectMetadata,
    RobotDefinition,
    PhysicsConfig,
    ControllerConfig,
    JointControllerGain,
    MaterialProperty,
    GeometryAssetReference,
    TrajectoryMetadata,
)
from .io import (
    atomic_write,
    recover_interrupted_saves,
    create_snapshot,
    create_project_archive,
    extract_project_archive,
)
from .validator import (
    validate_project_integrity,
    ProjectIntegrityReport,
    AssetVerificationResult,
)
from .manager import (
    ProjectManager,
    sanitize_slug,
)

__all__ = [
    "ProjectManifest",
    "ProjectMetadata",
    "RobotDefinition",
    "PhysicsConfig",
    "ControllerConfig",
    "JointControllerGain",
    "MaterialProperty",
    "GeometryAssetReference",
    "TrajectoryMetadata",
    "atomic_write",
    "recover_interrupted_saves",
    "create_snapshot",
    "create_project_archive",
    "extract_project_archive",
    "validate_project_integrity",
    "ProjectIntegrityReport",
    "AssetVerificationResult",
    "ProjectManager",
    "sanitize_slug",
]
