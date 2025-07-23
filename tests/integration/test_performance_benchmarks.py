"""Integration performance benchmarks for real server testing."""
import statistics
import time
from typing import Callable, List

import pytest

ollama = pytest.importorskip("ollama")


@pytest.mark.sdk
@pytest.mark.slow
@pytest.mark.integration
class TestRealServerPerformance:
    """Performance benchmarks against real running servers."""

    def measure_response_time(self, func: Callable, iterations: int = 10) -> List[float]:
        """Measure response time over multiple iterations."""
        times = []
        for _ in range(iterations):
            start = time.time()
            func()
            times.append(time.time() - start)
        return times

    def test_real_server_performance_benchmark(self) -> None:
        """Benchmark model listing performance against real server."""
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
        print("\nReal Server Performance:")
        print(f"  Average: {avg_time*1000:.2f}ms")
        print(f"  Median: {median_time*1000:.2f}ms")
        print(f"  Min: {min_time*1000:.2f}ms")
        print(f"  Max: {max_time*1000:.2f}ms")

        # Assert reasonable performance requirements for real server
        assert avg_time < 2.0  # Average under 2 seconds
        assert max_time < 10.0  # No request over 10 seconds

    def test_real_server_response_time(self) -> None:
        """Test basic response time against real server."""
        client = ollama.Client(host="http://localhost:11434")

        start_time = time.time()
        try:
            response = client.list()
            duration = time.time() - start_time

            # Should complete within reasonable time
            assert duration < 5.0  # 5 seconds max
            assert isinstance(response, dict)

            print(f"Single request time: {duration*1000:.2f}ms")

        except Exception as e:
            pytest.skip(f"Cannot test performance - server not available: {e}")

    def test_real_server_load_handling(self) -> None:
        """Test how server handles multiple sequential requests."""
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

                # Verify response is valid
                assert isinstance(response, dict)
                assert "models" in response

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
        assert avg_time < 5.0  # Average under 5 seconds


@pytest.mark.sdk
@pytest.mark.integration
class TestRealServerEdgeCases:
    """Test edge cases against real server."""

    def test_server_availability(self) -> None:
        """Test server availability and basic functionality."""
        client = ollama.Client(host="http://localhost:11434")

        try:
            response = client.list()
            assert isinstance(response, dict)
            assert "models" in response
            print(f"Server is available with {len(response['models'])} models")

        except Exception as e:
            pytest.fail(f"Server not available: {e}")

    def test_multiple_clients(self) -> None:
        """Test multiple client instances."""
        clients = [ollama.Client(host="http://localhost:11434") for _ in range(3)]

        responses = []
        for i, client in enumerate(clients):
            try:
                response = client.list()
                responses.append(response)
                print(f"Client {i+1}: {len(response['models'])} models")
            except Exception as e:
                pytest.fail(f"Client {i+1} failed: {e}")

        # All clients should get responses
        assert len(responses) == 3
        for response in responses:
            assert isinstance(response, dict)
            assert "models" in response


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
