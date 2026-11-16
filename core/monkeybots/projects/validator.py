"""
MonkeyBots Project Integrity & Asset Validator
Analyzes local project directories for structural consistency, missing assets,
valid relative paths, XML model health, and data corruption without external services.
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

from .schema import ProjectManifest


class AssetVerificationResult(BaseModel):
    name: str
    relative_path: str
    exists: bool
    size_bytes: int = 0
    format: str = "stl"
    status: str = "VALID"  # "VALID", "MISSING", "CORRUPT", "ABSOLUTE_PATH_FORBIDDEN"


class ProjectIntegrityReport(BaseModel):
    project_id: str
    is_valid: bool
    status: str = "HEALTHY"  # "HEALTHY", "WARNING", "ERROR"
    manifest_valid: bool
    model_mjcf_valid: bool
    model_urdf_valid: bool
    total_assets: int = 0
    missing_assets_count: int = 0
    assets: List[AssetVerificationResult] = Field(default_factory=list)
    experiments_count: int = 0
    trajectories_count: int = 0
    reports_count: int = 0
    snapshots_count: int = 0
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    file_inventory: Dict[str, int] = Field(default_factory=dict)


def validate_project_integrity(project_dir: Path) -> ProjectIntegrityReport:
    """
    Performs comprehensive offline audit of a project directory.
    Validates manifest schema, model XML syntax, relative asset paths,
    detects orphaned or missing assets, and tallies experiment records.
    """
    project_dir = Path(project_dir)
    report = ProjectIntegrityReport(
        project_id=project_dir.name,
        is_valid=True,
        status="HEALTHY",
        manifest_valid=False,
        model_mjcf_valid=False,
        model_urdf_valid=False,
    )

    if not project_dir.exists() or not project_dir.is_dir():
        report.is_valid = False
        report.status = "ERROR"
        report.errors.append(f"Project directory '{project_dir}' does not exist.")
        return report

    # 1. Manifest Validation
    manifest_path = project_dir / "project.json"
    manifest: Optional[ProjectManifest] = None
    if not manifest_path.exists():
        report.is_valid = False
        report.manifest_valid = False
        report.status = "ERROR"
        report.errors.append("Missing primary project manifest ('project.json').")
        return report

    try:
        raw_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        # Fill in metadata.id if omitted
        if "metadata" in raw_data and isinstance(raw_data["metadata"], dict):
            if "id" not in raw_data["metadata"]:
                raw_data["metadata"]["id"] = project_dir.name
        manifest = ProjectManifest.model_validate(raw_data)
        report.manifest_valid = True
    except Exception as e:
        report.is_valid = False
        report.manifest_valid = False
        report.status = "ERROR"
        report.errors.append(f"Corrupt or non-conforming project.json: {e}")
        return report

    # 2. Primary Model (MJCF) Validation
    mjcf_path = project_dir / manifest.robot.model_file
    if mjcf_path.exists():
        try:
            tree = ET.parse(mjcf_path)
            root = tree.getroot()
            if root.tag != "mujoco":
                report.warnings.append(f"Root XML tag in '{manifest.robot.model_file}' is '{root.tag}', expected 'mujoco'.")
            report.model_mjcf_valid = True
        except ET.ParseError as pe:
            report.is_valid = False
            report.status = "ERROR"
            report.errors.append(f"Invalid MJCF XML in '{manifest.robot.model_file}': {pe}")
    else:
        report.warnings.append(f"Referenced MJCF file '{manifest.robot.model_file}' not found.")

    # 3. Secondary Model (URDF) Validation
    if manifest.robot.urdf_file:
        urdf_path = project_dir / manifest.robot.urdf_file
        if urdf_path.exists():
            try:
                tree = ET.parse(urdf_path)
                root = tree.getroot()
                if root.tag != "robot":
                    report.warnings.append(f"Root tag in '{manifest.robot.urdf_file}' is '{root.tag}', expected 'robot'.")
                report.model_urdf_valid = True
            except ET.ParseError as pe:
                report.warnings.append(f"Invalid URDF XML in '{manifest.robot.urdf_file}': {pe}")
        else:
            report.warnings.append(f"Referenced URDF file '{manifest.robot.urdf_file}' not found.")

    # 4. Relative Asset Verification & Missing Asset Detection
    # Scan manifest declared assets
    checked_paths = set()
    for asset in manifest.assets:
        rel = asset.relative_path
        checked_paths.add(rel)
        # Check for forbidden absolute paths
        if Path(rel).is_absolute() or rel.startswith(("/", "\\")):
            report.status = "WARNING"
            report.warnings.append(f"Asset '{asset.name}' uses absolute path: '{rel}'. Must be relative.")
            report.assets.append(
                AssetVerificationResult(
                    name=asset.name,
                    relative_path=rel,
                    exists=False,
                    format=asset.format,
                    status="ABSOLUTE_PATH_FORBIDDEN",
                )
            )
            report.missing_assets_count += 1
            continue

        disk_path = project_dir / rel
        if disk_path.exists():
            report.assets.append(
                AssetVerificationResult(
                    name=asset.name,
                    relative_path=rel,
                    exists=True,
                    size_bytes=disk_path.stat().st_size,
                    format=asset.format,
                    status="VALID",
                )
            )
        else:
            report.status = "WARNING"
            report.missing_assets_count += 1
            report.warnings.append(f"Missing referenced asset: '{rel}'")
            report.assets.append(
                AssetVerificationResult(
                    name=asset.name,
                    relative_path=rel,
                    exists=False,
                    format=asset.format,
                    status="MISSING",
                )
            )

    # Also discover any unreferenced assets physically in assets/
    assets_dir = project_dir / "assets"
    if assets_dir.exists():
        for asset_file in assets_dir.rglob("*"):
            if asset_file.is_file():
                rel = str(asset_file.relative_to(project_dir)).replace("\\", "/")
                if rel not in checked_paths:
                    report.assets.append(
                        AssetVerificationResult(
                            name=asset_file.stem,
                            relative_path=rel,
                            exists=True,
                            size_bytes=asset_file.stat().st_size,
                            format=asset_file.suffix.lstrip(".").lower() or "bin",
                            status="VALID",
                        )
                    )

    report.total_assets = len(report.assets)

    # 5. Inventory Subdirectories
    exp_dir = project_dir / "experiments"
    if exp_dir.exists():
        report.experiments_count = len(list(exp_dir.glob("*.json")))

    traj_dir = project_dir / "trajectories"
    if traj_dir.exists():
        report.trajectories_count = len(list(traj_dir.glob("*.json")))

    rep_dir = project_dir / "reports"
    if rep_dir.exists():
        report.reports_count = len(list(rep_dir.glob("*.md")) + list(rep_dir.glob("*.json")))

    snap_dir = project_dir / ".snapshots"
    if snap_dir.exists():
        report.snapshots_count = len([s for s in snap_dir.iterdir() if s.is_dir()])

    # Inventory summary
    report.file_inventory = {
        "experiments": report.experiments_count,
        "trajectories": report.trajectories_count,
        "reports": report.reports_count,
        "assets": report.total_assets,
        "snapshots": report.snapshots_count,
    }

    if report.errors:
        report.is_valid = False
        report.status = "ERROR"
    elif report.warnings or report.missing_assets_count > 0:
        report.status = "WARNING"
    else:
        report.status = "HEALTHY"

    return report
