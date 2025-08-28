#!/usr/bin/env python3
"""
Main application module for the Spy CLI.
"""
import os
import sys
import logging

from textual.app import App

from .screens.main import MainScreen
from .config import APP_NAME, DATA_DIR, LOG_LEVEL

# Initialize logging
log_file = os.path.join(DATA_DIR, 'spy_cli_debug.log')
os.makedirs(DATA_DIR, exist_ok=True)

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger(APP_NAME)


class SpyApp(App):
    """Main application class for the Spy CLI."""
    
    CSS_PATH = "styles/spy_console.tcss"
    SCREENS = {"main": MainScreen}
    
    def on_mount(self) -> None:
        """Initialize the application."""
        self.push_screen("main")


def run_app() -> None:
    """Run the Spy application."""
    try:
        app = SpyApp()
        app.run()
    except Exception as e:
        logger.exception("Fatal error in application")
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run_app()
