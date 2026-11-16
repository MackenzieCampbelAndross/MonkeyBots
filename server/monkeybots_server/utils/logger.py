"""
MonkeyBots Structured Logging Standard
Provides standardized JSON and console logging using Loguru.
"""

import sys
from loguru import logger

# Remove default handler
logger.remove()

# Add structured standard output handler
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True,
)

# Standard logging export
def get_logger(module_name: str):
    """Returns a contextualized logger instance."""
    return logger.bind(module=module_name)
