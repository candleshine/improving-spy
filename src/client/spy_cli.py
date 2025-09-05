#!/usr/bin/env python
"""
Spy Agency CLI application.

This module contains the main entry point for the Spy Agency CLI application.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from textual.app import App

from src.client.config import APP_NAME, APP_VERSION, CSS_PATH
from src.client.logger import configure_logging, logger
from src.client.screens.main import MainScreen


class SpyConsoleApp(App):
    """
    Spy Agency CLI application.
    
    This class is the main entry point for the Spy Agency CLI application.
    """
    
    TITLE = f"{APP_NAME} v{APP_VERSION}"
    CSS_PATH = CSS_PATH
    SCREENS = {"main": MainScreen}
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the application.
        
        Args:
            *args: Additional positional arguments for the parent class
            **kwargs: Additional keyword arguments for the parent class
        """
        super().__init__(*args, **kwargs)
        
    def on_mount(self) -> None:
        """Handle the mount event."""
        # Switch to the main screen
        self.push_screen("main")


def main():
    """Main entry point for the application."""
    # Configure logging
    configure_logging()
    
    try:
        # Create and run the application
        app = SpyConsoleApp()
        app.run()
        
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")
        sys.exit(1)
        
    finally:
        logger.info("Application exited")


if __name__ == "__main__":
    main()
