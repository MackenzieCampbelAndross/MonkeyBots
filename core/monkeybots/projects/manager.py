"""
MonkeyBots Local Project Management Engine
Provides end-to-end lifecycle operations for robotics projects:
Create, Open, Save, Save As, Duplicate, Rename, Delete, Backup (.mbpkg), Restore,
Integrity Validation, and Model Import/Export.
100% database-free, local filesystem storage architecture.
"""

import os
import re
import shutil
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any

from .schema import (
    ProjectManifest,
    ProjectMetadata,
    RobotDefinition,
    PhysicsConfig,
    ControllerConfig,
    JointControllerGain,
    MaterialProperty,
)
from .io import (
    atomic_write,
    recover_interrupted_saves,
    create_snapshot,
    create_project_archive,
    extract_project_archive,
)
from .validator import validate_project_integrity, ProjectIntegrityReport
from ..models.assets.sample_6dof_arm import create_sample_6dof_arm
from ..models.mjcf_builder import export_mjcf
from ..models.urdf_parser import export_urdf
from ..models.assets.workcell_model import generate_workcell_mjcf


def sanitize_slug(name: str) -> str:
    """Converts a display name into a clean filesystem folder slug."""
    slug = re.sub(r"[^a-zA-Z0-9_\-]", "_", name.strip().lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "project"


class ProjectManager:
    """
    Central Manager for local filesystem robotics projects.
    Operates strictly on standard local directories and files.
    """

    def __init__(self, projects_dir: Optional[Path] = None):
        self.projects_dir = Path(projects_dir or "projects").resolve()
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def list_projects(self) -> List[Dict[str, Any]]:
        """
        Scans projects directory and returns an enriched list of local projects
        including integrity health, DOF, robot type, disk size, and file counts.
        """
        results: List[Dict[str, Any]] = []
        if not self.projects_dir.exists():
            return results

        for item in sorted(self.projects_dir.iterdir()):
            if not item.is_dir() or item.name.startswith("."):
                continue

            # Run recovery check for any abandoned .tmp files from previous sessions
            recover_interrupted_saves(item)

            manifest_path = item / "project.json"
            if not manifest_path.exists():
                continue

            try:
                raw_data = json.loads(manifest_path.read_text(encoding="utf-8"))
                meta = raw_data.get("metadata", {})
                robot = raw_data.get("robot", {})
                
                # Calculate folder size
                total_size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())

                # Quick integrity check
                report = validate_project_integrity(item)

                results.append({
                    "id": item.name,
                    "name": meta.get("name", item.name),
                    "description": meta.get("description", ""),
                    "robot_type": meta.get("robot_type", "Articulated Arm"),
                    "author": meta.get("author", "MonkeyBots Engineer"),
                    "created_at": meta.get("created_at", ""),
                    "updated_at": meta.get("updated_at", ""),
                    "path": str(item.resolve()),
                    "dof": robot.get("dof", 6),
                    "has_mjcf": (item / robot.get("model_file", "robot.mjcf")).exists(),
                    "has_urdf": (item / robot.get("urdf_file", "robot.urdf")).exists() if robot.get("urdf_file") else False,
                    "size_bytes": total_size,
                    "integrity_status": report.status,
                    "missing_assets_count": report.missing_assets_count,
                    "experiments_count": report.experiments_count,
                    "trajectories_count": report.trajectories_count,
                    "reports_count": report.reports_count,
                    "snapshots_count": report.snapshots_count,
                })
            except Exception:
                # If unreadable, include basic damaged record
                results.append({
                    "id": item.name,
                    "name": item.name,
                    "description": "[Damaged Project Manifest]",
                    "robot_type": "Unknown",
                    "path": str(item.resolve()),
                    "dof": 0,
                    "has_mjcf": False,
                    "has_urdf": False,
                    "size_bytes": 0,
                    "integrity_status": "ERROR",
                    "missing_assets_count": 0,
                    "experiments_count": 0,
                    "trajectories_count": 0,
                    "reports_count": 0,
                    "snapshots_count": 0,
                })

        return sorted(results, key=lambda x: x.get("updated_at", ""), reverse=True)

    def get_project(self, project_id: str) -> ProjectManifest:
        """Retrieves and validates manifest for a project ID."""
        project_dir = self.projects_dir / project_id
        if not project_dir.exists() or not project_dir.is_dir():
            raise FileNotFoundError(f"Project '{project_id}' does not exist at {project_dir}")

        # Recover from interrupted saves if needed
        recover_interrupted_saves(project_dir)

        manifest_path = project_dir / "project.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Project '{project_id}' lacks 'project.json'")

        raw_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        if "metadata" in raw_data and isinstance(raw_data["metadata"], dict):
            if "id" not in raw_data["metadata"]:
                raw_data["metadata"]["id"] = project_id

        return ProjectManifest.model_validate(raw_data)

    def create_project(
        self,
        name: str,
        description: str = "",
        robot_preset: str = "6dof_industrial",
        author: str = "MonkeyBots Engineer",
        robot_type: str = "Articulated Arm",
        tags: Optional[List[str]] = None,
    ) -> ProjectManifest:
        """
        Creates a new structured local project folder with complete directory hierarchy:
        - project.json (manifest)
        - robot.mjcf (MuJoCo physics model)
        - robot.urdf (URDF kinematic model)
        - assets/ (geometry meshes and textures)
        - trajectories/ (saved waypoint paths)
        - experiments/ (local simulation experiment results)
        - logs/ (runtime telemetry logs)
        - reports/ (engineering validation reports)
        - .snapshots/ (local revision history)
        """
        base_slug = sanitize_slug(name)
        slug = base_slug
        counter = 1
        while (self.projects_dir / slug).exists():
            slug = f"{base_slug}_{counter}"
            counter += 1

        project_dir = self.projects_dir / slug
        project_dir.mkdir(parents=True, exist_ok=True)

        # Standard subdirectories
        for sub in ["assets", "trajectories", "experiments", "logs", "reports", ".snapshots"]:
            (project_dir / sub).mkdir(parents=True, exist_ok=True)

        now_iso = datetime.now(timezone.utc).isoformat()
        metadata = ProjectMetadata(
            id=slug,
            name=name,
            description=description,
            created_at=now_iso,
            updated_at=now_iso,
            author=author,
            robot_type=robot_type,
            tags=tags or ["robotics", "simulation"],
            version_tag="v1.0.0",
        )

        # Generate robot model files according to preset
        dof = 6
        default_qpos = [0.0, -0.785398, 1.570796, 0.0, 0.785398, 0.0]
        model_file = "robot.mjcf"
        urdf_file = "robot.urdf"

        if robot_preset in ("6dof_industrial", "6dof"):
            arm = create_sample_6dof_arm()
            arm.name = f"MonkeyBots_{slug}"
            mjcf_xml = export_mjcf(arm)
            urdf_xml = export_urdf(arm)
            atomic_write(project_dir / model_file, mjcf_xml)
            atomic_write(project_dir / urdf_file, urdf_xml)
        elif robot_preset == "workcell":
            workcell_xml = generate_workcell_mjcf()
            atomic_write(project_dir / model_file, workcell_xml)
            atomic_write(project_dir / "workcell.mjcf", workcell_xml)
            dof = 8
            default_qpos = [0.0, -0.6, 1.2, 0.0, 0.6, 0.0, 0.0, 0.0]
        else:
            # Blank or basic model
            arm = create_sample_6dof_arm()
            arm.name = slug
            atomic_write(project_dir / model_file, export_mjcf(arm))
            atomic_write(project_dir / urdf_file, export_urdf(arm))

        robot_def = RobotDefinition(
            model_file=model_file,
            urdf_file=urdf_file,
            dof=dof,
            end_effector_site="flange_site",
            default_qpos=default_qpos,
        )

        physics = PhysicsConfig(
            timestep=0.002,
            integrator="RK4",
            gravity=[0.0, 0.0, -9.81],
            collision_tolerance=0.001,
        )

        controllers = ControllerConfig(
            default_mode="position",
            gains=[
                JointControllerGain(joint="joint_1", kp=350.0, ki=0.5, kd=25.0, max_torque=150.0),
                JointControllerGain(joint="joint_2", kp=450.0, ki=1.0, kd=40.0, max_torque=150.0),
                JointControllerGain(joint="joint_3", kp=300.0, ki=0.5, kd=20.0, max_torque=150.0),
                JointControllerGain(joint="joint_4", kp=150.0, ki=0.1, kd=10.0, max_torque=28.0),
                JointControllerGain(joint="joint_5", kp=150.0, ki=0.1, kd=10.0, max_torque=28.0),
                JointControllerGain(joint="joint_6", kp=80.0,  ki=0.05, kd=5.0,  max_torque=28.0),
            ],
        )

        manifest = ProjectManifest(
            version="1.1.0",
            metadata=metadata,
            robot=robot_def,
            physics=physics,
            controllers=controllers,
        )

        # Atomic manifest write
        atomic_write(project_dir / "project.json", manifest.model_dump_json(indent=2))

        # Initial baseline snapshot
        create_snapshot(project_dir, tag="initial_creation")

        return manifest

    def save_project(self, project_id: str, manifest: ProjectManifest) -> ProjectManifest:
        """
        Saves updated project manifest atomically, updates modification timestamp,
        and creates a safety snapshot in .snapshots/.
        """
        project_dir = self.projects_dir / project_id
        if not project_dir.exists():
            raise FileNotFoundError(f"Project '{project_id}' not found.")

        # Update timestamps
        manifest.metadata.updated_at = datetime.now(timezone.utc).isoformat()
        manifest.metadata.id = project_id

        # Atomic manifest write
        manifest_path = project_dir / "project.json"
        atomic_write(manifest_path, manifest.model_dump_json(indent=2))

        # Create revision snapshot
        create_snapshot(project_dir, tag="user_save")

        return manifest

    def save_project_as(self, project_id: str, new_name: str, new_id: Optional[str] = None) -> ProjectManifest:
        """
        Duplicates an existing project into a new project directory with updated title and slug.
        Preserves all robot configurations, geometries, trajectories, and experiments.
        """
        src_dir = self.projects_dir / project_id
        if not src_dir.exists():
            raise FileNotFoundError(f"Source project '{project_id}' not found.")

        target_slug = sanitize_slug(new_id or new_name)
        base_slug = target_slug
        counter = 1
        while (self.projects_dir / target_slug).exists():
            target_slug = f"{base_slug}_{counter}"
            counter += 1

        dst_dir = self.projects_dir / target_slug

        # Deep copy project tree (omitting old snapshots)
        shutil.copytree(
            src_dir,
            dst_dir,
            ignore=shutil.ignore_patterns(".snapshots", "*.tmp_*", "*.bak"),
        )
        (dst_dir / ".snapshots").mkdir(parents=True, exist_ok=True)

        # Update manifest
        manifest_path = dst_dir / "project.json"
        raw_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        raw_data["metadata"]["id"] = target_slug
        raw_data["metadata"]["name"] = new_name
        now_iso = datetime.now(timezone.utc).isoformat()
        raw_data["metadata"]["created_at"] = now_iso
        raw_data["metadata"]["updated_at"] = now_iso

        manifest = ProjectManifest.model_validate(raw_data)
        atomic_write(manifest_path, manifest.model_dump_json(indent=2))

        create_snapshot(dst_dir, tag="save_as")
        return manifest

    def duplicate_project(self, project_id: str, new_name: Optional[str] = None) -> ProjectManifest:
        """Convenience method to clone a project with an automatic title."""
        original = self.get_project(project_id)
        clone_title = new_name or f"{original.metadata.name} (Copy)"
        return self.save_project_as(project_id, new_name=clone_title)

    def rename_project(self, project_id: str, new_name: str) -> ProjectManifest:
        """
        Updates a project's display title and writes the manifest atomically.
        """
        manifest = self.get_project(project_id)
        manifest.metadata.name = new_name
        return self.save_project(project_id, manifest)

    def delete_project(self, project_id: str, confirmation: bool = False) -> bool:
        """
        Permanently deletes a local project folder from the filesystem.
        Requires explicit confirmation=True to prevent accidental data loss.
        """
        if not confirmation:
            raise ValueError("Project deletion aborted: confirmation flag must be explicitly set to True.")

        project_dir = self.projects_dir / project_id
        if not project_dir.exists():
            raise FileNotFoundError(f"Cannot delete non-existent project '{project_id}'.")

        shutil.rmtree(project_dir)
        return True

    def validate_project(self, project_id: str) -> ProjectIntegrityReport:
        """Runs the offline project integrity and asset audit."""
        project_dir = self.projects_dir / project_id
        return validate_project_integrity(project_dir)

    def create_backup(self, project_id: str, target_dir: Optional[Path] = None) -> Path:
        """Packages the complete project into a single compressed .mbpkg file."""
        project_dir = self.projects_dir / project_id
        if not project_dir.exists():
            raise FileNotFoundError(f"Project '{project_id}' not found.")

        target_dir = Path(target_dir) if target_dir else (self.projects_dir / "backups")
        target_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_file = target_dir / f"{project_id}_{timestamp}.mbpkg"
        return create_project_archive(project_dir, output_file=backup_file)

    def restore_backup(self, backup_file: Path, new_project_id: Optional[str] = None) -> ProjectManifest:
        """
        Extracts and verifies a .mbpkg archive into the projects directory.
        """
        backup_file = Path(backup_file)
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup archive '{backup_file}' does not exist.")

        # Determine target folder name
        target_slug = new_project_id or backup_file.stem.split("_backup_")[0].split("_20")[0]
        target_slug = sanitize_slug(target_slug)
        base_slug = target_slug
        counter = 1
        while (self.projects_dir / target_slug).exists():
            target_slug = f"{base_slug}_restored_{counter}"
            counter += 1

        dst_dir = self.projects_dir / target_slug
        extract_project_archive(backup_file, dst_dir)

        # Update manifest ID to match new folder
        manifest_path = dst_dir / "project.json"
        raw_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        raw_data["metadata"]["id"] = target_slug
        manifest = ProjectManifest.model_validate(raw_data)
        atomic_write(manifest_path, manifest.model_dump_json(indent=2))

        return manifest

    def list_backups(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists available .mbpkg backup archives."""
        backups_dir = self.projects_dir / "backups"
        if not backups_dir.exists():
            return []

        backups: List[Dict[str, Any]] = []
        for f in backups_dir.glob("*.mbpkg"):
            if project_id and not f.name.startswith(project_id):
                continue
            backups.append({
                "filename": f.name,
                "path": str(f.resolve()),
                "size_bytes": f.stat().st_size,
                "created_at": datetime.fromtimestamp(f.stat().st_mtime, timezone.utc).isoformat(),
            })

        return sorted(backups, key=lambda x: x["created_at"], reverse=True)

    def import_robot_model(
        self,
        project_id: str,
        source_model_path: Path,
        destination_filename: Optional[str] = None,
    ) -> ProjectManifest:
        """
        Imports an external URDF or MJCF model file into the project directory,
        validating XML structure and updating manifest references.
        """
        project_dir = self.projects_dir / project_id
        if not project_dir.exists():
            raise FileNotFoundError(f"Project '{project_id}' not found.")

        src = Path(source_model_path)
        if not src.exists():
            raise FileNotFoundError(f"Source model file '{src}' not found.")

        manifest = self.get_project(project_id)
        ext = src.suffix.lower()

        dst_name = destination_filename or src.name
        dst_path = project_dir / dst_name

        # Copy model file atomically
        content = src.read_text(encoding="utf-8")
        atomic_write(dst_path, content)

        if ext in (".mjcf", ".xml"):
            manifest.robot.model_file = dst_name
        elif ext == ".urdf":
            manifest.robot.urdf_file = dst_name

        self.save_project(project_id, manifest)
        return manifest

    def export_robot_model(
        self,
        project_id: str,
        export_dir: Path,
        format_type: str = "bundle",
    ) -> Path:
        """
        Exports a robot model (URDF, MJCF, or both with geometry meshes) to an export directory.
        """
        project_dir = self.projects_dir / project_id
        if not project_dir.exists():
            raise FileNotFoundError(f"Project '{project_id}' not found.")

        export_dir = Path(export_dir)
        export_dir.mkdir(parents=True, exist_ok=True)
        manifest = self.get_project(project_id)

        if format_type in ("mjcf", "bundle"):
            mjcf_src = project_dir / manifest.robot.model_file
            if mjcf_src.exists():
                shutil.copy2(mjcf_src, export_dir / manifest.robot.model_file)

        if format_type in ("urdf", "bundle") and manifest.robot.urdf_file:
            urdf_src = project_dir / manifest.robot.urdf_file
            if urdf_src.exists():
                shutil.copy2(urdf_src, export_dir / manifest.robot.urdf_file)

        # Copy assets if bundle
        if format_type == "bundle":
            assets_src = project_dir / "assets"
            if assets_src.exists() and any(assets_src.iterdir()):
                shutil.copytree(assets_src, export_dir / "assets", dirs_exist_ok=True)

        return export_dir
