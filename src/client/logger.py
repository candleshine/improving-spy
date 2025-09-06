"""
Logging configuration for the Spy Agency CLI application.

This module sets up logging for the application, writing logs to both
the console and a file specified in the config module.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from src.client.config import LOG_FILE, LOG_LEVEL


def setup_logger(name: str = "spy_console", log_file: Optional[Path] = None) -> logging.Logger:
    """
    Configure and return a logger with the specified name.
    
    Args:
        name: The name of the logger
        log_file: Path to the log file. If None, uses the default from config.
        
    Returns:
        A configured logger instance
    """
    logger = logging.getLogger(name)
    
    # If the logger already has handlers, assume it's configured and return it
    # This prevents duplicate handlers being added when the function is called multiple times
    if logger.hasHandlers():
        return logger
    
    # Set the log level based on the config
    level = getattr(logging, LOG_LEVEL)
    logger.setLevel(level)
    
    # Create formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    console_formatter = logging.Formatter(
        "%(levelname)s: %(message)s"
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(level)
    
    # Create file handler
    file_path = log_file or LOG_FILE
    try:
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    except (PermissionError, FileNotFoundError) as e:
        # If we can't write to the log file, just log to console
        console_handler.setLevel(logging.WARNING)
        logger.addHandler(console_handler)
        logger.warning(f"Could not create log file at {file_path}: {e}")
        return logger
    
    # Add the console handler
    logger.addHandler(console_handler)
    
    return logger


def configure_logging() -> logging.Logger:
    """
    Configure the logging system for the application.
    
    Returns:
        The configured logger instance
    """
    return setup_logger()


# Create a default logger instance
logger = setup_logger()
