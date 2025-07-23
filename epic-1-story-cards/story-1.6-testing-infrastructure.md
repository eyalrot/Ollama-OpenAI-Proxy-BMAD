# Story 1.6: Testing Infrastructure Setup

**Story Points**: 3  
**Priority**: P0 (Critical for quality)  
**Type**: Infrastructure  
**Dependencies**: Stories 1.1-1.5 provide code to test

## Story Summary
**As a** developer,  
**I want to** set up comprehensive testing infrastructure,  
**So that** I can verify true compatibility with Ollama clients.

## Technical Implementation Guide

### Pre-Implementation Checklist
- [ ] Basic project structure in place (Story 1.1)
- [ ] pytest installed via requirements-dev.txt
- [ ] Virtual environment activated for local development

### Implementation Steps

#### Step 1: Create Test Configuration
**tests/conftest.py**:
```python
"""Shared test configuration and fixtures."""
import asyncio
import os
import sys
from typing import AsyncIterator, Iterator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ollama_openai_proxy.config import Settings, get_settings
from ollama_openai_proxy.main import app
from ollama_openai_proxy.services.openai_service import OpenAIService


# Test environment setup
os.environ["OPENAI_API_KEY"] = "test-key-12345"
os.environ["LOG_LEVEL"] = "DEBUG"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = Settings(
        openai_api_key="test-key-12345",
        openai_api_base_url="https://api.test.com/v1",
        proxy_port=11434,
        log_level="DEBUG",
        request_timeout=30
    )
    return settings


@pytest.fixture
def test_client():
    """Create FastAPI test client."""
    # Clear settings cache
    get_settings.cache_clear()
    
    # Create test client
    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture
async def async_client():
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_openai_service(mock_settings):
    """Create mock OpenAI service."""
    service = MagicMock(spec=OpenAIService)
    service.settings = mock_settings
    service._request_count = 0
    service._error_count = 0
    
    # Mock methods
    service.list_models = AsyncMock()
    service.create_chat_completion = AsyncMock()
    service.create_chat_completion_stream = AsyncMock()
    service.create_embedding = AsyncMock()
    service.health_check = AsyncMock()
    service.close = AsyncMock()
    
    return service


@pytest.fixture
def mock_openai_models():
    """Create mock OpenAI model responses."""
    from openai.types import Model
    
    return [
        Model(
            id="gpt-3.5-turbo",
            created=1234567890,
            object="model",
            owned_by="openai"
        ),
        Model(
            id="gpt-4",
            created=1234567891,
            object="model",
            owned_by="openai"
        ),
        Model(
            id="text-embedding-ada-002",
            created=1234567892,
            object="model",
            owned_by="openai"
        ),
    ]


@pytest.fixture
def mock_ollama_client(monkeypatch):
    """Create mock Ollama client for SDK tests."""
    # Only create if ollama is installed
    try:
        import ollama
        
        # Set test URL
        monkeypatch.setenv("OLLAMA_HOST", "http://localhost:11434")
        
        client = ollama.Client(host="http://localhost:11434")
        return client
    except ImportError:
        pytest.skip("ollama package not installed")


@pytest.fixture(autouse=True)
def reset_app_state():
    """Reset app state between tests."""
    # Clear any existing state
    if hasattr(app.state, "settings"):
        delattr(app.state, "settings")
    if hasattr(app.state, "openai_service"):
        delattr(app.state, "openai_service")
    
    yield
    
    # Cleanup after test
    if hasattr(app.state, "openai_service"):
        if hasattr(app.state.openai_service, "close"):
            asyncio.create_task(app.state.openai_service.close())


# Markers for test organization
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "sdk: Ollama SDK compatibility tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests"
    )
    config.addinivalue_line(
        "markers", "requires_api_key: Tests requiring real API key"
    )
```

#### Step 2: Create Test Utilities
**tests/utils.py**:
```python
"""Test utilities and helpers."""
import json
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

from openai.types import Model


class ModelFactory:
    """Factory for creating test models."""
    
    @staticmethod
    def create_openai_model(
        model_id: str = "gpt-3.5-turbo",
        created: int = 1234567890,
        **kwargs
    ) -> Model:
        """Create an OpenAI model for testing."""
        return Model(
            id=model_id,
            created=created,
            object="model",
            owned_by=kwargs.get("owned_by", "openai"),
            **kwargs
        )
    
    @staticmethod
    def create_ollama_response(models: List[Dict[str, Any]]) -> Dict:
        """Create an Ollama-format response."""
        return {
            "models": [
                {
                    "name": model.get("name", "test-model"),
                    "modified_at": model.get("modified_at", "2024-01-01T00:00:00Z"),
                    "size": model.get("size", 1000000000),
                    "digest": model.get("digest", "sha256:abcdef")
                }
                for model in models
            ]
        }


class AsyncContextManagerMock:
    """Mock for async context managers."""
    
    def __init__(self, return_value=None):
        self.return_value = return_value
        self.aenter_called = False
        self.aexit_called = False
    
    async def __aenter__(self):
        self.aenter_called = True
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.aexit_called = True
        return False


def assert_ollama_model_format(model: Dict[str, Any]) -> None:
    """Assert that a model matches Ollama format."""
    assert "name" in model
    assert "modified_at" in model
    assert "size" in model
    assert isinstance(model["name"], str)
    assert isinstance(model["modified_at"], str)
    assert isinstance(model["size"], int)
    assert model["modified_at"].endswith("Z")  # ISO format with Z


def create_mock_stream(chunks: List[Any]) -> AsyncMock:
    """Create a mock async stream."""
    async def async_generator():
        for chunk in chunks:
            yield chunk
    
    return async_generator()
```

#### Step 3: Create pytest Configuration
**pytest.ini**:
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto

# Coverage settings
addopts = 
    --verbose
    --strict-markers
    --tb=short
    --cov=src/ollama_openai_proxy
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml
    --cov-fail-under=80

# Test markers
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (may require services)
    sdk: Ollama SDK compatibility tests
    slow: Tests that take > 1 second
    requires_api_key: Tests requiring real OpenAI API key

# Ignore warnings
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

#### Step 4: Create Test Runner Scripts
**scripts/test_local.sh**:
```bash
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
```

**scripts/test_ci.sh**:
```bash
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
```

#### Step 5: Create GitHub Actions Workflow
Update **.github/workflows/test.yml**:
```yaml
name: Test

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12"]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('requirements-dev.txt') }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt
    
    - name: Run linting
      run: |
        ruff check src/ tests/
    
    - name: Run type checking
      run: |
        mypy src/
    
    - name: Run unit tests
      run: |
        pytest tests/unit -v
    
    - name: Run integration tests
      run: |
        pytest tests/integration -v -m "not requires_api_key"
    
    - name: Generate coverage report
      run: |
        pytest --cov=src/ollama_openai_proxy --cov-report=xml --cov-report=term
    
    - name: Check coverage threshold
      run: |
        coverage report --fail-under=80
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
```

#### Step 6: Create Test Documentation
**tests/README.md**:
```markdown
# Testing Guide

## Overview

This project uses pytest for all testing with a target of 80% code coverage.

## Test Structure

```
tests/
├── conftest.py          # Shared fixtures and configuration
├── utils.py             # Test utilities
├── unit/                # Unit tests (fast, isolated)
│   ├── test_config.py
│   ├── test_openai_service.py
│   └── test_translation_service.py
└── integration/         # Integration tests
    ├── test_tags_endpoint.py
    └── test_ollama_sdk_compatibility.py
```

## Running Tests

### Local Development (with venv)

```bash
# Activate virtual environment first
source venv/bin/activate

# Run all tests
pytest

# Run only unit tests
pytest tests/unit

# Run with coverage
pytest --cov=src/ollama_openai_proxy

# Run specific test file
pytest tests/unit/test_config.py -v

# Run tests matching pattern
pytest -k "test_translation" -v
```

### CI Environment

Tests run automatically on push/PR via GitHub Actions.

## Test Markers

- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.sdk` - Ollama SDK compatibility tests
- `@pytest.mark.slow` - Tests taking > 1 second
- `@pytest.mark.requires_api_key` - Requires real API key

## Writing Tests

### Unit Test Example

```python
@pytest.mark.unit
def test_something_fast():
    """Test description."""
    assert True
```

### Async Test Example

```python
@pytest.mark.asyncio
async def test_async_operation():
    """Test async operation."""
    result = await some_async_function()
    assert result == expected
```

### Using Fixtures

```python
def test_with_mock_settings(mock_settings):
    """Test using mock settings fixture."""
    assert mock_settings.proxy_port == 11434
```

## Coverage Requirements

- Minimum: 80% overall
- Target: 90% for core modules
- View report: `open htmlcov/index.html`
```

### Verification Steps

1. **Run test infrastructure check:**
   ```bash
   # From activated venv
   pytest --collect-only  # Shows all discovered tests
   ```

2. **Run tests with coverage:**
   ```bash
   chmod +x scripts/test_local.sh
   ./scripts/test_local.sh
   ```

3. **Check coverage report:**
   ```bash
   coverage report
   coverage html
   open htmlcov/index.html  # View in browser
   ```

4. **Test GitHub Actions locally:**
   ```bash
   # Install act (GitHub Actions runner)
   brew install act  # macOS
   
   # Run workflow locally
   act -j test
   ```

### Definition of Done Checklist

- [ ] Test configuration (conftest.py) created
- [ ] Test utilities for common operations
- [ ] pytest.ini with coverage settings
- [ ] Fixtures for all major components
- [ ] Test markers for organization
- [ ] GitHub Actions workflow configured
- [ ] Test scripts for local and CI
- [ ] Test documentation complete
- [ ] 80% coverage threshold enforced
- [ ] All existing tests pass

### Common Issues & Solutions

1. **Import errors in tests:**
   - Ensure src is in Python path (handled in conftest.py)
   - Check virtual environment is activated

2. **Async test failures:**
   - Use `@pytest.mark.asyncio` decorator
   - Ensure pytest-asyncio is installed

3. **Coverage not meeting threshold:**
   - Add tests for uncovered code
   - Use `# pragma: no cover` sparingly for unreachable code

### Next Steps

After completing this story:
1. Run full test suite
2. Verify coverage meets 80% threshold
3. Commit all test infrastructure
4. Create PR for review
5. Move to Story 1.7: Ollama SDK Compatibility Test Suite