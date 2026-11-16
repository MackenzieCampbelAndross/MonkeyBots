"""
System & Health Check Router
Provides engine status, health verification, and lifecycle management endpoints.
"""

import os
import sys
import time
import psutil
import asyncio
from fastapi import APIRouter, status
from pydantic import BaseModel
from core.monkeybots.config import settings
from server.monkeybots_server.utils.logger import get_logger

router = APIRouter(prefix="/api/v1/system", tags=["System & Health"])
logger = get_logger("router_system")

START_TIME = time.time()


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    uptime_seconds: float
    python_version: str
    os: str
    cpu_percent: float
    memory_percent: float
    mujoco_available: bool


@router.get("/health", response_model=HealthResponse)
async def get_health():
    """Health check endpoint used by Tauri desktop shell and UI status indicator."""
    mujoco_ok = False
    try:
        import mujoco
        mujoco_ok = True
    except ImportError:
        pass

    uptime = time.time() - START_TIME
    mem = psutil.virtual_memory()

    return HealthResponse(
        status="HEALTHY",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        uptime_seconds=round(uptime, 2),
        python_version=sys.version.split()[0],
        os=sys.platform,
        cpu_percent=psutil.cpu_percent(),
        memory_percent=mem.percent,
        mujoco_available=mujoco_ok,
    )


@router.post("/shutdown")
async def trigger_shutdown():
    """Graceful shutdown endpoint triggered by Tauri when closing window."""
    logger.info("Shutdown signal received via REST API. Terminating backend in 500ms...")

    async def _delayed_exit():
        await asyncio.sleep(0.5)
        os._exit(0)

    asyncio.create_task(_delayed_exit())
    return {"message": "Shutting down gracefully"}
