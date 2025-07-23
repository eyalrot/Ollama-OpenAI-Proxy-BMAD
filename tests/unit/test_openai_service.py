"""Tests for OpenAI service wrapper."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from ollama_openai_proxy.config import Settings
from ollama_openai_proxy.exceptions import OpenAIError
from ollama_openai_proxy.services.openai_service import OpenAIService
from openai import APIError, APITimeoutError, RateLimitError
from openai.types import Model


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = MagicMock(spec=Settings)
    settings.get_openai_api_key.return_value = "test-api-key"
    settings.openai_api_base_url = "https://api.test.com/v1"
    settings.request_timeout = 30
    return settings


@pytest.fixture
def openai_service(mock_settings):
    """Create OpenAI service with mock settings."""
    return OpenAIService(mock_settings)


class TestOpenAIService:
    """Test OpenAI service functionality."""

    def test_initialization(self, openai_service, mock_settings):
        """Test service initialization."""
        assert openai_service.settings == mock_settings
        assert openai_service._client is None
        assert openai_service._request_count == 0
        assert openai_service._error_count == 0

    def test_client_lazy_initialization(self, openai_service):
        """Test client is created on first access."""
        assert openai_service._client is None

        with patch("ollama_openai_proxy.services.openai_service.AsyncOpenAI") as mock_client:
            client = openai_service.client
            assert client is not None
            assert openai_service._client is not None
            mock_client.assert_called_once()

    def test_generate_request_id(self, openai_service):
        """Test request ID generation."""
        id1 = openai_service._generate_request_id()
        id2 = openai_service._generate_request_id()

        assert id1.startswith("req_")
        assert id2.startswith("req_")
        assert id1 != id2
        assert len(id1) == 12  # "req_" + 8 hex chars

    @pytest.mark.parametrize(
        "error,should_retry",
        [
            (APITimeoutError("Timeout"), True),
            (ValueError("Invalid input"), False),
        ],
    )
    def test_should_retry(self, openai_service, error, should_retry):
        """Test retry logic for different errors."""
        assert openai_service._should_retry(error) == should_retry

    def test_should_retry_api_errors(self, openai_service):
        """Test retry logic for API errors with status codes."""
        # Test 5xx errors (should retry)
        error_503 = MagicMock(spec=APIError)
        error_503.status_code = 503
        assert openai_service._should_retry(error_503) is True

        # Test 4xx errors (should not retry)
        error_400 = MagicMock(spec=APIError)
        error_400.status_code = 400
        assert openai_service._should_retry(error_400) is False

    def test_should_retry_rate_limit(self, openai_service):
        """Test retry logic for rate limit errors."""
        # RateLimitError should always retry
        error = MagicMock(spec=RateLimitError)
        assert openai_service._should_retry(error) is True

    @pytest.mark.asyncio
    async def test_list_models_success(self, openai_service):
        """Test successful model listing."""
        mock_models = [
            Model(id="gpt-3.5-turbo", created=1234567890, object="model", owned_by="openai"),
            Model(id="gpt-4", created=1234567891, object="model", owned_by="openai"),
        ]

        mock_client = MagicMock()
        openai_service._client = mock_client
        mock_response = MagicMock()
        mock_response.data = mock_models
        mock_client.models.list = AsyncMock(return_value=mock_response)

        models = await openai_service.list_models()

        assert len(models) == 2
        assert models[0].id == "gpt-3.5-turbo"
        assert models[1].id == "gpt-4"
        assert openai_service._request_count == 1
        assert openai_service._error_count == 0

    @pytest.mark.asyncio
    async def test_retry_on_timeout(self, openai_service):
        """Test retry logic on timeout errors."""
        mock_client = MagicMock()
        openai_service._client = mock_client
        # First two calls timeout, third succeeds
        mock_client.models.list = AsyncMock(
            side_effect=[APITimeoutError("Timeout 1"), APITimeoutError("Timeout 2"), MagicMock(data=[])]
        )

        # Speed up test by reducing retry delay
        openai_service.retry_delay = 0.01

        models = await openai_service.list_models()

        assert models == []
        assert mock_client.models.list.call_count == 3
        assert openai_service._request_count == 3
        assert openai_service._error_count == 2

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, openai_service):
        """Test behavior when max retries are exceeded."""
        mock_client = MagicMock()
        openai_service._client = mock_client
        # All calls fail
        mock_client.models.list = AsyncMock(side_effect=APITimeoutError("Persistent timeout"))

        openai_service.retry_delay = 0.01

        with pytest.raises(OpenAIError) as exc_info:
            await openai_service.list_models()

        assert "after 4 attempts" in str(exc_info.value)
        assert mock_client.models.list.call_count == 4  # Initial + 3 retries

    @pytest.mark.asyncio
    async def test_create_chat_completion(self, openai_service):
        """Test chat completion creation."""
        mock_completion = MagicMock()
        mock_completion.id = "chat-123"

        mock_client = MagicMock()
        openai_service._client = mock_client
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

        result = await openai_service.create_chat_completion(
            model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Hello"}], temperature=0.7
        )

        assert result.id == "chat-123"
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Hello"}], stream=False, temperature=0.7
        )

    @pytest.mark.asyncio
    async def test_create_chat_completion_stream(self, openai_service):
        """Test streaming chat completion."""
        mock_chunks = [
            MagicMock(id="chunk-1"),
            MagicMock(id="chunk-2"),
            MagicMock(id="chunk-3"),
        ]

        async def mock_stream():
            for chunk in mock_chunks:
                yield chunk

        mock_client = MagicMock()
        openai_service._client = mock_client
        mock_client.chat.completions.create = AsyncMock(return_value=mock_stream())

        chunks = []
        async for chunk in openai_service.create_chat_completion_stream(
            model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Hello"}]
        ):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert chunks[0].id == "chunk-1"

    @pytest.mark.asyncio
    async def test_create_embedding(self, openai_service):
        """Test embedding creation."""
        mock_embedding = MagicMock()
        mock_embedding.data = [{"embedding": [0.1, 0.2, 0.3]}]

        mock_client = MagicMock()
        openai_service._client = mock_client
        mock_client.embeddings.create = AsyncMock(return_value=mock_embedding)

        result = await openai_service.create_embedding(model="text-embedding-ada-002", input="Test text")

        assert result.data[0]["embedding"] == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, openai_service):
        """Test health check when service is healthy."""
        with patch.object(openai_service, "list_models") as mock_list:
            mock_list.return_value = [MagicMock(), MagicMock()]

            health = await openai_service.health_check()

            assert health["status"] == "healthy"
            assert health["models_available"] == 2
            assert health["error_rate"] == 0

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, openai_service):
        """Test health check when service is unhealthy."""
        with patch.object(openai_service, "list_models") as mock_list:
            mock_list.side_effect = Exception("API is down")

            health = await openai_service.health_check()

            assert health["status"] == "unhealthy"
            assert "API is down" in health["error"]

    @pytest.mark.asyncio
    async def test_close(self, openai_service):
        """Test service cleanup."""
        mock_client = AsyncMock()
        openai_service._client = mock_client

        await openai_service.close()

        mock_client.close.assert_called_once()
        assert openai_service._client is None
