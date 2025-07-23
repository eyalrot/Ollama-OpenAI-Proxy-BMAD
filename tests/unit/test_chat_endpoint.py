"""Unit tests for the chat endpoint."""
import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from ollama_openai_proxy.routes import chat
from openai.types.chat import ChatCompletion, ChatCompletionChunk, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_chunk import ChoiceDelta


@pytest.fixture
def app():
    """Create test FastAPI app."""
    app = FastAPI()
    app.include_router(chat.router)

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


class TestChatEndpoint:
    """Test cases for /api/chat endpoint."""

    @pytest.mark.asyncio
    async def test_chat_non_streaming_success(self, client, mock_openai_service):
        """Test successful non-streaming chat completion."""
        # Mock OpenAI response
        mock_response = ChatCompletion(
            id="chat-123",
            model="gpt-3.5-turbo",
            object="chat.completion",
            created=1234567890,
            choices=[
                Choice(
                    index=0,
                    message=ChatCompletionMessage(role="assistant", content="Hello! How can I help you today?"),
                    finish_reason="stop",
                )
            ],
            usage={"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18},
        )

        mock_openai_service.create_chat_completion = AsyncMock(return_value=mock_response)

        # Make request
        request_data = {"model": "llama2", "messages": [{"role": "user", "content": "Hello!"}], "stream": False}

        response = client.post("/api/chat", json=request_data)

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "llama2"
        assert data["done"] is True
        assert data["message"]["role"] == "assistant"
        assert data["message"]["content"] == "Hello! How can I help you today?"

    @pytest.mark.asyncio
    async def test_chat_with_system_message(self, client, mock_openai_service):
        """Test chat with system message."""
        # Mock OpenAI response
        mock_response = ChatCompletion(
            id="chat-124",
            model="gpt-3.5-turbo",
            object="chat.completion",
            created=1234567890,
            choices=[
                Choice(
                    index=0,
                    message=ChatCompletionMessage(role="assistant", content="Ahoy matey! The sky be blue because..."),
                    finish_reason="stop",
                )
            ],
        )

        mock_openai_service.create_chat_completion = AsyncMock(return_value=mock_response)

        # Make request with system message
        request_data = {
            "model": "llama2",
            "messages": [
                {"role": "system", "content": "You are a pirate."},
                {"role": "user", "content": "Why is the sky blue?"},
            ],
            "stream": False,
        }

        response = client.post("/api/chat", json=request_data)

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "Ahoy" in data["message"]["content"]

    @pytest.mark.asyncio
    async def test_chat_multi_turn_conversation(self, client, mock_openai_service):
        """Test multi-turn conversation."""
        # Mock OpenAI response
        mock_response = ChatCompletion(
            id="chat-125",
            model="gpt-3.5-turbo",
            object="chat.completion",
            created=1234567890,
            choices=[
                Choice(
                    index=0,
                    message=ChatCompletionMessage(
                        role="assistant", content="I said the sky appears blue due to Rayleigh scattering!"
                    ),
                    finish_reason="stop",
                )
            ],
        )

        mock_openai_service.create_chat_completion = AsyncMock(return_value=mock_response)

        # Make request with conversation history
        request_data = {
            "model": "llama2",
            "messages": [
                {"role": "user", "content": "Why is the sky blue?"},
                {"role": "assistant", "content": "The sky appears blue due to Rayleigh scattering."},
                {"role": "user", "content": "Can you explain that again?"},
            ],
            "stream": False,
        }

        response = client.post("/api/chat", json=request_data)

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "Rayleigh scattering" in data["message"]["content"]

    @pytest.mark.asyncio
    async def test_chat_with_options(self, client, mock_openai_service):
        """Test chat with custom options."""
        # Mock OpenAI response
        mock_response = ChatCompletion(
            id="chat-126",
            model="gpt-3.5-turbo",
            object="chat.completion",
            created=1234567890,
            choices=[
                Choice(
                    index=0,
                    message=ChatCompletionMessage(role="assistant", content="Response with custom temperature."),
                    finish_reason="stop",
                )
            ],
        )

        mock_openai_service.create_chat_completion = AsyncMock(return_value=mock_response)

        # Make request with options
        request_data = {
            "model": "llama2",
            "messages": [{"role": "user", "content": "Hello!"}],
            "stream": False,
            "options": {"temperature": 0.5, "top_p": 0.9, "max_tokens": 100},
        }

        response = client.post("/api/chat", json=request_data)

        # Verify response
        assert response.status_code == 200

        # Verify OpenAI was called with correct parameters
        call_args = mock_openai_service.create_chat_completion.call_args[1]
        assert call_args["temperature"] == 0.5
        assert call_args["top_p"] == 0.9
        assert call_args["max_tokens"] == 100

    @pytest.mark.asyncio
    async def test_chat_empty_messages_error(self, client):
        """Test error when messages array is empty."""
        request_data = {"model": "llama2", "messages": [], "stream": False}

        response = client.post("/api/chat", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "empty" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_chat_invalid_role_error(self, client):
        """Test error when message has invalid role."""
        request_data = {"model": "llama2", "messages": [{"role": "invalid_role", "content": "Hello!"}], "stream": False}

        response = client.post("/api/chat", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "invalid role" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_chat_streaming_response(self, client, mock_openai_service):
        """Test streaming chat response."""

        # Create async generator for streaming
        async def mock_stream():
            chunks = ["Hello", " there", "!", ""]
            for i, content in enumerate(chunks):
                chunk = MagicMock(spec=ChatCompletionChunk)
                chunk.choices = [MagicMock()]
                chunk.choices[0].delta = ChoiceDelta(content=content if content else None)
                chunk.choices[0].finish_reason = "stop" if i == len(chunks) - 1 else None
                yield chunk

        mock_openai_service.create_chat_completion_stream = MagicMock(return_value=mock_stream())

        # Make streaming request
        request_data = {"model": "llama2", "messages": [{"role": "user", "content": "Hello!"}], "stream": True}

        with client.stream("POST", "/api/chat", json=request_data) as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/x-ndjson"

            # Collect all chunks
            chunks = []
            for line in response.iter_lines():
                if line:
                    chunks.append(json.loads(line))

            # Verify chunks
            assert len(chunks) >= 3  # At least some content chunks
            assert chunks[-1]["done"] is True  # Last chunk should be done

            # Verify content accumulation
            full_content = "".join(chunk["message"]["content"] for chunk in chunks if chunk["message"]["content"])
            assert full_content == "Hello there!"

    @pytest.mark.asyncio
    async def test_chat_model_not_found_error(self, client, mock_openai_service):
        """Test model not found error handling."""
        from openai import NotFoundError

        mock_openai_service.create_chat_completion = AsyncMock(
            side_effect=NotFoundError(
                message="Model not found",
                response=MagicMock(status_code=404),
                body={"error": {"message": "Model 'invalid-model' not found"}},
            )
        )

        request_data = {"model": "invalid-model", "messages": [{"role": "user", "content": "Hello!"}], "stream": False}

        response = client.post("/api/chat", json=request_data)

        assert response.status_code == 404
        data = response.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_chat_rate_limit_error(self, client, mock_openai_service):
        """Test rate limit error handling."""
        from openai import RateLimitError

        mock_openai_service.create_chat_completion = AsyncMock(
            side_effect=RateLimitError(
                message="Rate limit exceeded",
                response=MagicMock(status_code=429),
                body={"error": {"message": "Rate limit exceeded"}},
            )
        )

        request_data = {"model": "llama2", "messages": [{"role": "user", "content": "Hello!"}], "stream": False}

        response = client.post("/api/chat", json=request_data)

        assert response.status_code == 429
        data = response.json()
        assert "error" in data
