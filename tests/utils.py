"""Test utilities and helpers."""
from typing import Any, Dict, List
from unittest.mock import AsyncMock

from openai.types import Model


class ModelFactory:
    """Factory for creating test models."""

    @staticmethod
    def create_openai_model(model_id: str = "gpt-3.5-turbo", created: int = 1234567890, **kwargs) -> Model:
        """Create an OpenAI model for testing."""
        return Model(id=model_id, created=created, object="model", owned_by=kwargs.get("owned_by", "openai"), **kwargs)

    @staticmethod
    def create_ollama_response(models: List[Dict[str, Any]]) -> Dict:
        """Create an Ollama-format response."""
        return {
            "models": [
                {
                    "name": model.get("name", "test-model"),
                    "modified_at": model.get("modified_at", "2024-01-01T00:00:00Z"),
                    "size": model.get("size", 1000000000),
                    "digest": model.get("digest", "sha256:abcdef"),
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
