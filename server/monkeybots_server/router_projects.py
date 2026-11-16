"""
Local Projects Management Router
Reads, creates, and inspects local filesystem projects without any database.
"""

import json
from pathlib import Path
from typing import List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from core.monkeybots.config import settings
from server.monkeybots_server.schemas.project import ProjectManifest
from server.monkeybots_server.utils.logger import get_logger

router = APIRouter(prefix="/api/v1/projects", tags=["Local Projects"])
logger = get_logger("router_projects")


class ProjectSummary(BaseModel):
    id: str
    name: str
    description: str
    path: str
    dof: int
    has_mjcf: bool
    has_urdf: bool


@router.get("", response_model=List[ProjectSummary])
async def list_projects():
    """Scan local projects directory for valid project folders containing project.json."""
    projects_dir = settings.PROJECTS_DIR
    if not projects_dir.exists():
        projects_dir.mkdir(parents=True, exist_ok=True)
        return []

    summaries: List[ProjectSummary] = []
    for item in sorted(projects_dir.iterdir()):
        if item.is_dir():
            manifest_file = item / "project.json"
            if manifest_file.exists():
                try:
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    manifest = ProjectManifest.model_validate(data)
                    summaries.append(
                        ProjectSummary(
                            id=item.name,
                            name=manifest.metadata.name,
                            description=manifest.metadata.description,
                            path=str(item.resolve()),
                            dof=manifest.robot.dof,
                            has_mjcf=(item / manifest.robot.model_file).exists(),
                            has_urdf=(item / (manifest.robot.urdf_file or "")).exists() if manifest.robot.urdf_file else False,
                        )
                    )
                except Exception as e:
                    logger.warning(f"Failed to parse project manifest at {manifest_file}: {e}")
    return summaries


@router.get("/{project_id}", response_model=ProjectManifest)
async def get_project(project_id: str):
    """Retrieve full manifest for a specific local project."""
    project_dir = settings.PROJECTS_DIR / project_id
    manifest_file = project_dir / "project.json"
    if not manifest_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found")
    
    try:
        with open(manifest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ProjectManifest.model_validate(data)
    except Exception as e:
        logger.error(f"Error reading project {project_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
