"""
Configuration module for the Spy Agency CLI application.

This module contains all configuration settings for the application,
including server connection details, logging settings, and UI preferences.
"""

import os
from pathlib import Path
from typing import Dict, Any

# Server connection settings
SERVER_HOST = "localhost"
SERVER_PORT = 8000
SERVER_URL = f"ws://{SERVER_HOST}:{SERVER_PORT}"
WEBSOCKET_BASE_URL = f"{SERVER_URL}/ws"
API_BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"

# WebSocket endpoint for the game
WS_GAME_ENDPOINT = "play"

# Application settings
APP_NAME = "Spy Agency Console"
APP_VERSION = "1.0.0"
APP_PLATFORM = "terminal"

# Path to CSS file
CSS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "styles/spy_console.tcss")

# UI settings
TERMINAL_TITLE = "Spy Agency Terminal"
TERMINAL_SUB_TITLE = "Secure Communication Channel"

# Logging settings
LOG_DIR = Path.home() / ".spy_console"
LOG_FILE = LOG_DIR / "spy_cli_debug.log"
LOG_LEVEL = "DEBUG"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

# WebSocket settings
WS_RECONNECT_MAX_ATTEMPTS = 5
WS_RECONNECT_BASE_DELAY = 1.0  # seconds
WS_HEARTBEAT_INTERVAL = 30.0  # seconds
WS_HEARTBEAT_TIMEOUT = 10.0  # seconds

# Create log directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

# Default agent settings
DEFAULT_AGENT_ID = "agent1"
DEFAULT_AGENT_NAME = "Agent"
DEFAULT_AGENT_CODENAME = "Alpha"

# Default scenario
DEFAULT_SCENARIO = "last_oracle"

# Message display settings
MAX_MESSAGES_DISPLAYED = 100
MESSAGE_TIMESTAMP_FORMAT = "%H:%M:%S"

# User preferences (could be loaded from a file in the future)
USER_PREFERENCES: Dict[str, Any] = {
    "show_timestamps": True,
    "show_typing_indicator": True,
    "theme": "dark",
    "message_alignment": "left",
}

# Styling constants
COLORS = {
    "primary": "#3498db",
    "secondary": "#2ecc71",
    "accent": "#e74c3c",
    "background": "#1e1e2e",
    "foreground": "#f8f8f2",
    "user_message": "#2ecc71",
    "agent_message": "#3498db",
    "system_message": "#e74c3c",
    "typing_indicator": "#f39c12",
}
