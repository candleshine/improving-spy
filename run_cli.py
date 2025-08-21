#!/usr/bin/env python3
"""
Run script for the Spy CLI application.
This script ensures proper module imports by running from the project root.
"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the CLI
from src.client.spy_cli import SpyCommandConsole

if __name__ == "__main__":
    app = SpyCommandConsole()
    app.run()
