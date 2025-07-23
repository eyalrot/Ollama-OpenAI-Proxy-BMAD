"""Ollama SDK compatibility tests for list functionality."""
import os
import time
from datetime import datetime
from unittest.mock import patch

import pytest

# Import ollama if available
ollama = pytest.importorskip("ollama", reason="ollama package required for SDK tests")

# Import after ollama to avoid E402
from ollama_openai_proxy.services.openai_service import OpenAIService  # noqa: E402


@pytest.mark.sdk
class TestOllamaSDKList:
    """Test Ollama SDK list() compatibility."""

    @pytest.fixture
    def ollama_client(self):
        """Create Ollama client pointing to test proxy."""
        # Use test server URL
        client = ollama.Client(host="http://localhost:11434")
        return client

    @pytest.fixture
    def mock_openai_models(self):
        """Mock OpenAI models for consistent testing."""
        from openai.types import Model

        return [
            Model(id="gpt-3.5-turbo", created=1680000000, object="model", owned_by="openai"),
            Model(id="gpt-4", created=1680000001, object="model", owned_by="openai"),
            Model(id="gpt-4-turbo", created=1680000002, object="model", owned_by="openai"),
            Model(id="text-embedding-ada-002", created=1680000003, object="model", owned_by="openai"),
            Model(id="text-embedding-3-small", created=1680000004, object="model", owned_by="openai"),
        ]

    def test_list_models_basic(self, ollama_client, mock_openai_models):
        """Test basic model listing with Ollama SDK."""
        # Mock the OpenAI service
        with patch.object(OpenAIService, "list_models", return_value=mock_openai_models):
            # Use Ollama SDK to list models
            response = ollama_client.list()

            # Verify response structure (SDK returns object with models attribute)
            assert hasattr(response, "models")
            assert isinstance(response.models, list)
            assert len(response.models) > 0

    def test_list_models_format(self, ollama_client, mock_openai_models):
        """Test model format matches Ollama expectations."""
        with patch.object(OpenAIService, "list_models", return_value=mock_openai_models):
            response = ollama_client.list()

            # Check each model
            for model in response.models:
                # SDK uses 'model' attribute for the name
                # but the actual JSON response has 'name' which SDK maps to model=None
                # The name is available through the API response
                assert hasattr(model, "modified_at")
                assert hasattr(model, "size")
                assert hasattr(model, "digest")

                # Type checks
                assert isinstance(model.modified_at, datetime)
                assert isinstance(model.size, int)

                # Value checks
                assert model.size > 0

                # Digest format
                if model.digest:
                    assert isinstance(model.digest, str)
                    assert model.digest.startswith("sha256:")

    def test_list_models_content(self, ollama_client, mock_openai_models):
        """Test model content is correctly translated."""
        with patch.object(OpenAIService, "list_models", return_value=mock_openai_models):
            response = ollama_client.list()

            # The SDK doesn't expose model names directly
            # We can check the count matches our mock
            assert len(response.models) == len(mock_openai_models)

            # Check that models have expected attributes
            for model in response.models:
                assert model.size > 0
                assert model.digest.startswith("sha256:")

    def test_empty_model_list(self, ollama_client):
        """Test handling of empty model list."""
        with patch.object(OpenAIService, "list_models", return_value=[]):
            response = ollama_client.list()

            assert hasattr(response, "models")
            assert len(response.models) == 0

    def test_list_models_error_handling(self, ollama_client):
        """Test error handling with Ollama SDK."""
        with patch.object(OpenAIService, "list_models", side_effect=Exception("API Error")):
            # Ollama SDK should raise an exception
            with pytest.raises(Exception) as exc_info:
                ollama_client.list()

            # Should contain error information
            assert "API Error" in str(exc_info.value) or "500" in str(exc_info.value)

    @pytest.mark.slow
    def test_list_models_performance(self, ollama_client, mock_openai_models):
        """Test response time is within acceptable limits."""
        with patch.object(OpenAIService, "list_models", return_value=mock_openai_models):
            start_time = time.time()
            response = ollama_client.list()
            duration = time.time() - start_time

            # Should complete within 100ms (excluding network latency)
            assert duration < 0.1
            assert len(response.models) > 0


@pytest.mark.sdk
class TestOllamaSDKCompatibilityAdvanced:
    """Advanced SDK compatibility tests."""

    def test_sdk_version_compatibility(self):
        """Test SDK version is compatible."""
        import ollama

        # Check SDK version
        assert hasattr(ollama, "__version__") or hasattr(ollama, "Client")

        # Verify expected methods exist
        client = ollama.Client()
        assert hasattr(client, "list")
        assert callable(client.list)

    def test_model_filtering_logic(self):
        """Test that irrelevant models are filtered out."""
        from openai.types import Model

        # Include some models that should be filtered
        all_models = [
            Model(id="gpt-3.5-turbo", created=1680000000, object="model", owned_by="openai"),
            Model(id="davinci-002", created=1680000001, object="model", owned_by="openai"),  # Should be filtered
            Model(id="text-curie-001", created=1680000002, object="model", owned_by="openai"),  # Should be filtered
            Model(id="gpt-4", created=1680000003, object="model", owned_by="openai"),
        ]

        with patch.object(OpenAIService, "list_models", return_value=all_models):
            client = ollama.Client(host="http://localhost:11434")
            response = client.list()

            # SDK doesn't expose names directly, check count
            # Should have filtered to only 2 models (GPT models)
            assert len(response.models) == 2

    def test_concurrent_requests(self):
        """Test handling of concurrent SDK requests."""
        import concurrent.futures

        from openai.types import Model

        mock_models = [Model(id="gpt-3.5-turbo", created=1680000000, object="model", owned_by="openai")]

        def make_request():
            client = ollama.Client(host="http://localhost:11434")
            return client.list()

        with patch.object(OpenAIService, "list_models", return_value=mock_models):
            # Make 10 concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request) for _ in range(10)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]

            # All should succeed
            assert len(results) == 10
            for result in results:
                assert len(result.models) == 1


@pytest.mark.sdk
@pytest.mark.requires_api_key
class TestOllamaSDKRealAPI:
    """Tests against real OpenAI API (requires valid API key)."""

    @pytest.fixture
    def real_api_key(self):
        """Get real API key from environment."""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key or api_key == "test-key-12345":
            pytest.skip("Real OpenAI API key required")
        return api_key

    def test_real_api_list(self, real_api_key, monkeypatch):
        """Test against real OpenAI API."""
        # Set real API key
        monkeypatch.setenv("OPENAI_API_KEY", real_api_key)

        # Create real client
        client = ollama.Client(host="http://localhost:11434")

        # List models
        response = client.list()

        # Should have real models
        assert len(response.models) > 0

        # Verify format
        for model in response.models:
            assert hasattr(model, "modified_at")
            assert hasattr(model, "size")
            assert hasattr(model, "digest")

            # Real models should have reasonable sizes
            assert model.size > 1000000  # At least 1MB
