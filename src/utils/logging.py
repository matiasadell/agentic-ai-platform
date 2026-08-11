"""Logging configuration using Loguru."""

import sys
from loguru import logger
from .config import settings


def setup_logging() -> None:
    """Configure logging for the application."""
    
    # Remove default handler
    logger.remove()
    
    # Console handler with color
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True,
    )
    
    # File handler
    logger.add(
        "logs/finsight_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        compression="zip",
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )
    
    logger.info(f"Logging configured - Level: {settings.log_level}, Environment: {settings.environment}")


# Export configured logger
__all__ = ["logger", "setup_logging"]
