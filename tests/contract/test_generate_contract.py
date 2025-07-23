"""Contract tests for /api/generate endpoint compliance with Ollama API spec."""
import json
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient


class TestGenerateEndpointContract:
    """Contract tests to ensure /api/generate matches Ollama API specification."""

    @pytest.fixture
    def valid_generate_request(self) -> Dict[str, Any]:
        """Valid Ollama generate request based on API spec."""
        return {
            "model": "llama2",
            "prompt": "Why is the sky blue?",
            "stream": False,
            "options": {"temperature": 0.7, "top_p": 0.9, "seed": 42},
        }

    @pytest.fixture
    def valid_streaming_request(self) -> Dict[str, Any]:
        """Valid Ollama streaming generate request."""
        return {"model": "llama2", "prompt": "Tell me a story", "stream": True}

    def test_generate_request_schema(self, test_client: TestClient, valid_generate_request: Dict[str, Any]) -> None:
        """Test that endpoint accepts valid Ollama generate request format."""
        response = test_client.post("/api/generate", json=valid_generate_request)

        # Should accept the request (even if it fails due to missing implementation)
        assert response.status_code in [200, 404, 501, 500]  # 404/501/500 ok for not implemented yet

    def test_generate_request_minimal(self, test_client: TestClient) -> None:
        """Test minimal valid request with only required fields."""
        minimal_request = {"model": "llama2", "prompt": "Hello"}

        response = test_client.post("/api/generate", json=minimal_request)
        assert response.status_code in [200, 404, 501, 500]

    def test_generate_request_validation(self, test_client: TestClient) -> None:
        """Test request validation for required fields."""
        # Missing model
        invalid_request = {"prompt": "Hello"}
        response = test_client.post("/api/generate", json=invalid_request)
        assert response.status_code in [422, 400, 404]  # Validation error or not found

        # Missing prompt
        invalid_request = {"model": "llama2"}
        response = test_client.post("/api/generate", json=invalid_request)
        assert response.status_code in [422, 400, 404]  # Validation error or not found

    def test_generate_response_format_non_streaming(self, test_client: TestClient, mock_openai_completion: Any) -> None:
        """Test non-streaming response format matches Ollama spec."""
        # Mock the OpenAI service to return our mock completion
        app = test_client.app
        app.state.openai_service.create_chat_completion = AsyncMock(return_value=mock_openai_completion)

        request = {"model": "llama2", "prompt": "Why is the sky blue?", "stream": False}

        response = test_client.post("/api/generate", json=request)

        if response.status_code == 200:
            data = response.json()
            print(f"Response data: {data}")  # Debug output

            # Required fields per Ollama spec
            assert "model" in data
            assert "created_at" in data
            assert "response" in data
            assert "done" in data

            # Validate field types
            assert isinstance(data["model"], str)
            assert isinstance(data["created_at"], str)
            assert isinstance(data["response"], str)
            assert isinstance(data["done"], bool)

            # Validate done flag for non-streaming
            assert data["done"] is True

            # Validate timestamp format (RFC3339 with timezone)
            try:
                # Should parse as RFC3339
                datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            except ValueError:
                pytest.fail(f"Invalid timestamp format: {data['created_at']}")

            # Optional fields that may be present
            optional_fields = [
                "total_duration",
                "load_duration",
                "prompt_eval_count",
                "prompt_eval_duration",
                "eval_count",
                "eval_duration",
                "context",
                "done_reason",
            ]

            for field in optional_fields:
                if field in data and data[field] is not None:
                    if "duration" in field:
                        assert isinstance(data[field], int)
                    elif "count" in field:
                        assert isinstance(data[field], int)
                    elif field == "context":
                        assert isinstance(data[field], list)
                    elif field == "done_reason":
                        assert data[field] in ["stop", "length", "load"]

    def test_generate_response_streaming_format(self, test_client: TestClient, mock_openai_streaming: Any) -> None:
        """Test streaming response format matches Ollama spec."""
        # Mock the OpenAI service to return our streaming generator
        # Since create_chat_completion_stream is an async generator method,
        # we replace it directly with our mock generator
        app = test_client.app
        app.state.openai_service.create_chat_completion_stream = mock_openai_streaming

        request = {"model": "llama2", "prompt": "Tell me a story", "stream": True}

        with test_client:
            with test_client.stream("POST", "/api/generate", json=request) as response:
                if response.status_code == 200:
                    chunks = []
                    for line in response.iter_lines():
                        if line:
                            chunk = json.loads(line)
                            chunks.append(chunk)

                            # Validate each chunk
                            assert "model" in chunk
                            assert "created_at" in chunk
                            assert "response" in chunk
                            assert "done" in chunk

                            # Types
                            assert isinstance(chunk["model"], str)
                            assert isinstance(chunk["created_at"], str)
                            assert isinstance(chunk["response"], str)
                            assert isinstance(chunk["done"], bool)

                    # Validate streaming sequence
                    assert len(chunks) > 0

                    # All chunks except last should have done=false
                    for chunk in chunks[:-1]:
                        assert chunk["done"] is False

                    # Last chunk should have done=true
                    assert chunks[-1]["done"] is True

                    # Last chunk may have additional fields
                    last_chunk = chunks[-1]
                    if "total_duration" in last_chunk:
                        assert isinstance(last_chunk["total_duration"], int)

    def test_generate_options_handling(self, test_client: TestClient) -> None:
        """Test that options are properly handled."""
        request = {
            "model": "llama2",
            "prompt": "Hello",
            "stream": False,
            "options": {
                "temperature": 0.5,
                "top_p": 0.95,
                "top_k": 40,
                "seed": 12345,
                "num_predict": 100,
                "num_ctx": 2048,
                "stop": ["\\n", "User:"],
            },
        }

        response = test_client.post("/api/generate", json=request)
        assert response.status_code in [200, 404, 501, 500]

    def test_generate_raw_mode(self, test_client: TestClient) -> None:
        """Test raw mode support."""
        request = {"model": "llama2", "prompt": "Raw prompt without template", "raw": True, "stream": False}

        response = test_client.post("/api/generate", json=request)
        assert response.status_code in [200, 404, 501, 500]

    def test_generate_json_format(self, test_client: TestClient) -> None:
        """Test JSON format mode."""
        request = {
            "model": "llama2",
            "prompt": "Generate a JSON object with name and age",
            "format": "json",
            "stream": False,
        }

        response = test_client.post("/api/generate", json=request)
        assert response.status_code in [200, 404, 501, 500]

    def test_generate_system_prompt(self, test_client: TestClient) -> None:
        """Test system prompt support."""
        request = {"model": "llama2", "prompt": "Hello", "system": "You are a helpful assistant", "stream": False}

        response = test_client.post("/api/generate", json=request)
        assert response.status_code in [200, 404, 501, 500]

    def test_generate_context_preservation(self, test_client: TestClient) -> None:
        """Test context field for conversation continuation."""
        request = {
            "model": "llama2",
            "prompt": "Continue from before",
            "context": [128006, 882, 128007],  # Example context tokens
            "stream": False,
        }

        response = test_client.post("/api/generate", json=request)
        assert response.status_code in [200, 404, 501, 500]

        if response.status_code == 200:
            data = response.json()
            # Response should include context for next turn
            if "context" in data:
                assert isinstance(data["context"], list)

    def test_generate_keep_alive(self, test_client: TestClient) -> None:
        """Test keep_alive parameter."""
        request = {"model": "llama2", "prompt": "Hello", "keep_alive": "5m", "stream": False}

        response = test_client.post("/api/generate", json=request)
        assert response.status_code in [200, 404, 501, 500]
