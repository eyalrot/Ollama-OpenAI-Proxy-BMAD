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