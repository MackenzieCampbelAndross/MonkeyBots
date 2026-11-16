"""
MonkeyBots Configuration Manager
Loads environment variables and default system settings using Pydantic Settings V2.
"""

from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "MonkeyBots"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Server / Network
    HOST: str = "127.0.0.1"
    PORT: int = 8765
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "tauri://localhost",
        "https://tauri.localhost",
        "*",
    ]

    # Local Filesystem Paths
    PROJECTS_DIR: Path = Path("projects").resolve()
    LOGS_DIR: Path = Path("logs").resolve()

    # Simulation Defaults
    DEFAULT_TIMESTEP: float = 0.002  # 500 Hz
    TELEMETRY_FPS: int = 60  # 60 Hz broadcast rate

    model_config = SettingsConfigDict(
        env_prefix="MONKEYBOTS_",
        case_sensitive=False,
    )


settings = Settings()
