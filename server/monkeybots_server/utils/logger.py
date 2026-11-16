"""
MonkeyBots Structured Logging Standard
Provides standardized logging with Loguru or standard library fallback.
"""

import sys
import logging
from pathlib import Path
from core.monkeybots.config import settings

# Ensure log directory exists
settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
log_file_path = settings.LOGS_DIR / "monkeybots_backend.log"

try:
    from loguru import logger

    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG" if settings.DEBUG else "INFO",
        colorize=True,
    )
    logger.add(
        str(log_file_path),
        rotation="10 MB",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
        level="DEBUG",
        encoding="utf-8",
    )

    def get_logger(module_name: str):
        return logger.bind(module=module_name)

except ImportError:
    # Standard library fallback
    std_logger = logging.getLogger("MonkeyBots")
    std_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    if not std_logger.handlers:
        c_handler = logging.StreamHandler(sys.stdout)
        c_format = logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)s - %(message)s')
        c_handler.setFormatter(c_format)
        std_logger.addHandler(c_handler)

        f_handler = logging.FileHandler(str(log_file_path), encoding="utf-8")
        f_handler.setFormatter(c_format)
        std_logger.addHandler(f_handler)

    class StdLoggerWrapper:
        def __init__(self, name):
            self._logger = logging.getLogger(f"MonkeyBots.{name}")

        def debug(self, msg, *args, **kwargs):
            self._logger.debug(msg, *args, **kwargs)

        def info(self, msg, *args, **kwargs):
            self._logger.info(msg, *args, **kwargs)

        def warning(self, msg, *args, **kwargs):
            self._logger.warning(msg, *args, **kwargs)

        def error(self, msg, *args, **kwargs):
            self._logger.error(msg, *args, **kwargs)

        def bind(self, **kwargs):
            return self

    logger = StdLoggerWrapper("Root")

    def get_logger(module_name: str):
        return StdLoggerWrapper(module_name)
