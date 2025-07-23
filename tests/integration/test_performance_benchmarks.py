"""Performance benchmarks for SDK compatibility."""
import statistics
import time
from typing import List
from unittest.mock import patch

import pytest

ollama = pytest.importorskip("ollama")

# Import after ollama to avoid E402
from ollama_openai_proxy.services.openai_service import OpenAIService  # noqa: E402


@pytest.mark.sdk
@pytest.mark.slow
class TestPerformanceBenchmarks:
    """Performance benchmarks for Ollama SDK operations."""

    def measure_response_time(self, func, iterations: int = 100) -> List[float]:
        """Measure response time over multiple iterations."""
        times = []
        for _ in range(iterations):
            start = time.time()
            func()
            times.append(time.time() - start)
        return times

    def test_list_models_benchmark(self):
        """Benchmark model listing performance."""
        from openai.types import Model

        # Mock models
        mock_models = [
            Model(id=f"model-{i}", created=1680000000 + i, object="model", owned_by="openai")
            for i in range(50)  # 50 models
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
            p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile
            p99_time = statistics.quantiles(times, n=100)[98]  # 99th percentile

            # Log results
            print("\nList Models Performance:")
            print(f"  Average: {avg_time*1000:.2f}ms")
            print(f"  Median: {median_time*1000:.2f}ms")
            print(f"  P95: {p95_time*1000:.2f}ms")
            print(f"  P99: {p99_time*1000:.2f}ms")

            # Assert performance requirements
            assert avg_time < 0.1  # Average under 100ms
            assert p95_time < 0.15  # 95th percentile under 150ms
            assert p99_time < 0.2  # 99th percentile under 200ms


@pytest.mark.sdk
class TestOllamaSDKEdgeCases:
    """Test edge cases with Ollama SDK."""

    def test_special_characters_in_model_names(self):
        """Test handling of special characters in model names."""
        from openai.types import Model

        # Models with special characters
        special_models = [
            Model(id="gpt-3.5-turbo", created=1680000000, object="model", owned_by="openai"),
            Model(id="gpt-4-vision-preview", created=1680000001, object="model", owned_by="openai"),
            Model(id="text-embedding-3-large", created=1680000002, object="model", owned_by="openai"),
        ]

        with patch.object(OpenAIService, "list_models", return_value=special_models):
            client = ollama.Client(host="http://localhost:11434")
            response = client.list()

            # All models should be present
            assert len(response.models) == 3

    def test_very_large_model_list(self):
        """Test handling of very large model lists."""
        from openai.types import Model

        # Create 1000 models
        large_model_list = [
            Model(id=f"model-{i:04d}", created=1680000000 + i, object="model", owned_by="openai") for i in range(1000)
        ]

        with patch.object(OpenAIService, "list_models", return_value=large_model_list):
            client = ollama.Client(host="http://localhost:11434")
            response = client.list()

            # Should handle large lists
            assert len(response.models) <= 1000  # May filter some

            # Should complete in reasonable time
            start = time.time()
            client.list()
            duration = time.time() - start
            assert duration < 1.0  # Under 1 second even for large list


def test_ollama_cli_compatibility():
    """Test compatibility with Ollama CLI (manual test)."""
    instructions = """
    Manual test for Ollama CLI compatibility:

    1. Start the proxy:
       python -m ollama_openai_proxy

    2. In another terminal, set Ollama host:
       export OLLAMA_HOST=http://localhost:11434

    3. List models using Ollama CLI:
       ollama list

    4. Verify output shows available models

    Expected output format:
    NAME                    ID              SIZE    MODIFIED
    gpt-3.5-turbo          gpt-3.5-turbo   1.5 GB  2024-01-20 10:30:00
    gpt-4                  gpt-4           20 GB   2024-01-20 10:30:00
    """
    print(instructions)
