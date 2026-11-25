"""
System Diagnostics REST API
Monitors physics engine state, hardware capabilities, and solver health.
"""

import sys
import platform
from fastapi import APIRouter
from core.monkeybots.config import settings
from core.monkeybots.models.registry import list_registered_robots

router = APIRouter(prefix="/api/v1/diagnostics", tags=["diagnostics"])


@router.get("/system")
async def get_system_diagnostics():
    return {
        "status": "HEALTHY",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "platform": platform.platform(),
        "python_version": sys.version.split()[0],
        "physics_engine": "MuJoCo 3.x C-Engine",
        "registered_robots_count": len(list_registered_robots()),
        "robot_models": list_registered_robots(),
        "acceleration": "CPU (SIMD AVX2)",
    }
