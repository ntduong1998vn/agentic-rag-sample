---
description: run project tests
---

# Run Tests

This workflow runs the test suite for the project.

## Prerequisites

- Ensure Docker services are running (especially PostgreSQL for integration tests)
- Ensure dependencies are installed

## Run All Tests

// turbo
1. Run all tests with pytest:
   ```bash
   uv run pytest
   ```

## Run Tests with Coverage

// turbo
2. Run tests with coverage report:
   ```bash
   uv run pytest --cov=app --cov-report=html --cov-report=term
   ```

3. View the HTML coverage report:
   ```bash
   open htmlcov/index.html
   ```

## Run Specific Tests

// turbo
4. Run tests in a specific file:
   ```bash
   uv run pytest tests/test_chatbot_api.py
   ```

// turbo
5. Run tests matching a pattern:
   ```bash
   uv run pytest -k "test_chatbot"
   ```

// turbo
6. Run tests with verbose output:
   ```bash
   uv run pytest -v
   ```

## Run Tests in Watch Mode

7. Install pytest-watch (if not already installed):
   ```bash
   uv pip install pytest-watch
   ```

8. Run tests in watch mode (re-runs on file changes):
   ```bash
   uv run ptw
   ```

## Tips

- Use `-v` flag for verbose output
- Use `-s` flag to see print statements
- Use `-x` flag to stop at first failure
- Use `--lf` to run only last failed tests
- Use `--ff` to run failures first, then others

## Test Structure

- Unit tests: Test individual functions and classes in isolation
- Integration tests: Test API endpoints and database interactions
- All tests should be in the `tests/` directory
- Follow naming convention: `test_*.py` for files, `test_*` for functions
