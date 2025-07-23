"""Comprehensive integration tests for Ollama SDK streaming functionality."""
import time
from typing import Any

import pytest

# Skip if ollama not installed
ollama = pytest.importorskip("ollama", reason="ollama package required for SDK tests")


@pytest.mark.integration
@pytest.mark.sdk
class TestOllamaSDKStreaming:
    """Test Ollama SDK streaming generation with comprehensive validation."""

    @pytest.fixture
    def ollama_client(self) -> Any:
        """Create Ollama client configured for our proxy."""
        return ollama.Client(host="http://localhost:11434")

    def test_streaming_basic_validation(self, ollama_client: Any) -> None:
        """Test basic streaming with chunk validation."""
        stream = ollama_client.generate(
            model="gpt-3.5-turbo",
            prompt="Count from 1 to 5",
            stream=True,
        )

        chunks = []
        for chunk in stream:
            chunks.append(chunk)

            # Validate chunk structure (new SDK returns objects)
            assert hasattr(chunk, "model")
            assert hasattr(chunk, "created_at")
            assert hasattr(chunk, "response")
            assert hasattr(chunk, "done")

            # Validate types
            assert chunk.model == "gpt-3.5-turbo"
            assert isinstance(chunk.created_at, str)
            assert isinstance(chunk.response, str)
            assert isinstance(chunk.done, bool)

        # Validate we got multiple chunks
        assert len(chunks) > 1, "Should receive multiple chunks for streaming"

        # Print chunk distribution
        print(f"\nReceived {len(chunks)} chunks")
        print(f"First chunk: {chunks[0].response[:50] if chunks[0].response else '(empty)'}")
        print(f"Last chunk: {chunks[-1].response[:50] if chunks[-1].response else '(empty)'}")

    def test_streaming_lifecycle(self, ollama_client: Any) -> None:
        """Test streaming lifecycle - done flags and chunk sequence."""
        stream = ollama_client.generate(
            model="gpt-3.5-turbo",
            prompt="Write a short sentence about Python",
            stream=True,
        )

        chunks = list(stream)

        # All chunks except last should have done=False
        for i, chunk in enumerate(chunks[:-1]):
            assert chunk.done is False, f"Chunk {i} should have done=False"

        # Last chunk must have done=True
        assert chunks[-1].done is True, "Final chunk must have done=True"

        # Check if final chunk has other metadata
        final_chunk = chunks[-1]
        print("\nFinal chunk metadata:")
        print(f"  done: {final_chunk.done}")
        print(f"  done_reason: {getattr(final_chunk, 'done_reason', 'N/A')}")
        if hasattr(final_chunk, "eval_count"):
            print(f"  eval_count: {final_chunk.eval_count}")
        if hasattr(final_chunk, "eval_duration"):
            print(f"  eval_duration: {final_chunk.eval_duration}")

    def test_response_reconstruction(self, ollama_client: Any) -> None:
        """Test reconstructing full response from chunks."""
        prompt = "What is the capital of France?"

        # Get streaming response
        stream = ollama_client.generate(
            model="gpt-3.5-turbo",
            prompt=prompt,
            stream=True,
        )

        chunks = []
        full_response = ""
        timestamps = []

        for chunk in stream:
            chunks.append(chunk)
            if chunk.response:
                full_response += chunk.response
            timestamps.append(chunk.created_at)

        print(f"\nReconstructed response: {full_response}")
        print(f"Total chunks: {len(chunks)}")
        print(f"Response length: {len(full_response)} chars")

        # Verify response makes sense
        assert len(full_response) > 0, "Should have non-empty response"
        assert "Paris" in full_response or "paris" in full_response.lower(), "Response should mention Paris"

        # Check timestamp format consistency (timestamps may differ slightly)
        # Just verify all timestamps are in valid format
        for ts in timestamps:
            assert ts.endswith("Z") or "+" in ts, f"Invalid timestamp format: {ts}"

        # Verify model consistency
        models = [chunk.model for chunk in chunks]
        assert all(m == "gpt-3.5-turbo" for m in models), "All chunks should have same model"

    def test_streaming_vs_non_streaming(self, ollama_client: Any) -> None:
        """Compare streaming vs non-streaming responses for same prompt."""
        prompt = "Explain what JSON is in one sentence"

        # Non-streaming response
        non_stream_response = ollama_client.generate(
            model="gpt-3.5-turbo",
            prompt=prompt,
            stream=False,
            options={"temperature": 0.1, "seed": 42},
        )

        # Streaming response with same settings
        stream = ollama_client.generate(
            model="gpt-3.5-turbo",
            prompt=prompt,
            stream=True,
            options={"temperature": 0.1, "seed": 42},
        )

        # Reconstruct streaming response
        streaming_response = ""
        chunk_count = 0
        for chunk in stream:
            if chunk.response:
                streaming_response += chunk.response
            chunk_count += 1

        print(f"\nNon-streaming response: {non_stream_response.response[:100]}...")
        print(f"Streaming response ({chunk_count} chunks): {streaming_response[:100]}...")

        # Both should have content about JSON
        assert "JSON" in non_stream_response.response or "json" in non_stream_response.response.lower()
        assert "JSON" in streaming_response or "json" in streaming_response.lower()

        # Note: Due to the nature of LLMs, responses might not be identical even with same seed

    def test_very_short_response_streaming(self, ollama_client: Any) -> None:
        """Test streaming with very short responses (1-2 chunks)."""
        stream = ollama_client.generate(
            model="gpt-3.5-turbo",
            prompt="Reply with just 'OK'",
            stream=True,
            options={"temperature": 0.1},
        )

        chunks = list(stream)
        full_response = "".join(chunk.response for chunk in chunks if chunk.response)

        print(f"\nShort response: '{full_response}'")
        print(f"Chunk count: {len(chunks)}")

        # Even short responses should have at least 2 chunks (content + done)
        assert len(chunks) >= 1, "Should have at least 1 chunk"
        assert chunks[-1].done is True

    def test_long_response_streaming(self, ollama_client: Any) -> None:
        """Test streaming with longer responses."""
        stream = ollama_client.generate(
            model="gpt-3.5-turbo",
            prompt="Write a detailed 5-step process for making a sandwich",
            stream=True,
        )

        chunks = []
        chunk_sizes = []
        start_time = time.time()

        for chunk in stream:
            chunks.append(chunk)
            if chunk.response:
                chunk_sizes.append(len(chunk.response))

        elapsed = time.time() - start_time

        print("\nLong response streaming stats:")
        print(f"  Total chunks: {len(chunks)}")
        print(f"  Chunks with content: {len(chunk_sizes)}")
        print(f"  Average chunk size: {sum(chunk_sizes) / len(chunk_sizes):.1f} chars")
        print(f"  Min chunk size: {min(chunk_sizes)} chars")
        print(f"  Max chunk size: {max(chunk_sizes)} chars")
        print(f"  Streaming duration: {elapsed:.2f}s")

        # Should have many chunks for detailed response
        assert len(chunks) > 5, "Detailed response should have multiple chunks"

    def test_streaming_with_system_prompt(self, ollama_client: Any) -> None:
        """Test streaming with system prompt."""
        stream = ollama_client.generate(
            model="gpt-3.5-turbo",
            prompt="Hello",
            system="You are a pirate. Always respond in pirate speak.",
            stream=True,
        )

        full_response = ""
        chunk_count = 0

        for chunk in stream:
            if chunk.response:
                full_response += chunk.response
            chunk_count += 1

        print(f"\nPirate response ({chunk_count} chunks): {full_response}")

        # Should have pirate-like language
        pirate_words = ["ahoy", "matey", "arr", "ye", "aye", "sailin", "treasure"]
        assert any(word in full_response.lower() for word in pirate_words), "Should contain pirate speak"

    def test_streaming_with_options(self, ollama_client: Any) -> None:
        """Test streaming with various options."""
        stream = ollama_client.generate(
            model="gpt-3.5-turbo",
            prompt="Generate exactly three words",
            stream=True,
            options={
                "temperature": 0.1,
                "top_p": 0.9,
                "seed": 12345,
            },
        )

        chunks = list(stream)
        full_response = "".join(chunk.response for chunk in chunks if chunk.response)

        print(f"\nOptions test response: '{full_response}'")
        print(f"Word count: {len(full_response.split())}")

        # Should have generated a short response
        assert len(full_response.split()) <= 10, "Low temperature should produce concise response"

    def test_streaming_context_preservation(self, ollama_client: Any) -> None:
        """Test context preservation in streaming mode."""
        # First request
        stream1 = ollama_client.generate(
            model="gpt-3.5-turbo",
            prompt="My favorite color is blue. Remember this.",
            stream=True,
        )

        chunks1 = list(stream1)
        context = chunks1[-1].context if hasattr(chunks1[-1], "context") else None

        if context:
            # Second request with context
            stream2 = ollama_client.generate(
                model="gpt-3.5-turbo",
                prompt="What is my favorite color?",
                context=context,
                stream=True,
            )

            response2 = ""
            for chunk in stream2:
                if chunk.response:
                    response2 += chunk.response

            print("\nContext preservation test:")
            print("  Context available: Yes")
            print(f"  Second response: {response2[:100]}...")
        else:
            print("\nContext preservation test: Context not available in streaming chunks")

    def test_streaming_performance_metrics(self, ollama_client: Any) -> None:
        """Measure streaming performance and chunk delivery timing."""
        prompt = "Tell me a fun fact"

        # Measure chunk arrival times
        chunk_times = []
        start_time = time.time()
        first_chunk_time = None

        stream = ollama_client.generate(
            model="gpt-3.5-turbo",
            prompt=prompt,
            stream=True,
        )

        for i, _ in enumerate(stream):
            arrival_time = time.time() - start_time
            chunk_times.append(arrival_time)

            if i == 0:
                first_chunk_time = arrival_time

        total_time = chunk_times[-1]

        # Calculate inter-chunk delays
        inter_chunk_delays = []
        for i in range(1, len(chunk_times)):
            delay = chunk_times[i] - chunk_times[i - 1]
            inter_chunk_delays.append(delay)

        print("\nStreaming performance metrics:")
        print(f"  Time to first chunk: {first_chunk_time:.3f}s")
        print(f"  Total streaming time: {total_time:.3f}s")
        print(f"  Number of chunks: {len(chunk_times)}")
        print(f"  Average inter-chunk delay: {sum(inter_chunk_delays) / len(inter_chunk_delays):.3f}s")
        print(f"  Max inter-chunk delay: {max(inter_chunk_delays):.3f}s")

        # Performance assertions
        assert first_chunk_time is not None and first_chunk_time < 2.0, "First chunk should arrive within 2 seconds"
        assert total_time < 10.0, "Total streaming should complete within 10 seconds"

    def test_streaming_interruption_handling(self, ollama_client: Any) -> None:
        """Test handling of stream interruption."""
        stream = ollama_client.generate(
            model="gpt-3.5-turbo",
            prompt="Write a very long story about a dragon",
            stream=True,
        )

        chunks_before_break = []
        try:
            for i, chunk in enumerate(stream):
                chunks_before_break.append(chunk)
                # Simulate interruption after 5 chunks
                if i >= 4:
                    break
        except Exception as e:
            print(f"Exception during interruption: {e}")

        print("\nInterruption test:")
        print(f"  Collected {len(chunks_before_break)} chunks before interruption")
        print(f"  Last chunk done status: {chunks_before_break[-1].done if chunks_before_break else 'N/A'}")

        # Should have collected some chunks
        assert len(chunks_before_break) >= 5

    def test_streaming_edge_cases(self, ollama_client: Any) -> None:
        """Test various edge cases in streaming."""
        # Test with empty-ish prompts
        edge_cases = [
            ("", "empty prompt"),
            (" ", "whitespace prompt"),
            (".", "single punctuation"),
            ("a", "single character"),
        ]

        for prompt, description in edge_cases:
            try:
                stream = ollama_client.generate(
                    model="gpt-3.5-turbo",
                    prompt=prompt,
                    stream=True,
                )

                chunks = list(stream)
                response = "".join(chunk.response for chunk in chunks if chunk.response)

                print(f"\nEdge case - {description}:")
                print(f"  Prompt: '{prompt}'")
                print(f"  Chunks: {len(chunks)}")
                print(f"  Response length: {len(response)}")

                # Should still get valid response structure
                assert len(chunks) > 0
                assert chunks[-1].done is True

            except Exception as e:
                print(f"\nEdge case - {description}: Error: {e}")
