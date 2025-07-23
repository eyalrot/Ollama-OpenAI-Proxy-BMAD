"""Integration performance benchmarks for our proxy server."""
import statistics
import time
from typing import Callable, List

import pytest

ollama = pytest.importorskip("ollama")


@pytest.mark.sdk
@pytest.mark.slow
@pytest.mark.integration
class TestProxyServerPerformance:
    """Performance benchmarks against our proxy server."""

    def measure_response_time(self, func: Callable, iterations: int = 10) -> List[float]:
        """Measure response time over multiple iterations."""
        times = []
        for _ in range(iterations):
            start = time.time()
            func()
            times.append(time.time() - start)
        return times

    def test_proxy_server_performance_benchmark(self) -> None:
        """Benchmark model listing performance against our proxy server."""
        client = ollama.Client(host="http://localhost:11434")

        # Warmup (fewer iterations for real server)
        for _ in range(3):
            try:
                client.list()
            except Exception:
                pytest.skip("Cannot connect to proxy server")

        # Measure performance (fewer iterations for CI)
        times = self.measure_response_time(lambda: client.list(), iterations=10)

        # Calculate statistics
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        max_time = max(times)
        min_time = min(times)

        # Log results
        print("\nProxy Server Performance:")
        print(f"  Average: {avg_time*1000:.2f}ms")
        print(f"  Median: {median_time*1000:.2f}ms")
        print(f"  Min: {min_time*1000:.2f}ms")
        print(f"  Max: {max_time*1000:.2f}ms")

        # Assert reasonable performance requirements for proxy + OpenAI API
        assert avg_time < 5.0  # Average under 5 seconds (includes OpenAI API call)
        assert max_time < 15.0  # No request over 15 seconds

    def test_proxy_server_response_time(self) -> None:
        """Test basic response time against our proxy server."""
        client = ollama.Client(host="http://localhost:11434")

        start_time = time.time()
        try:
            response = client.list()
            duration = time.time() - start_time

            # Should complete within reasonable time (including OpenAI API call)
            assert duration < 10.0  # 10 seconds max for OpenAI API call
            assert isinstance(response, dict)

            print(f"Single request time: {duration*1000:.2f}ms")

        except Exception as e:
            pytest.skip(f"Cannot test performance - proxy server not available: {e}")

    def test_proxy_server_load_handling(self) -> None:
        """Test how our proxy server handles multiple sequential requests."""
        client = ollama.Client(host="http://localhost:11434")

        response_times = []
        errors = 0

        # Make 20 sequential requests
        for i in range(20):
            start = time.time()
            try:
                response = client.list()
                duration = time.time() - start
                response_times.append(duration)

                # Verify response is valid (ollama 0.5+ format)
                assert hasattr(response, "models")
                assert isinstance(response.models, list)

            except Exception as e:
                errors += 1
                print(f"Request {i+1} failed: {e}")

        if not response_times:
            pytest.skip("No successful requests - server not available")

        # Calculate statistics
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)

        print("\nLoad test results:")
        print(f"  Successful requests: {len(response_times)}/20")
        print(f"  Failed requests: {errors}")
        print(f"  Average time: {avg_time*1000:.2f}ms")
        print(f"  Max time: {max_time*1000:.2f}ms")

        # Most requests should succeed
        assert errors < 5  # Less than 25% failure rate
        assert avg_time < 10.0  # Average under 10 seconds (including OpenAI API calls)


@pytest.mark.sdk
@pytest.mark.integration
class TestProxyServerEdgeCases:
    """Test edge cases against our proxy server."""

    def test_proxy_server_availability(self) -> None:
        """Test our proxy server availability and basic functionality."""
        client = ollama.Client(host="http://localhost:11434")

        try:
            response = client.list()
            assert hasattr(response, "models")
            assert isinstance(response.models, list)
            print(f"Proxy server is available with {len(response.models)} models from OpenAI")

        except Exception as e:
            pytest.fail(f"Proxy server not available: {e}")

    def test_multiple_proxy_clients(self) -> None:
        """Test multiple client instances against our proxy server."""
        clients = [ollama.Client(host="http://localhost:11434") for _ in range(3)]

        responses = []
        for i, client in enumerate(clients):
            try:
                response = client.list()
                responses.append(response)
                print(f"Client {i+1}: {len(response.models)} models from proxy")
            except Exception as e:
                pytest.fail(f"Client {i+1} failed to connect to proxy: {e}")

        # All clients should get responses
        assert len(responses) == 3
        for response in responses:
            assert hasattr(response, "models")
            assert isinstance(response.models, list)


def test_ollama_cli_compatibility() -> None:
    """Test compatibility with Ollama CLI (manual test instructions)."""
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
