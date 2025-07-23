"""Shared test configuration and fixtures."""
import asyncio
import os
import sys
from typing import Any, AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from httpx import AsyncClient  # noqa: E402
from ollama_openai_proxy.config import Settings, get_settings  # noqa: E402
from ollama_openai_proxy.main import app  # noqa: E402
from ollama_openai_proxy.services.openai_service import OpenAIService  # noqa: E402

# Test environment setup - only set if not already set
# Skip setting OPENAI_API_KEY to allow testing missing key scenarios
if "LOG_LEVEL" not in os.environ:
    os.environ["LOG_LEVEL"] = "DEBUG"


# Event loop handled by pytest-asyncio


@pytest.fixture
def mock_settings() -> Any:
    """Create mock settings for testing."""
    settings = Settings(
        openai_api_key="test-key-12345",
        openai_api_base_url="https://api.test.com/v1",
        proxy_port=11434,
        log_level="DEBUG",
        request_timeout=30,
    )
    return settings


@pytest.fixture
def test_client(mock_openai_service: Any) -> Generator[TestClient, None, None]:
    """Create FastAPI test client."""
    # Clear settings cache
    get_settings.cache_clear()

    # Create test client
    client = TestClient(app)

    # Set up mock OpenAI service
    app.state.openai_service = mock_openai_service

    yield client


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_openai_service(mock_settings: Any) -> Any:
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
def mock_openai_models() -> Any:
    """Create mock OpenAI model responses."""
    from openai.types import Model

    return [
        Model(id="gpt-3.5-turbo", created=1234567890, object="model", owned_by="openai"),
        Model(id="gpt-4", created=1234567891, object="model", owned_by="openai"),
        Model(id="text-embedding-ada-002", created=1234567892, object="model", owned_by="openai"),
    ]


@pytest.fixture
def mock_ollama_client(monkeypatch: Any) -> Any:
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


@pytest.fixture
def mock_openai_completion() -> Any:
    """Create mock OpenAI completion response."""
    from openai.types.chat import ChatCompletion, ChatCompletionMessage
    from openai.types.chat.chat_completion import Choice

    return ChatCompletion(
        id="chatcmpl-test123",
        object="chat.completion",
        created=1234567890,
        model="gpt-3.5-turbo",
        choices=[
            Choice(
                index=0,
                message=ChatCompletionMessage(
                    role="assistant", content="The sky appears blue because of a phenomenon called Rayleigh scattering."
                ),
                finish_reason="stop",
            )
        ],
        usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
    )


@pytest.fixture
def mock_openai_streaming() -> Any:
    """Create mock OpenAI streaming response."""
    from openai.types.chat import ChatCompletionChunk
    from openai.types.chat.chat_completion_chunk import Choice, ChoiceDelta

    async def stream_generator() -> AsyncGenerator[Any, None]:
        chunks = [
            ChatCompletionChunk(
                id="chatcmpl-test123",
                object="chat.completion.chunk",
                created=1234567890,
                model="gpt-3.5-turbo",
                choices=[Choice(index=0, delta=ChoiceDelta(content="The"), finish_reason=None)],
            ),
            ChatCompletionChunk(
                id="chatcmpl-test123",
                object="chat.completion.chunk",
                created=1234567890,
                model="gpt-3.5-turbo",
                choices=[Choice(index=0, delta=ChoiceDelta(content=" sky"), finish_reason=None)],
            ),
            ChatCompletionChunk(
                id="chatcmpl-test123",
                object="chat.completion.chunk",
                created=1234567890,
                model="gpt-3.5-turbo",
                choices=[Choice(index=0, delta=ChoiceDelta(content=" is"), finish_reason=None)],
            ),
            ChatCompletionChunk(
                id="chatcmpl-test123",
                object="chat.completion.chunk",
                created=1234567890,
                model="gpt-3.5-turbo",
                choices=[Choice(index=0, delta=ChoiceDelta(content=" blue"), finish_reason=None)],
            ),
            ChatCompletionChunk(
                id="chatcmpl-test123",
                object="chat.completion.chunk",
                created=1234567890,
                model="gpt-3.5-turbo",
                choices=[Choice(index=0, delta=ChoiceDelta(content=""), finish_reason="stop")],
            ),
        ]

        for chunk in chunks:
            yield chunk

    return stream_generator


@pytest.fixture(autouse=True)
def reset_app_state() -> Generator[None, None, None]:
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
            # Use asyncio.run for cleanup
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(app.state.openai_service.close())
                else:
                    asyncio.run(app.state.openai_service.close())
            except Exception:
                pass  # Ignore cleanup errors


# Markers for test organization
def pytest_configure(config: Any) -> None:
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "sdk: Ollama SDK compatibility tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "requires_api_key: Tests requiring real API key")
