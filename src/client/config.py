"""
Configuration settings for the Spy Command Console application.
"""
import os
from typing import Dict, Any

# API settings
API_BASE_URL = os.environ.get("SPY_API_URL", "http://localhost:8000")
API_TIMEOUT = 30  # seconds

# WebSocket settings
WS_BASE_URL = os.environ.get("SPY_WS_URL", "ws://localhost:8000")
WS_RECONNECT_ATTEMPTS = 3
WS_RECONNECT_DELAY = 2  # seconds

# UI settings
UI_THEME = {
    "background": "#000000",
    "text": "#00ff00",
    "accent": "#003300",
    "error": "#ff0000",
    "warning": "#ffff00",
    "info": "#0088ff",
}

# Logging settings
LOG_LEVEL = os.environ.get("SPY_LOG_LEVEL", "INFO")
LOG_FILE = os.environ.get("SPY_LOG_FILE", "")  # Empty string means log to stdout only

# Data directories
DATA_DIR = os.path.join(os.path.expanduser("~"), ".spy_console")
HISTORY_DIR = os.path.join(DATA_DIR, "history")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(HISTORY_DIR, exist_ok=True)

# Application settings
APP_NAME = "Spy Command Console"
APP_VERSION = "1.0.0"

def get_config() -> Dict[str, Any]:
    """Return the full configuration as a dictionary."""
    return {
        "api": {
            "base_url": API_BASE_URL,
            "timeout": API_TIMEOUT,
        },
        "websocket": {
            "base_url": WS_BASE_URL,
            "reconnect_attempts": WS_RECONNECT_ATTEMPTS,
            "reconnect_delay": WS_RECONNECT_DELAY,
        },
        "ui": UI_THEME,
        "logging": {
            "level": LOG_LEVEL,
            "file": LOG_FILE,
        },
        "paths": {
            "data_dir": DATA_DIR,
            "history_dir": HISTORY_DIR,
        },
        "app": {
            "name": APP_NAME,
            "version": APP_VERSION,
        },
    }
