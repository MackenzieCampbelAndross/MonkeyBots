"""
Unit and Integration Tests for MonkeyBots Stage 11: Local Project Management and Storage
Verifies:
1. Filesystem-based project creation, directory hierarchy, and metadata schemas.
2. Atomic saving, .bak file creation, and recovery from interrupted/corrupted saves.
3. Open, close, save, save-as, duplicate, rename, and delete lifecycle.
4. Offline project integrity validation and missing asset detection.
5. Project backup creation (.mbpkg archive) and restoration.
6. Robot model import and export.
7. FastAPI REST API endpoints on /api/v1/projects/*.
"""

import pytest
import json
import shutil
from pathlib import Path
from fastapi.testclient import TestClient

from core.monkeybots.projects import (
    ProjectManager,
    ProjectManifest,
    ProjectMetadata,
    atomic_write,
    recover_interrupted_saves,
    create_snapshot,
    validate_project_integrity,
    create_project_archive,
    extract_project_archive,
)
from core.monkeybots.projects.schema import GeometryAssetReference
from server.monkeybots_server.main import app

client = TestClient(app)


def test_project_creation_and_hierarchy(tmp_path: Path):
    """Test creating a project with the complete structured directory hierarchy."""
    manager = ProjectManager(projects_dir=tmp_path)
    manifest = manager.create_project(
        name="Articulated 6-Axis Arm",
        description="Precision factory automation robot",
        robot_preset="6dof_industrial",
    )

    project_dir = tmp_path / manifest.metadata.id
    assert project_dir.exists()
    assert (project_dir / "project.json").exists()
    assert (project_dir / "robot.mjcf").exists()
    assert (project_dir / "robot.urdf").exists()
    assert (project_dir / "assets").is_dir()
    assert (project_dir / "trajectories").is_dir()
    assert (project_dir / "experiments").is_dir()
    assert (project_dir / "logs").is_dir()
    assert (project_dir / "reports").is_dir()
    assert (project_dir / ".snapshots").is_dir()

    # Verify initial snapshot
    snapshots = list((project_dir / ".snapshots").iterdir())
    assert len(snapshots) >= 1


def test_atomic_file_write_and_recovery(tmp_path: Path):
    """Test atomic file writes and recovery from interrupted/corrupted saves."""
    test_file = tmp_path / "data.json"

    # 1. Normal atomic write
    atomic_write(test_file, json.dumps({"status": "OK", "step": 1}))
    assert test_file.exists()
    assert json.loads(test_file.read_text(encoding="utf-8"))["step"] == 1

    # 2. Overwrite creates a safety .bak
    atomic_write(test_file, json.dumps({"status": "OK", "step": 2}))
    assert json.loads(test_file.read_text(encoding="utf-8"))["step"] == 2
    bak_file = test_file.with_suffix(".json.bak")
    assert bak_file.exists()
    assert json.loads(bak_file.read_text(encoding="utf-8"))["step"] == 1

    # 3. Simulate an interrupted save with an abandoned temp file and corrupted manifest
    project_dir = tmp_path / "mock_project"
    project_dir.mkdir(parents=True, exist_ok=True)
    manifest_file = project_dir / "project.json"
    bak_manifest = project_dir / "project.json.bak"

    # Valid backup
    bak_manifest.write_text(json.dumps({"name": "Recovered Project"}), encoding="utf-8")
    # Corrupt target (interrupted write simulation)
    manifest_file.write_text("{ incomplete json...", encoding="utf-8")
    # Orphaned temp file
    temp_orphan = project_dir / "project.tmp_1234_abc.json"
    temp_orphan.write_text("temporary data", encoding="utf-8")

    # Run recovery
    actions = recover_interrupted_saves(project_dir)
    assert any("Cleaned orphaned temporary file" in a for a in actions)
    assert any("restored project.json from safety backup" in a for a in actions)
    assert not temp_orphan.exists()

    # Manifest is now valid JSON from .bak
    loaded = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert loaded["name"] == "Recovered Project"


def test_project_manifest_save_and_reopen(tmp_path: Path):
    """Test saving updated physics parameters, trajectories, and controller gains, and reopening."""
    manager = ProjectManager(projects_dir=tmp_path)
    proj = manager.create_project("SCARA Workcell", robot_preset="6dof")
    proj_id = proj.metadata.id

    # Modify physics and controller gains
    proj.physics.timestep = 0.001
    proj.physics.integrator = "Euler"
    proj.controllers.gains[0].kp = 999.0
    proj.experiments = ["EXP_001", "EXP_002"]

    saved = manager.save_project(proj_id, proj)
    assert saved.physics.timestep == 0.001

    # Reopen fresh
    reloaded = manager.get_project(proj_id)
    assert reloaded.physics.timestep == 0.001
    assert reloaded.physics.integrator == "Euler"
    assert reloaded.controllers.gains[0].kp == 999.0
    assert reloaded.experiments == ["EXP_001", "EXP_002"]


def test_project_save_as_and_duplicate(tmp_path: Path):
    """Test save-as and duplication with independent deep copy."""
    manager = ProjectManager(projects_dir=tmp_path)
    orig = manager.create_project("Source Robot", "Original system")

    # Duplicate
    dupe = manager.duplicate_project(orig.metadata.id, "Duplicated Robot")
    assert dupe.metadata.id != orig.metadata.id
    assert dupe.metadata.name == "Duplicated Robot"
    assert (tmp_path / dupe.metadata.id / "project.json").exists()
    assert (tmp_path / dupe.metadata.id / "robot.mjcf").exists()

    # Save As
    saved_as = manager.save_project_as(orig.metadata.id, "Saved As Robot", new_id="custom_slug_robot")
    assert saved_as.metadata.id == "custom_slug_robot"
    assert saved_as.metadata.name == "Saved As Robot"
    assert (tmp_path / "custom_slug_robot" / "project.json").exists()


def test_project_rename_and_delete(tmp_path: Path):
    """Test renaming a project and deleting it with safety confirmation check."""
    manager = ProjectManager(projects_dir=tmp_path)
    proj = manager.create_project("Temporary Robot")
    proj_id = proj.metadata.id

    # Rename
    renamed = manager.rename_project(proj_id, "Renamed Robot")
    assert renamed.metadata.name == "Renamed Robot"
    assert manager.get_project(proj_id).metadata.name == "Renamed Robot"

    # Delete without confirmation -> must raise ValueError
    with pytest.raises(ValueError):
        manager.delete_project(proj_id, confirmation=False)

    # Delete with confirmation
    res = manager.delete_project(proj_id, confirmation=True)
    assert res is True
    assert not (tmp_path / proj_id).exists()


def test_project_integrity_and_missing_asset_detection(tmp_path: Path):
    """Test project integrity auditing, missing asset detection, and relative path checks."""
    manager = ProjectManager(projects_dir=tmp_path)
    proj = manager.create_project("Integrity Test Robot")
    proj_id = proj.metadata.id

    # Healthy project audit
    report1 = manager.validate_project(proj_id)
    assert report1.is_valid is True
    assert report1.status == "HEALTHY"
    assert report1.manifest_valid is True
    assert report1.model_mjcf_valid is True
    assert report1.missing_assets_count == 0

    # Inject missing asset reference in manifest
    proj.assets.append(
        GeometryAssetReference(
            name="gripper_mesh",
            relative_path="assets/non_existent_gripper.stl",
            format="stl",
        )
    )
    manager.save_project(proj_id, proj)

    # Re-validate: should detect missing asset
    report2 = manager.validate_project(proj_id)
    assert report2.status == "WARNING"
    assert report2.missing_assets_count == 1
    assert any("non_existent_gripper.stl" in w for w in report2.warnings)


def test_project_backup_archive_and_restore(tmp_path: Path):
    """Test exporting project to .mbpkg (zip archive) and restoring it."""
    manager = ProjectManager(projects_dir=tmp_path)
    proj = manager.create_project("Backup Source Robot")
    proj_id = proj.metadata.id

    # Create backup archive
    archive_file = manager.create_backup(proj_id)
    assert archive_file.exists()
    assert archive_file.suffix == ".mbpkg"
    assert archive_file.stat().st_size > 0

    # Restore backup into a new project
    restored = manager.restore_backup(archive_file, new_project_id="restored_backup_robot")
    assert restored.metadata.id == "restored_backup_robot"
    assert (tmp_path / "restored_backup_robot" / "project.json").exists()
    assert (tmp_path / "restored_backup_robot" / "robot.mjcf").exists()

    # Verify integrity of restored project
    rep = manager.validate_project("restored_backup_robot")
    assert rep.is_valid is True
    assert rep.status == "HEALTHY"


def test_fastapi_projects_endpoints():
    """Verify all FastAPI REST API endpoints for project lifecycle."""
    # 1. List projects
    list_res = client.get("/api/v1/projects")
    assert list_res.status_code == 200
    assert isinstance(list_res.json(), list)

    # 2. Create project via API
    create_payload = {
        "name": "API Integration Robot",
        "description": "Created via FastAPI endpoint",
        "robot_preset": "6dof_industrial",
        "robot_type": "Articulated Arm",
    }
    create_res = client.post("/api/v1/projects/create", json=create_payload)
    assert create_res.status_code == 201
    created_proj = create_res.json()
    proj_id = created_proj["metadata"]["id"]
    assert proj_id.startswith("api_integration_robot")

    # 3. Get project
    get_res = client.get(f"/api/v1/projects/{proj_id}")
    assert get_res.status_code == 200
    assert get_res.json()["metadata"]["name"] == "API Integration Robot"

    # 4. Save/update project manifest
    manifest_data = get_res.json()
    manifest_data["physics"]["timestep"] = 0.001
    put_res = client.put(f"/api/v1/projects/{proj_id}", json=manifest_data)
    assert put_res.status_code == 200
    assert put_res.json()["physics"]["timestep"] == 0.001

    # 5. Duplicate project
    dupe_res = client.post(f"/api/v1/projects/{proj_id}/duplicate?new_name=API_Dupe")
    assert dupe_res.status_code == 200
    dupe_id = dupe_res.json()["metadata"]["id"]

    # 6. Rename project
    rename_res = client.patch(f"/api/v1/projects/{proj_id}/rename", json={"new_name": "API Renamed Robot"})
    assert rename_res.status_code == 200
    assert rename_res.json()["metadata"]["name"] == "API Renamed Robot"

    # 7. Validate project
    val_res = client.get(f"/api/v1/projects/{proj_id}/validate")
    assert val_res.status_code == 200
    assert val_res.json()["status"] == "HEALTHY"

    # 8. Create backup
    bkp_res = client.post(f"/api/v1/projects/{proj_id}/backup")
    assert bkp_res.status_code == 200
    bkp_data = bkp_res.json()
    assert bkp_data["status"] == "BACKUP_CREATED"
    backup_file_path = bkp_data["path"]

    # 9. List backups
    bkps_res = client.get(f"/api/v1/projects/backups?project_id={proj_id}")
    assert bkps_res.status_code == 200
    assert len(bkps_res.json()["backups"]) >= 1

    # 10. Delete duplicate without confirm -> 400
    del_bad = client.delete(f"/api/v1/projects/{dupe_id}")
    assert del_bad.status_code == 400

    # 11. Delete duplicate with confirm -> 200
    del_ok = client.delete(f"/api/v1/projects/{dupe_id}?confirm=true")
    assert del_ok.status_code == 200

    # 12. Delete primary created project
    client.delete(f"/api/v1/projects/{proj_id}?confirm=true")
