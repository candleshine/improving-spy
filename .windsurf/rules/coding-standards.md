---
trigger: model_decision
description: Use this rule when writing or reviewing Python code to ensure consistency with project standards, FastAPI conventions, and best practices. Applies to all Python files and helps maintain code quality and architectural consistency.
globs: *.py
---

# Python Spy Agency Coding Standards

## Python Code Style
- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Use f-strings for string formatting
- Prefer list/dict comprehensions over explicit loops when appropriate
- Use `pathlib.Path` for file operations instead of `os.path`

## FastAPI Conventions
- Use dependency injection with `Depends()` for database sessions and services
- Return Pydantic models as response models
- Use proper HTTP status codes (201 for creation, 404 for not found, etc.)
- Implement proper error handling with `HTTPException`
- Use router prefixes and tags for API organization

## Database & Models
- Use SQLAlchemy 2.0+ style with `declarative_base()`
- Implement repository pattern for data access
- Use Pydantic models for API input/output validation
- Separate SQLAlchemy models from Pydantic models
- Use UUID strings for primary keys

## AI Agent Patterns
- Keep system prompts concise and focused
- Use tool calling sparingly and only when explicitly requested
- Implement proper error handling for AI model interactions
- Cache mission context when appropriate
- Use structured logging for debugging AI interactions

## Error Handling
- Log errors with appropriate log levels
- Return meaningful error messages to users
- Use try-catch blocks around external service calls
- Implement graceful degradation for non-critical failures

## Testing
- Write unit tests for all business logic
- Use pytest fixtures for common test setup
- Mock external dependencies (AI models, databases)
- Test both success and failure scenarios

## File Organization
- Keep related functionality in the same module
- Use `__init__.py` files to expose public APIs
- Group imports: standard library, third-party, local
- Maintain clear separation between backend and frontend code

## Documentation
- Use docstrings for all public functions and classes
- Include type information in docstrings
- Document complex business logic with inline comments
- Keep README files updated with current project status
