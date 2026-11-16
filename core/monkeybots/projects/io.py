"""
MonkeyBots Robust Filesystem I/O Engine
Implements atomic file writes, crash/power-loss recovery, backup archives (.mbpkg),
rolling revision snapshots, and asset path management.
Guarantees zero database reliance and safe local data persistence.
"""

import os
import shutil
import zipfile
import uuid
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple


def atomic_write(target_path: Path, content: str | bytes, is_json: bool = False) -> Path:
    """
    Atomically writes content to target_path using an isolated temporary file,
    flushes and syncs to physical disk, creates a safety .bak copy of any existing file,
    and atomically replaces the target.
    
    Prevents file corruption if the process or system halts mid-write.
    """
    target_path = Path(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Unique temp file in the same directory (ensures same filesystem volume for atomic rename)
    temp_name = f"{target_path.stem}.tmp_{os.getpid()}_{uuid.uuid4().hex[:8]}{target_path.suffix}"
    temp_path = target_path.parent / temp_name

    try:
        if isinstance(content, str):
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
        else:
            with open(temp_path, "wb") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())

        # If target already exists and is non-empty, keep a safety backup
        backup_path = target_path.with_suffix(target_path.suffix + ".bak")
        if target_path.exists() and target_path.stat().st_size > 0:
            try:
                shutil.copy2(target_path, backup_path)
            except Exception:
                pass

        # Atomic rename/replace
        os.replace(temp_path, target_path)
        return target_path

    except Exception as e:
        # Clean up temporary artifact on error
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass
        raise IOError(f"Atomic write to '{target_path}' failed: {e}") from e


def recover_interrupted_saves(directory: Path) -> List[str]:
    """
    Scans directory for interrupted save artifacts (.tmp_*),
    cleans up abandoned temporary files, and if project.json is missing or corrupt,
    attempts recovery from project.json.bak or the latest snapshot.
    Returns a list of recovery actions taken.
    """
    actions: List[str] = []
    directory = Path(directory)
    if not directory.exists() or not directory.is_dir():
        return actions

    # 1. Clean up stray .tmp_* files
    for tmp_file in directory.glob("*.tmp_*"):
        try:
            tmp_file.unlink()
            actions.append(f"Cleaned orphaned temporary file: {tmp_file.name}")
        except Exception as e:
            actions.append(f"Could not remove {tmp_file.name}: {e}")

    # 2. Check primary manifest project.json
    manifest_path = directory / "project.json"
    backup_path = directory / "project.json.bak"
    manifest_corrupted = False

    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                json.load(f)
        except Exception:
            manifest_corrupted = True
            actions.append("Detected corrupted/truncated project.json.")
    else:
        manifest_corrupted = True
        actions.append("project.json was missing.")

    # 3. Recover from .bak if needed
    if manifest_corrupted and backup_path.exists():
        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                json.load(f)  # Ensure backup is valid
            shutil.copy2(backup_path, manifest_path)
            actions.append("Successfully restored project.json from safety backup (project.json.bak).")
            manifest_corrupted = False
        except Exception as e:
            actions.append(f"Failed to restore from backup: {e}")

    # 4. Fallback to latest snapshot in .snapshots/
    snapshots_dir = directory / ".snapshots"
    if manifest_corrupted and snapshots_dir.exists():
        snapshots = sorted([s for s in snapshots_dir.iterdir() if s.is_dir()], reverse=True)
        for s in snapshots:
            snap_manifest = s / "project.json"
            if snap_manifest.exists():
                try:
                    with open(snap_manifest, "r", encoding="utf-8") as f:
                        json.load(f)
                    shutil.copy2(snap_manifest, manifest_path)
                    actions.append(f"Successfully restored project.json from snapshot '{s.name}'.")
                    break
                except Exception:
                    pass

    return actions


def create_snapshot(project_dir: Path, tag: Optional[str] = None) -> Path:
    """
    Creates a timestamped snapshot of project configuration and models in .snapshots/.
    Used for local version control and safe rollback.
    """
    project_dir = Path(project_dir)
    snapshots_dir = project_dir / ".snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    folder_name = f"snapshot_{timestamp_str}"
    if tag:
        folder_name += f"_{tag}"

    snapshot_path = snapshots_dir / folder_name
    snapshot_path.mkdir(parents=True, exist_ok=True)

    # Copy manifest and primary model files
    for fname in ["project.json", "robot.mjcf", "robot.urdf", "workcell.mjcf"]:
        src = project_dir / fname
        if src.exists():
            shutil.copy2(src, snapshot_path / fname)

    # Prune old snapshots (keep 10 most recent)
    all_snaps = sorted([s for s in snapshots_dir.iterdir() if s.is_dir()], key=lambda p: p.stat().st_mtime)
    while len(all_snaps) > 10:
        oldest = all_snaps.pop(0)
        try:
            shutil.rmtree(oldest)
        except Exception:
            pass

    return snapshot_path


def create_project_archive(project_dir: Path, output_file: Optional[Path] = None) -> Path:
    """
    Packages an entire project directory into a single portable MonkeyBots package (.mbpkg / .zip).
    Includes manifest, URDF/MJCF models, geometries, trajectories, experiments, and reports.
    Omits .snapshots to keep archive lean and portable.
    """
    project_dir = Path(project_dir)
    if not output_file:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_file = project_dir.parent / f"{project_dir.name}_backup_{timestamp}.mbpkg"

    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(project_dir):
            # Exclude .snapshots and __pycache__ from archive
            dirs[:] = [d for d in dirs if d not in (".snapshots", "__pycache__", ".git")]
            for file in files:
                if file.endswith((".bak", ".tmp")):
                    continue
                file_path = Path(root) / file
                rel_path = file_path.relative_to(project_dir)
                zf.write(file_path, arcname=str(rel_path))

    return output_file


def extract_project_archive(archive_path: Path, destination_dir: Path) -> Path:
    """
    Restores a project from a .mbpkg / .zip archive into destination_dir.
    Validates archive safety (no directory traversal attacks) and verifies project.json presence.
    """
    archive_path = Path(archive_path)
    destination_dir = Path(destination_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)

    if not zipfile.is_zipfile(archive_path):
        raise ValueError(f"File '{archive_path}' is not a valid MonkeyBots package (.mbpkg/zip).")

    with zipfile.ZipFile(archive_path, "r") as zf:
        # Check for path traversal vulnerabilities (Zip Slip)
        for member in zf.namelist():
            target = destination_dir / member
            if not target.resolve().is_relative_to(destination_dir.resolve()):
                raise SecurityError(f"Security violation: Archive attempts directory traversal in '{member}'")
        
        zf.extractall(destination_dir)

    # Verify extracted integrity
    if not (destination_dir / "project.json").exists():
        raise ValueError("Invalid project package: extracted contents lack 'project.json'.")

    return destination_dir
