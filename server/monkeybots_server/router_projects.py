"""
Local Projects Management REST API Router
Complete local-first project management system without databases:
Create, Open, Save, Save As, Duplicate, Rename, Delete, Backup (.mbpkg), Restore,
Integrity Validation, and Robot Model Import/Export.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from core.monkeybots.config import settings
from core.monkeybots.projects import (
    ProjectManager,
    ProjectManifest,
    ProjectIntegrityReport,
)
from server.monkeybots_server.utils.logger import get_logger

router = APIRouter(prefix="/api/v1/projects", tags=["Local Projects"])
logger = get_logger("router_projects")

# Global ProjectManager instance bound to the workspace projects directory
project_manager = ProjectManager(projects_dir=settings.PROJECTS_DIR)


class ProjectSummaryItem(BaseModel):
    id: str
    name: str
    description: str
    robot_type: str = "Articulated Arm"
    author: str = "MonkeyBots Engineer"
    created_at: str = ""
    updated_at: str = ""
    path: str
    dof: int
    has_mjcf: bool
    has_urdf: bool
    size_bytes: int = 0
    integrity_status: str = "HEALTHY"
    missing_assets_count: int = 0
    experiments_count: int = 0
    trajectories_count: int = 0
    reports_count: int = 0
    snapshots_count: int = 0


class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Human readable project name")
    description: str = Field(default="", description="Project engineering description")
    robot_preset: str = Field(default="6dof_industrial", description="'6dof_industrial', 'workcell', 'blank'")
    author: str = Field(default="MonkeyBots Engineer")
    robot_type: str = Field(default="Articulated Arm")
    tags: List[str] = Field(default_factory=lambda: ["robotics", "simulation"])


class SaveAsRequest(BaseModel):
    new_name: str = Field(..., min_length=1, description="New project title")
    new_id: Optional[str] = Field(default=None, description="Optional custom directory slug")


class RenameProjectRequest(BaseModel):
    new_name: str = Field(..., min_length=1, description="Updated display title")


class ImportModelRequest(BaseModel):
    source_model_path: str = Field(..., description="Path to external URDF or MJCF file on disk")
    destination_filename: Optional[str] = Field(default=None, description="Target filename inside project directory")


class ExportModelRequest(BaseModel):
    export_dir: str = Field(..., description="Destination directory path on local disk")
    format_type: str = Field(default="bundle", description="'mjcf', 'urdf', 'bundle'")


class RestoreBackupRequest(BaseModel):
    backup_file: str = Field(..., description="Path to .mbpkg archive file")
    new_project_id: Optional[str] = Field(default=None, description="Optional project ID for restored project")


@router.get("", response_model=List[ProjectSummaryItem])
async def list_projects():
    """Returns an enriched list of all local projects with integrity status and metadata."""
    try:
        return project_manager.list_projects()
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create", response_model=ProjectManifest, status_code=status.HTTP_201_CREATED)
async def create_project(req: CreateProjectRequest):
    """Creates a new structured local project folder with complete directory hierarchy."""
    try:
        manifest = project_manager.create_project(
            name=req.name,
            description=req.description,
            robot_preset=req.robot_preset,
            author=req.author,
            robot_type=req.robot_type,
            tags=req.tags,
        )
        logger.info(f"Successfully created project '{manifest.metadata.name}' (ID: {manifest.metadata.id})")
        return manifest
    except Exception as e:
        logger.error(f"Failed to create project '{req.name}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backups")
async def list_backups(project_id: Optional[str] = None):
    """Lists available .mbpkg backup archives."""
    try:
        return {"backups": project_manager.list_backups(project_id)}
    except Exception as e:
        logger.error(f"Error listing backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore-backup", response_model=ProjectManifest)
async def restore_project_backup(req: RestoreBackupRequest):
    """Restores a project from a compressed .mbpkg archive."""
    try:
        manifest = project_manager.restore_backup(
            backup_file=Path(req.backup_file),
            new_project_id=req.new_project_id,
        )
        logger.info(f"Successfully restored project '{manifest.metadata.name}' from '{req.backup_file}'")
        return manifest
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except Exception as e:
        logger.error(f"Failed to restore backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}", response_model=ProjectManifest)
async def get_project(project_id: str):
    """Retrieves full manifest for a specific local project."""
    try:
        return project_manager.get_project(project_id)
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except Exception as e:
        logger.error(f"Error loading project '{project_id}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{project_id}", response_model=ProjectManifest)
async def save_project(project_id: str, manifest: ProjectManifest):
    """Atomically saves updated project manifest and generates revision snapshot."""
    try:
        saved = project_manager.save_project(project_id, manifest)
        logger.info(f"Atomically saved project '{project_id}'")
        return saved
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except Exception as e:
        logger.error(f"Error saving project '{project_id}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/save-as", response_model=ProjectManifest)
async def save_project_as(project_id: str, req: SaveAsRequest):
    """Duplicates an existing project into a new directory with a new title."""
    try:
        duplicated = project_manager.save_project_as(
            project_id=project_id,
            new_name=req.new_name,
            new_id=req.new_id,
        )
        logger.info(f"Cloned project '{project_id}' to '{duplicated.metadata.id}' ('{req.new_name}')")
        return duplicated
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except Exception as e:
        logger.error(f"Save-as failed for project '{project_id}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/duplicate", response_model=ProjectManifest)
async def duplicate_project(project_id: str, new_name: Optional[str] = Query(default=None)):
    """Convenience endpoint to clone a project."""
    try:
        return project_manager.duplicate_project(project_id, new_name=new_name)
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except Exception as e:
        logger.error(f"Failed to duplicate project '{project_id}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{project_id}/rename", response_model=ProjectManifest)
async def rename_project(project_id: str, req: RenameProjectRequest):
    """Renames a project title atomically."""
    try:
        return project_manager.rename_project(project_id, req.new_name)
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except Exception as e:
        logger.error(f"Rename failed for '{project_id}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}")
async def delete_project(project_id: str, confirm: bool = Query(default=False)):
    """Permanently deletes a local project folder from the filesystem."""
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Deletion requires explicit query parameter '?confirm=true' for safety.",
        )
    try:
        project_manager.delete_project(project_id, confirmation=confirm)
        logger.info(f"Deleted project '{project_id}' from disk.")
        return {"status": "DELETED", "project_id": project_id}
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except Exception as e:
        logger.error(f"Error deleting project '{project_id}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/validate", response_model=ProjectIntegrityReport)
async def validate_project(project_id: str):
    """Audits local project integrity, missing assets, and relative path conformance."""
    try:
        return project_manager.validate_project(project_id)
    except Exception as e:
        logger.error(f"Failed to validate project '{project_id}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/backup")
async def create_project_backup(project_id: str):
    """Creates a standalone .mbpkg archive of the project on local disk."""
    try:
        backup_path = project_manager.create_backup(project_id)
        logger.info(f"Created backup for '{project_id}' at '{backup_path}'")
        return {
            "status": "BACKUP_CREATED",
            "project_id": project_id,
            "filename": backup_path.name,
            "path": str(backup_path.resolve()),
            "size_bytes": backup_path.stat().st_size,
        }
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except Exception as e:
        logger.error(f"Failed to create backup for '{project_id}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/import-model", response_model=ProjectManifest)
async def import_model(project_id: str, req: ImportModelRequest):
    """Imports external URDF or MJCF model into the project."""
    try:
        return project_manager.import_robot_model(
            project_id=project_id,
            source_model_path=Path(req.source_model_path),
            destination_filename=req.destination_filename,
        )
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except Exception as e:
        logger.error(f"Import model failed for '{project_id}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/export-model")
async def export_model(project_id: str, req: ExportModelRequest):
    """Exports model files and geometries to a target destination directory."""
    try:
        export_path = project_manager.export_robot_model(
            project_id=project_id,
            export_dir=Path(req.export_dir),
            format_type=req.format_type,
        )
        return {
            "status": "EXPORTED",
            "project_id": project_id,
            "export_dir": str(export_path.resolve()),
            "format": req.format_type,
        }
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except Exception as e:
        logger.error(f"Export model failed for '{project_id}': {e}")
        raise HTTPException(status_code=500, detail=str(e))
