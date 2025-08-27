#!/usr/bin/env python3
"""
Run script for the Spy CLI application.
This script ensures proper module imports by running from the project root.
"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the application
from src.client.app import run_app

if __name__ == "__main__":
    run_app()
