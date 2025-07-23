"""Unit tests for the embeddings endpoint."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from ollama_openai_proxy.routes import embeddings
from openai import (
    APIConnectionError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    RateLimitError,
)
from openai.types import CreateEmbeddingResponse, Embedding
from openai.types.create_embedding_response import Usage


@pytest.fixture
def app():
    """Create test FastAPI app."""
    app = FastAPI()
    app.include_router(embeddings.router)

    # Mock the OpenAI service
    mock_openai_service = MagicMock()
    app.state.openai_service = mock_openai_service

    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_openai_service(app):
    """Get mock OpenAI service from app."""
    return app.state.openai_service


class TestEmbeddingsEndpoint:
    """Test cases for /api/embeddings and /api/embed endpoints."""

    @pytest.mark.asyncio
    async def test_embeddings_success(self, client, mock_openai_service):
        """Test successful embeddings generation."""
        # Mock OpenAI response
        mock_embedding = Embedding(index=0, embedding=[0.1, 0.2, 0.3, -0.4, 0.5], object="embedding")

        mock_response = CreateEmbeddingResponse(
            data=[mock_embedding],
            model="text-embedding-ada-002",
            object="list",
            usage=Usage(prompt_tokens=10, total_tokens=10),
        )

        mock_openai_service.create_embedding = AsyncMock(return_value=mock_response)

        # Make request
        response = client.post("/api/embeddings", json={"model": "text-embedding-ada-002", "prompt": "Hello, world!"})

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "embedding" in data
        assert data["embedding"] == [0.1, 0.2, 0.3, -0.4, 0.5]

        # Verify OpenAI service was called correctly
        mock_openai_service.create_embedding.assert_called_once()
        call_args = mock_openai_service.create_embedding.call_args
        assert call_args[1]["model"] == "text-embedding-ada-002"
        assert call_args[1]["input"] == "Hello, world!"

    @pytest.mark.asyncio
    async def test_embed_endpoint_alias(self, client, mock_openai_service):
        """Test /api/embed endpoint returns same response as /api/embeddings."""
        # Mock OpenAI response
        mock_embedding = Embedding(index=0, embedding=[0.1, 0.2, 0.3], object="embedding")

        mock_response = CreateEmbeddingResponse(
            data=[mock_embedding],
            model="text-embedding-ada-002",
            object="list",
            usage=Usage(prompt_tokens=5, total_tokens=5),
        )

        mock_openai_service.create_embedding = AsyncMock(return_value=mock_response)

        # Make request to /api/embed
        response = client.post("/api/embed", json={"model": "text-embedding-ada-002", "prompt": "Test"})

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "embedding" in data
        assert data["embedding"] == [0.1, 0.2, 0.3]

    def test_embeddings_empty_prompt(self, client):
        """Test error handling for empty prompt."""
        response = client.post("/api/embeddings", json={"model": "text-embedding-ada-002", "prompt": ""})

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "Prompt cannot be empty" in data["error"]

    @pytest.mark.asyncio
    async def test_embeddings_model_not_found(self, client, mock_openai_service):
        """Test handling of model not found error."""
        # Mock OpenAI error
        mock_openai_service.create_embedding = AsyncMock(
            side_effect=NotFoundError("Model not found", response=MagicMock(status_code=404), body={})
        )

        response = client.post("/api/embeddings", json={"model": "nonexistent-model", "prompt": "Test"})

        assert response.status_code == 404
        data = response.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_embeddings_rate_limit_error(self, client, mock_openai_service):
        """Test handling of rate limit error."""
        # Mock OpenAI error
        mock_openai_service.create_embedding = AsyncMock(
            side_effect=RateLimitError("Rate limit exceeded", response=MagicMock(status_code=429), body={})
        )

        response = client.post("/api/embeddings", json={"model": "text-embedding-ada-002", "prompt": "Test"})

        assert response.status_code == 429
        data = response.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_embeddings_auth_error(self, client, mock_openai_service):
        """Test handling of authentication error."""
        # Mock OpenAI error
        mock_openai_service.create_embedding = AsyncMock(
            side_effect=AuthenticationError("Invalid API key", response=MagicMock(status_code=401), body={})
        )

        response = client.post("/api/embeddings", json={"model": "text-embedding-ada-002", "prompt": "Test"})

        assert response.status_code == 401
        data = response.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_embeddings_bad_request(self, client, mock_openai_service):
        """Test handling of bad request error."""
        # Mock OpenAI error
        mock_openai_service.create_embedding = AsyncMock(
            side_effect=BadRequestError("Invalid request", response=MagicMock(status_code=400), body={})
        )

        response = client.post("/api/embeddings", json={"model": "text-embedding-ada-002", "prompt": "Test"})

        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_embeddings_connection_error(self, client, mock_openai_service):
        """Test handling of connection error."""
        # Mock OpenAI error
        mock_openai_service.create_embedding = AsyncMock(side_effect=APIConnectionError(request=MagicMock()))

        response = client.post("/api/embeddings", json={"model": "text-embedding-ada-002", "prompt": "Test"})

        assert response.status_code == 503
        data = response.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_embeddings_timeout_error(self, client, mock_openai_service):
        """Test handling of timeout error."""
        # Mock timeout error
        mock_openai_service.create_embedding = AsyncMock(side_effect=TimeoutError("Request timed out"))

        response = client.post("/api/embeddings", json={"model": "text-embedding-ada-002", "prompt": "Test"})

        assert response.status_code == 504
        data = response.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_embeddings_high_dimensional(self, client, mock_openai_service):
        """Test handling of high-dimensional embeddings (1536 dimensions)."""
        # Create a large embedding vector
        large_embedding = [0.1] * 1536

        mock_embedding = Embedding(index=0, embedding=large_embedding, object="embedding")

        mock_response = CreateEmbeddingResponse(
            data=[mock_embedding],
            model="text-embedding-ada-002",
            object="list",
            usage=Usage(prompt_tokens=10, total_tokens=10),
        )

        mock_openai_service.create_embedding = AsyncMock(return_value=mock_response)

        response = client.post(
            "/api/embeddings", json={"model": "text-embedding-ada-002", "prompt": "Test high-dimensional embeddings"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "embedding" in data
        assert len(data["embedding"]) == 1536
        assert all(x == 0.1 for x in data["embedding"])

    @pytest.mark.asyncio
    async def test_embeddings_very_long_prompt(self, client, mock_openai_service):
        """Test handling of very long prompts."""
        # Create a very long prompt
        long_prompt = "This is a test. " * 1000

        mock_embedding = Embedding(index=0, embedding=[0.1, 0.2, 0.3], object="embedding")

        mock_response = CreateEmbeddingResponse(
            data=[mock_embedding],
            model="text-embedding-ada-002",
            object="list",
            usage=Usage(prompt_tokens=1000, total_tokens=1000),
        )

        mock_openai_service.create_embedding = AsyncMock(return_value=mock_response)

        response = client.post("/api/embeddings", json={"model": "text-embedding-ada-002", "prompt": long_prompt})

        assert response.status_code == 200
        data = response.json()
        assert "embedding" in data

    def test_embeddings_missing_model(self, client):
        """Test error handling for missing model field."""
        response = client.post("/api/embeddings", json={"prompt": "Test"})

        assert response.status_code == 422  # Unprocessable Entity

    def test_embeddings_missing_prompt(self, client):
        """Test error handling for missing prompt field."""
        response = client.post("/api/embeddings", json={"model": "text-embedding-ada-002"})

        assert response.status_code == 422  # Unprocessable Entity

    @pytest.mark.asyncio
    async def test_embeddings_preserve_dimensions(self, client, mock_openai_service):
        """Test that embedding dimensions are preserved without truncation."""
        # Test with different embedding sizes
        test_cases = [
            (384, "small-model"),
            (768, "medium-model"),
            (1024, "large-model"),
            (1536, "text-embedding-ada-002"),
            (3072, "text-embedding-3-large"),
        ]

        for dimensions, model in test_cases:
            embedding_vector = [float(i) / dimensions for i in range(dimensions)]

            mock_embedding = Embedding(index=0, embedding=embedding_vector, object="embedding")

            mock_response = CreateEmbeddingResponse(
                data=[mock_embedding], model=model, object="list", usage=Usage(prompt_tokens=10, total_tokens=10)
            )

            mock_openai_service.create_embedding = AsyncMock(return_value=mock_response)

            response = client.post("/api/embeddings", json={"model": model, "prompt": f"Test {dimensions} dimensions"})

            assert response.status_code == 200
            data = response.json()
            assert "embedding" in data
            assert len(data["embedding"]) == dimensions
            # Verify values are preserved
            for i, val in enumerate(data["embedding"]):
                assert abs(val - (float(i) / dimensions)) < 1e-6

    def test_embeddings_correlation_id_header(self, client):
        """Test that correlation ID is included in response headers."""
        response = client.post(
            "/api/embeddings",
            json={"model": "text-embedding-ada-002", "prompt": "Test"},
            headers={"X-Correlation-ID": "test-correlation-123"},
        )

        assert "X-Correlation-ID" in response.headers
        assert response.headers["X-Correlation-ID"] == "test-correlation-123"
