---
trigger: always_on
description: Use this rule when setting up the development environment, running the application, managing dependencies, or following the project's development process. Essential for getting started and maintaining the development workflow.
globs:
---

# Development Workflow & Getting Started

## Environment Setup
- Use **UV** as the Python package manager (installed via `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Python 3.13+ is required (specified in [pyproject.toml](mdc:pyproject.toml))
- All dependencies are managed through `uv sync`

## Running the Application

### Backend Server
```bash
# From project root
uv run python main.py
```
The backend will start on `http://localhost:8000` with automatic API documentation at `/docs`

### Frontend CLI
```bash
# From project root
uv run python src/client/spy_cli.py
```
Or use the alternative entry point:
```bash
uv run python run_cli.py
```

## Development Commands

### Package Management
```bash
# Install all dependencies
uv sync

# Add new dependency
uv add package-name

# Add development dependency
uv add --dev package-name

# Update dependencies
uv sync --upgrade
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/client/test_widgets.py

# Run with coverage
uv run pytest --cov=src
```

### Code Quality
```bash
# Format code with black
uv run black src/

# Lint with flake8
uv run flake8 src/

# Type checking with mypy
uv run mypy src/
```

## Project Structure Guidelines

### Adding New Features
1. **Backend**: Add models in [src/backend/models/](mdc:src/backend/models/), services in [src/backend/services/](mdc:src/backend/services/), and routes in [src/backend/api/routes.py](mdc:src/backend/api/routes.py)
2. **Frontend**: Add widgets in [src/client/widgets/](mdc:src/client/widgets/) and screens in [src/client/screens/](mdc:src/client/screens/)
3. **Tests**: Add corresponding tests in [tests/](mdc:tests/) directory

### Database Changes
1. Modify models in [src/backend/models/__init__.py](mdc:src/backend/models/__init__.py)
2. Update repositories in [src/backend/repositories/](mdc:src/backend/repositories/)
3. Run database migrations (when implemented)

### API Development
1. Use [requests/](mdc:requests/) directory for testing API endpoints
2. Follow FastAPI best practices with proper status codes and error handling
3. Use Pydantic models for request/response validation

## Key Development Files

### Configuration
- [pyproject.toml](mdc:pyproject.toml) - Project dependencies and metadata
- [src/client/config.py](mdc:src/client/config.py) - Frontend configuration
- [main.py](mdc:main.py) - Backend server configuration

### API Testing
- [requests/01-setup-agent.http](mdc:requests/01-setup-agent.http) - Agent setup requests
- [requests/02-chat-basic.http](mdc:requests/02-chat-basic.http) - Basic chat functionality
- [requests/get_by_codename.http](mdc:requests/get_by_codename.http) - Spy lookup by codename

### Documentation
- [README.md](mdc:README.md) - Project overview and setup instructions
- [src/client/README.md](mdc:src/client/README.md) - Frontend-specific documentation
- [lesson-plans/](mdc:lesson-plans/) - Course materials and weekly objectives

## Debugging Tips
- Use structured logging throughout the application
- Check the FastAPI docs at `/docs` for API testing
- Use the Textual debug mode for frontend issues
- Monitor Ollama logs when debugging AI agent interactions
