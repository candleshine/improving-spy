#!/usr/bin/env python3
"""
Generate OpenAPI YAML file from FastAPI application.
This script exports the OpenAPI schema from your FastAPI app to a YAML file.
"""
import yaml
import sys
from pathlib import Path

# Import your FastAPI app
sys.path.append(str(Path(__file__).parent))
from main import app

def generate_openapi_yaml(output_file="openapi.yaml"):
    """Generate OpenAPI YAML file from FastAPI application."""
    print(f"Generating OpenAPI YAML file: {output_file}")
    
    # Get the OpenAPI JSON schema from FastAPI
    openapi_schema = app.openapi()
    
    # Convert to YAML and write to file
    with open(output_file, "w") as f:
        yaml.dump(openapi_schema, f, sort_keys=False)
    
    print(f"OpenAPI YAML file generated: {output_file}")
    return output_file

if __name__ == "__main__":
    # Allow custom output filename as command line argument
    output_file = sys.argv[1] if len(sys.argv) > 1 else "openapi.yaml"
    generate_openapi_yaml(output_file)
