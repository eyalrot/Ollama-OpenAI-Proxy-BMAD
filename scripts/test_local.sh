#!/bin/bash
# Run tests locally with coverage

set -e

echo "Running tests in virtual environment..."

# Check if in venv
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Error: Not in virtual environment!"
    echo "Please activate venv first: source venv/bin/activate"
    exit 1
fi

# Run unit tests
echo "Running unit tests..."
pytest tests/unit -v -m "not slow"

# Run integration tests
echo "Running integration tests..."
pytest tests/integration -v -m "not requires_api_key"

# Run all tests with coverage
echo "Running all tests with coverage..."
pytest --cov-report=term-missing --cov-report=html

# Check coverage threshold
echo "Checking coverage threshold (80%)..."
coverage report --fail-under=80

echo "All tests passed!"