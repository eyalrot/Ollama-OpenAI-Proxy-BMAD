"""Unit tests for Ollama SDK compatibility with mocked services."""
import statistics
import time
from datetime import datetime
from typing import Any, Callable, List
from unittest.mock import patch

import pytest

# Import ollama if available
ollama = pytest.importorskip("ollama", reason="ollama package required for SDK tests")

# Import after ollama to avoid E402
from ollama_openai_proxy.services.openai_service import OpenAIService  # noqa: E402


@pytest.mark.sdk
class TestOllamaSDKMocked:
    """Test Ollama SDK with mocked OpenAI service."""

    @pytest.fixture
    def ollama_client(self) -> Any:
        """Create Ollama client for testing."""
        client = ollama.Client(host="http://localhost:11434")
        return client

    @pytest.fixture
    def mock_openai_models(self) -> List[Any]:
        """Mock OpenAI models for consistent testing."""
        from openai.types import Model

        return [
            Model(id="gpt-3.5-turbo", created=1680000000, object="model", owned_by="openai"),
            Model(id="gpt-4", created=1680000001, object="model", owned_by="openai"),
            Model(id="gpt-4-turbo", created=1680000002, object="model", owned_by="openai"),
            Model(id="text-embedding-ada-002", created=1680000003, object="model", owned_by="openai"),
            Model(id="text-embedding-3-small", created=1680000004, object="model", owned_by="openai"),
        ]

    def test_list_models_basic_mocked(self, ollama_client: Any, mock_openai_models: List[Any]) -> None:
        """Test basic model listing with mocked OpenAI service."""
        with patch.object(OpenAIService, "list_models", return_value=mock_openai_models):
            response = ollama_client.list()

            # Verify response structure
            assert isinstance(response, dict)
            assert "models" in response
            assert isinstance(response["models"], list)
            assert len(response["models"]) > 0

    def test_list_models_format_mocked(self, ollama_client: Any, mock_openai_models: List[Any]) -> None:
        """Test model format with mocked data."""
        with patch.object(OpenAIService, "list_models", return_value=mock_openai_models):
            response = ollama_client.list()

            # Check each model has expected attributes
            for model in response["models"]:
                assert hasattr(model, "modified_at")
                assert hasattr(model, "size")
                assert hasattr(model, "digest")
                assert isinstance(model.modified_at, datetime)
                assert isinstance(model.size, int)
                assert model.size > 0

    def test_list_models_content_mocked(self, ollama_client: Any, mock_openai_models: List[Any]) -> None:
        """Test model content with mocked data."""
        with patch.object(OpenAIService, "list_models", return_value=mock_openai_models):
            response = ollama_client.list()

            # Count should match our mock
            assert len(response["models"]) == len(mock_openai_models)

    def test_empty_model_list_mocked(self, ollama_client: Any) -> None:
        """Test handling of empty model list with mocking."""
        with patch.object(OpenAIService, "list_models", return_value=[]):
            response = ollama_client.list()

            assert isinstance(response, dict)
            assert "models" in response
            assert len(response["models"]) == 0

    def test_list_models_error_handling_mocked(self, ollama_client: Any) -> None:
        """Test error handling with mocked service."""
        with patch.object(OpenAIService, "list_models", side_effect=Exception("API Error")):
            with pytest.raises(Exception) as exc_info:
                ollama_client.list()

            assert "API Error" in str(exc_info.value) or "500" in str(exc_info.value)

    def test_special_characters_in_model_names_mocked(self, ollama_client: Any) -> None:
        """Test handling of special characters in model names."""
        from openai.types import Model

        special_models = [
            Model(id="gpt-3.5-turbo", created=1680000000, object="model", owned_by="openai"),
            Model(id="gpt-4-vision-preview", created=1680000001, object="model", owned_by="openai"),
            Model(id="text-embedding-3-large", created=1680000002, object="model", owned_by="openai"),
        ]

        with patch.object(OpenAIService, "list_models", return_value=special_models):
            response = ollama_client.list()
            assert len(response["models"]) == 3

    def test_very_large_model_list_mocked(self, ollama_client: Any) -> None:
        """Test handling of very large model lists."""
        from openai.types import Model

        large_model_list = [
            Model(id=f"model-{i:04d}", created=1680000000 + i, object="model", owned_by="openai") for i in range(1000)
        ]

        with patch.object(OpenAIService, "list_models", return_value=large_model_list):
            response = ollama_client.list()
            assert len(response["models"]) <= 1000

    def test_model_filtering_logic_mocked(self, ollama_client: Any) -> None:
        """Test that irrelevant models are filtered out."""
        from openai.types import Model

        all_models = [
            Model(id="gpt-3.5-turbo", created=1680000000, object="model", owned_by="openai"),
            Model(id="davinci-002", created=1680000001, object="model", owned_by="openai"),
            Model(id="text-curie-001", created=1680000002, object="model", owned_by="openai"),
            Model(id="gpt-4", created=1680000003, object="model", owned_by="openai"),
        ]

        with patch.object(OpenAIService, "list_models", return_value=all_models):
            response = ollama_client.list()
            # Should filter to only GPT models
            assert len(response["models"]) == 2


@pytest.mark.sdk
@pytest.mark.slow
class TestOllamaSDKPerformanceMocked:
    """Performance tests with mocked services."""

    def measure_response_time(self, func: Callable, iterations: int = 100) -> List[float]:
        """Measure response time over multiple iterations."""
        times = []
        for _ in range(iterations):
            start = time.time()
            func()
            times.append(time.time() - start)
        return times

    def test_list_models_benchmark_mocked(self) -> None:
        """Benchmark model listing performance with mocked service."""
        from openai.types import Model

        mock_models = [
            Model(id=f"model-{i}", created=1680000000 + i, object="model", owned_by="openai") for i in range(50)
        ]

        with patch.object(OpenAIService, "list_models", return_value=mock_models):
            client = ollama.Client(host="http://localhost:11434")

            # Warmup
            for _ in range(10):
                client.list()

            # Measure
            times = self.measure_response_time(lambda: client.list(), iterations=100)

            # Calculate statistics
            avg_time = statistics.mean(times)
            median_time = statistics.median(times)
            p95_time = statistics.quantiles(times, n=20)[18]
            p99_time = statistics.quantiles(times, n=100)[98]

            # Log results
            print("\nList Models Performance (Mocked):")
            print(f"  Average: {avg_time*1000:.2f}ms")
            print(f"  Median: {median_time*1000:.2f}ms")
            print(f"  P95: {p95_time*1000:.2f}ms")
            print(f"  P99: {p99_time*1000:.2f}ms")

            # Assert performance requirements
            assert avg_time < 0.1
            assert p95_time < 0.15
            assert p99_time < 0.2

    def test_list_models_performance_mocked(self) -> None:
        """Test response time with mocked service."""
        from openai.types import Model

        mock_models = [Model(id="gpt-3.5-turbo", created=1680000000, object="model", owned_by="openai")]

        with patch.object(OpenAIService, "list_models", return_value=mock_models):
            client = ollama.Client(host="http://localhost:11434")

            start_time = time.time()
            response = client.list()
            duration = time.time() - start_time

            assert duration < 0.1
            assert len(response["models"]) > 0
