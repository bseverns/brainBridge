"""Logging configuration for sb-rig-bridge."""
from __future__ import annotations

import logging
import sys
from typing import Optional


def setup_logging(level: str = "INFO", name: str = "sbrig") -> logging.Logger:
    """Configure and return the bridge logger.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(
        fmt="[%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Optional sub-logger name (e.g., "sbrig.morph")
        
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"sbrig.{name}")
    return logging.getLogger("sbrig")
