"""Integration tests for Ollama SDK against our proxy server."""
import concurrent.futures
import os
import time
from datetime import datetime
from typing import Any

import pytest

# Import ollama if available
ollama = pytest.importorskip("ollama", reason="ollama package required for SDK tests")


@pytest.mark.sdk
@pytest.mark.integration
class TestOllamaSDKIntegration:
    """Test Ollama SDK against our proxy server."""

    @pytest.fixture
    def ollama_client(self) -> Any:
        """Create Ollama client pointing to proxy server."""
        # Connect to the proxy server running on port 11434
        client = ollama.Client(host="http://localhost:11434")
        return client

    def test_server_connectivity(self, ollama_client: Any) -> None:
        """Test that we can connect to the proxy server."""
        try:
            response = ollama_client.list()
            # If we get here, the connection works (new ollama 0.5+ format)
            assert hasattr(response, "models")
            assert isinstance(response.models, list)
        except Exception as e:
            pytest.fail(f"Cannot connect to proxy server: {e}")

    def test_list_models_real_server(self, ollama_client: Any) -> None:
        """Test model listing against our proxy server."""
        response = ollama_client.list()

        # Verify response structure (new ollama 0.5+ format)
        assert hasattr(response, "models")
        assert isinstance(response.models, list)

        # Our proxy translates OpenAI models to Ollama format
        # With valid API key, should return OpenAI models
        print(f"Found {len(response.models)} models from OpenAI via proxy")

    def test_model_format_real_server(self, ollama_client: Any) -> None:
        """Test that model format matches Ollama SDK expectations."""
        response = ollama_client.list()

        if len(response.models) > 0:
            for model in response.models:
                # Each model should have these attributes (new ollama 0.5+ format)
                assert hasattr(model, "modified_at")
                assert hasattr(model, "size")
                assert hasattr(model, "digest")
                assert hasattr(model, "model")

                # Type checks
                assert isinstance(model.modified_at, datetime)
                assert isinstance(model.size, int)
                assert model.size > 0

                # Digest should be a valid sha256 hash if present
                if model.digest:
                    assert isinstance(model.digest, str)
                    assert len(model.digest) > 10  # Some reasonable length
        else:
            pytest.skip("No models available for format testing")

    @pytest.mark.slow
    def test_performance_real_server(self, ollama_client: Any) -> None:
        """Test response time against our proxy server."""
        start_time = time.time()
        response = ollama_client.list()
        duration = time.time() - start_time

        # Should complete within reasonable time (including OpenAI API call)
        assert duration < 10.0  # 10 seconds max for OpenAI API call
        assert hasattr(response, "models")

        print(f"Response time: {duration*1000:.2f}ms")

    def test_concurrent_requests_real_server(self, ollama_client: Any) -> None:
        """Test concurrent requests against our proxy server."""

        def make_request() -> Any:
            client = ollama.Client(host="http://localhost:11434")
            return client.list()

        # Make 5 concurrent requests (keep it reasonable for CI)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = []

            for future in concurrent.futures.as_completed(futures, timeout=30):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    pytest.fail(f"Concurrent request failed: {e}")

        # All requests should succeed
        assert len(results) == 5
        for result in results:
            assert hasattr(result, "models")
            assert isinstance(result.models, list)

    def test_error_handling_real_server(self, ollama_client: Any) -> None:
        """Test error handling with invalid endpoints."""
        # Test with invalid client to trigger error
        invalid_client = ollama.Client(host="http://localhost:9999")

        with pytest.raises((ConnectionError, OSError, Exception)):
            invalid_client.list()


@pytest.mark.sdk
class TestOllamaSDKCompatibility:
    """Test SDK compatibility without server dependency."""

    def test_sdk_version_compatibility(self) -> None:
        """Test SDK version is compatible."""
        import ollama

        # Check SDK has expected interface
        assert hasattr(ollama, "Client")

        # Verify expected methods exist
        client = ollama.Client()
        assert hasattr(client, "list")
        assert callable(client.list)

    def test_client_instantiation(self) -> None:
        """Test client can be created with different configurations."""
        # Default client
        client1 = ollama.Client()
        assert client1 is not None

        # Client with specific host
        client2 = ollama.Client(host="http://localhost:11434")
        assert client2 is not None

        # Client with timeout
        client3 = ollama.Client(host="http://localhost:11434", timeout=30)
        assert client3 is not None


@pytest.mark.sdk
@pytest.mark.requires_api_key
class TestOllamaSDKWithRealAPI:
    """Tests with real OpenAI API (requires valid API key)."""

    @pytest.fixture
    def real_api_key(self) -> Any:
        """Get real API key from environment."""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key or api_key == "test-key-12345":
            pytest.skip("Real OpenAI API key required")
        return api_key

    def test_real_api_integration(self, real_api_key: str, monkeypatch: Any) -> None:
        """Test integration with real OpenAI API."""
        # Set real API key
        monkeypatch.setenv("OPENAI_API_KEY", real_api_key)

        # Create client
        client = ollama.Client(host="http://localhost:11434")

        # List models - should get OpenAI models via proxy
        response = client.list()

        # Should have models from OpenAI
        assert len(response.models) > 0

        print(f"Real API returned {len(response.models)} models")

        # Verify format
        for model in response.models:
            assert hasattr(model, "modified_at")
            assert hasattr(model, "size")
            assert hasattr(model, "digest")

            # Models should have reasonable properties
            assert isinstance(model.size, int)
            assert model.size > 0
