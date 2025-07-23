#!/bin/bash
# Run tests in CI environment (no venv)

set -e

echo "Running tests in CI environment..."

# Install test dependencies
pip install -r requirements-dev.txt

# Run linting
echo "Running linting..."
ruff check src/ tests/

# Run type checking
echo "Running type checking..."
mypy src/

# Run all tests
echo "Running all tests..."
pytest -v --cov-report=xml

# Generate coverage report
coverage report