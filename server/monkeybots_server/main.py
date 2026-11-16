"""
MonkeyBots Backend Service
FastAPI entrypoint orchestrating simulation, kinematics, and telemetry IPC.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from core.monkeybots.config import settings
from server.monkeybots_server.utils.logger import get_logger, logger
from server.monkeybots_server.router_system import router as system_router
from server.monkeybots_server.router_projects import router as projects_router
from server.monkeybots_server.router_simulation import router as simulation_router
from server.monkeybots_server.router_ws import router as ws_router
from server.monkeybots_server.router_models import router as models_router

log = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and graceful shutdown."""
    log.info(f"==================================================")
    log.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    log.info(f"Workspace Projects: {settings.PROJECTS_DIR}")
    log.info(f"Logs Directory:     {settings.LOGS_DIR}")
    log.info(f"Host: {settings.HOST}:{settings.PORT}")
    log.info(f"==================================================")
    
    yield
    
    log.info(f"Graceful shutdown initiated. Terminating background threads & simulators...")
    log.info(f"{settings.APP_NAME} backend successfully stopped.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Local-first robotics engineering and simulation platform backend",
    lifespan=lifespan,
)

# Configure CORS for local desktop & web development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Application-Level Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": str(exc),
            "path": request.url.path,
        },
    )

# Include Routers
app.include_router(system_router)
app.include_router(projects_router)
app.include_router(simulation_router)
app.include_router(ws_router)
app.include_router(models_router)


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "ONLINE",
        "docs_url": "/docs",
    }
