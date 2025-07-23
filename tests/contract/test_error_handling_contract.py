"""Contract tests for error handling in /api/generate endpoint."""
import json
from typing import Any, Dict, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from openai import AuthenticationError, NotFoundError, RateLimitError


class TestErrorHandlingContract:
    """Contract tests to ensure error handling matches Ollama API specification."""

    @pytest.fixture
    def valid_generate_request(self) -> Dict[str, Any]:
        """Valid Ollama generate request."""
        return {
            "model": "llama2",
            "prompt": "Hello",
            "stream": False,
        }

    def test_rate_limit_error_format(self, test_client: TestClient, valid_generate_request: Dict[str, Any]) -> None:
        """Test that rate limit errors (429) are properly formatted."""
        # Mock OpenAI service to raise RateLimitError
        app = cast(Any, test_client).app
        # Create a proper mock response object
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"retry-after": "60"}
        mock_response.request = MagicMock()

        mock_error = RateLimitError(
            message="Rate limit exceeded",
            response=mock_response,
            body={"error": {"message": "Rate limit exceeded", "type": "rate_limit_error"}},
        )
        app.state.openai_service.create_chat_completion = AsyncMock(side_effect=mock_error)

        response = test_client.post("/api/generate", json=valid_generate_request)

        assert response.status_code == 429
        data = response.json()

        # Verify error structure
        assert "error" in data
        assert isinstance(data["error"], str)
        # Should contain rate limit message
        assert "rate limit" in data["error"].lower() or "429" in data["error"]

    def test_authentication_error_format(self, test_client: TestClient, valid_generate_request: Dict[str, Any]) -> None:
        """Test that authentication errors (401) are properly formatted."""
        # Mock OpenAI service to raise AuthenticationError
        app = cast(Any, test_client).app
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.request = MagicMock()

        mock_error = AuthenticationError(
            message="Invalid API key",
            response=mock_response,
            body={"error": {"message": "Invalid API key", "type": "authentication_error"}},
        )
        app.state.openai_service.create_chat_completion = AsyncMock(side_effect=mock_error)

        response = test_client.post("/api/generate", json=valid_generate_request)

        assert response.status_code == 401
        data = response.json()

        # Verify error structure
        assert "error" in data
        assert isinstance(data["error"], str)
        assert "authentication" in data["error"].lower() or "unauthorized" in data["error"].lower()

    def test_model_not_found_error_format(self, test_client: TestClient) -> None:
        """Test that model not found errors are properly formatted."""
        # Mock OpenAI service to raise NotFoundError
        app = cast(Any, test_client).app
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.request = MagicMock()

        mock_error = NotFoundError(
            message="The model 'invalid-model' does not exist",
            response=mock_response,
            body={"error": {"message": "Model not found", "type": "model_not_found"}},
        )
        app.state.openai_service.create_chat_completion = AsyncMock(side_effect=mock_error)

        request = {
            "model": "invalid-model",
            "prompt": "Hello",
            "stream": False,
        }

        response = test_client.post("/api/generate", json=request)

        assert response.status_code == 404
        data = response.json()

        # Verify error structure matches Ollama format
        assert "error" in data
        assert isinstance(data["error"], str)
        assert "not found" in data["error"].lower() or "does not exist" in data["error"].lower()

    def test_invalid_request_parameters_error(self, test_client: TestClient) -> None:
        """Test that invalid request parameters return 422 with details."""
        # Missing required field 'model'
        invalid_request = {
            "prompt": "Hello",
            "stream": False,
        }

        response = test_client.post("/api/generate", json=invalid_request)

        assert response.status_code == 422
        data = response.json()

        # FastAPI validation error format
        assert "detail" in data
        assert isinstance(data["detail"], list)
        assert len(data["detail"]) > 0

        # Check error mentions missing model
        error_str = str(data["detail"])
        assert "model" in error_str.lower()

    def test_empty_prompt_validation_error(self, test_client: TestClient) -> None:
        """Test that empty prompt is handled properly."""
        request = {
            "model": "llama2",
            "prompt": "",  # Empty prompt
            "stream": False,
        }

        response = test_client.post("/api/generate", json=request)

        # Empty prompt might be allowed or return validation error
        if response.status_code == 422:
            data = response.json()
            assert "detail" in data or "error" in data

    def test_streaming_error_format(self, test_client: TestClient) -> None:
        """Test that streaming errors are properly formatted."""
        # Mock OpenAI service to raise error during streaming
        app = cast(Any, test_client).app

        async def mock_stream_error() -> Any:
            # Yield one chunk then error
            yield type(
                "obj",
                (object,),
                {"choices": [{"delta": {"content": "Hello"}, "finish_reason": None}], "model": "gpt-3.5-turbo"},
            )
            mock_resp = MagicMock()
            mock_resp.status_code = 429
            mock_resp.request = MagicMock()
            raise RateLimitError(
                message="Rate limit exceeded during streaming",
                response=mock_resp,
                body={"error": {"message": "Rate limit exceeded"}},
            )

        app.state.openai_service.create_chat_completion_stream = mock_stream_error

        request = {
            "model": "llama2",
            "prompt": "Hello",
            "stream": True,
        }

        with test_client:
            with test_client.stream("POST", "/api/generate", json=request) as response:
                chunks = []
                for line in response.iter_lines():
                    if line:
                        chunks.append(json.loads(line))

                # Should have at least one chunk (maybe error chunk)
                assert len(chunks) >= 1

                # Last chunk should indicate error or done
                last_chunk = chunks[-1]
                assert last_chunk.get("done") is True or "error" in last_chunk

    def test_timeout_error_handling(self, test_client: TestClient, valid_generate_request: Dict[str, Any]) -> None:
        """Test that timeout errors are properly handled."""
        # Mock OpenAI service to raise timeout
        app = cast(Any, test_client).app
        mock_error = TimeoutError("Request timed out")
        app.state.openai_service.create_chat_completion = AsyncMock(side_effect=mock_error)

        response = test_client.post("/api/generate", json=valid_generate_request)

        # Should return 504 Gateway Timeout or 500 Internal Server Error
        assert response.status_code in [500, 504]
        data = response.json()
        assert "error" in data or "detail" in data

    def test_internal_server_error_format(
        self, test_client: TestClient, valid_generate_request: Dict[str, Any]
    ) -> None:
        """Test that internal server errors are properly formatted."""
        # Mock OpenAI service to raise generic exception
        app = cast(Any, test_client).app
        app.state.openai_service.create_chat_completion = AsyncMock(side_effect=Exception("Internal server error"))

        response = test_client.post("/api/generate", json=valid_generate_request)

        assert response.status_code == 500
        data = response.json()

        # Should have error information
        assert "error" in data or "detail" in data

        # Should not expose internal details
        error_msg = str(data)
        assert "traceback" not in error_msg.lower()

    def test_error_includes_correlation_id(self, test_client: TestClient) -> None:
        """Test that errors include correlation IDs for debugging."""
        # This test checks if correlation IDs are included
        # The actual implementation may vary
        request = {
            "model": "non-existent-model",
            "prompt": "Hello",
            "stream": False,
        }

        response = test_client.post("/api/generate", json=request)

        # Check headers for correlation ID
        has_correlation_id = "x-request-id" in response.headers or "x-correlation-id" in response.headers
        assert has_correlation_id, "Should have correlation ID in headers"

    def test_network_connection_error(self, test_client: TestClient, valid_generate_request: Dict[str, Any]) -> None:
        """Test handling of network connection errors."""
        # Mock OpenAI service to raise connection error
        app = cast(Any, test_client).app
        mock_error = ConnectionError("Failed to connect to OpenAI API")
        app.state.openai_service.create_chat_completion = AsyncMock(side_effect=mock_error)

        response = test_client.post("/api/generate", json=valid_generate_request)

        assert response.status_code in [500, 503]  # Internal error or service unavailable
        data = response.json()
        assert "error" in data or "detail" in data
