#!/usr/bin/env python
"""
Alternative entry point for the Spy Agency CLI application.

This module provides a convenient entry point for running the Spy CLI
from the project root directory.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.client.spy_cli import main

if __name__ == "__main__":
    sys.exit(main())
