#!/usr/bin/env python3
"""
Debug wrapper for frontend.py to catch and display all exceptions
"""
import sys
import traceback

try:
    # Add explicit print statements for debugging
    print("Starting debug wrapper for frontend.py")
    
    # Import the main module
    from frontend import ChronicleApp
    
    print("Successfully imported ChronicleApp")
    
    # Create and run the app with explicit exception handling
    app = ChronicleApp()
    print("Created ChronicleApp instance")
    
    # Run with debug flag
    print("Attempting to run app...")
    app.run()
    
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {str(e)}")
    traceback.print_exc()
    sys.exit(1)
