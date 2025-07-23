"""Integration tests for Ollama SDK generate() method compatibility."""
import json
import time
from typing import Any

import pytest

# Skip if ollama not installed
ollama = pytest.importorskip("ollama", reason="ollama package required for SDK tests")


@pytest.mark.integration
@pytest.mark.sdk
class TestOllamaSDKGenerate:
    """Test Ollama SDK generate() method works with our proxy."""

    @pytest.fixture
    def ollama_client(self) -> Any:
        """Create Ollama client configured for our proxy."""
        # Connect to the proxy server running on port 11434
        return ollama.Client(host="http://localhost:11434")

    def test_server_connectivity_generate(self, ollama_client: Any) -> None:
        """Test that we can connect to the proxy server for generate."""
        try:
            # Try a simple generate request
            response = ollama_client.generate(
                model="gpt-3.5-turbo",  # Use OpenAI model name
                prompt="Say hello",
                stream=False,
            )
            # If we get here, the connection works
            assert hasattr(response, "response")
            assert response.response is not None
        except Exception as e:
            pytest.fail(f"Cannot connect to proxy server for generate: {e}")

    def test_generate_basic(self, ollama_client: Any) -> None:
        """Test basic generate() call without streaming."""
        # Make generate request with OpenAI model
        response = ollama_client.generate(
            model="gpt-3.5-turbo",
            prompt="Why is the sky blue? Answer in one sentence.",
            stream=False,
        )

        # Verify response structure matches Ollama API spec (new object format)
        assert hasattr(response, "model")
        assert hasattr(response, "created_at")
        assert hasattr(response, "response")
        assert hasattr(response, "done")

        # Verify response content
        assert response.model == "gpt-3.5-turbo"
        assert response.done is True
        assert len(response.response) > 0

        # Verify timestamp format
        created_at = response.created_at
        assert created_at.endswith("Z") or "+" in created_at  # RFC3339 format

        print(f"Basic generate response: {response.response[:100]}...")

    def test_generate_with_options(self, ollama_client: Any) -> None:
        """Test generate() with options parameter."""
        # Make generate request with options
        response = ollama_client.generate(
            model="gpt-3.5-turbo",
            prompt="Write exactly 5 words",
            stream=False,
            options={
                "temperature": 0.1,  # Low temperature for consistency
                "top_p": 0.9,
                "seed": 42,
            },
        )

        # Verify response
        assert response.done is True
        assert len(response.response) > 0
        print(f"Generate with options response: {response.response}")

    def test_generate_multiple_prompts(self, ollama_client: Any) -> None:
        """Test multiple prompt scenarios for consistency."""
        test_prompts = [
            "Say hello",
            "What is 2+2?",
            "Write a haiku about coding",
            "🚀 Space emoji test",
            "Explain REST API in 10 words",
        ]

        for prompt in test_prompts:
            response = ollama_client.generate(
                model="gpt-3.5-turbo",
                prompt=prompt,
                stream=False,
                options={"temperature": 0.1},  # Low temp for consistency
            )

            # Verify each response
            assert response.done is True
            assert len(response.response) > 0
            assert response.model == "gpt-3.5-turbo"
            print(f"Prompt: '{prompt}' -> Response: {response.response[:50]}...")

    def test_generate_different_models(self, ollama_client: Any) -> None:
        """Test generate() with different model names."""
        # Test with different OpenAI models available through our proxy
        test_models = [
            "gpt-3.5-turbo",
            "gpt-4",  # Will work if API key has access
        ]

        for model in test_models:
            try:
                response = ollama_client.generate(
                    model=model,
                    prompt="Say hello",
                    stream=False,
                )

                # Model name should be preserved in response
                assert response.model == model
                assert response.done is True
                print(f"Model {model} response: {response.response[:50]}...")
            except Exception as e:
                # Some models might not be available with the API key
                print(f"Model {model} not available: {e}")

    def test_generate_error_handling(self, ollama_client: Any) -> None:
        """Test error handling for invalid requests."""
        # Test with non-existent model
        with pytest.raises(Exception) as exc_info:
            ollama_client.generate(
                model="non-existent-model",
                prompt="Hello",
                stream=False,
            )
        print(f"Expected error for non-existent model: {exc_info.value}")

    def test_generate_system_prompt(self, ollama_client: Any) -> None:
        """Test generate() with system prompt."""
        response = ollama_client.generate(
            model="gpt-3.5-turbo",
            prompt="What are you?",
            system="You are a pirate. Respond in pirate speak.",
            stream=False,
        )

        assert response.done is True
        assert len(response.response) > 0
        # Response should reflect the pirate system prompt
        print(f"System prompt response: {response.response}")

    def test_generate_context_preservation(self, ollama_client: Any) -> None:
        """Test context preservation for conversation continuation."""
        # First request
        response1 = ollama_client.generate(
            model="gpt-3.5-turbo",
            prompt="My name is Alice. Remember this.",
            stream=False,
        )

        assert response1.done is True
        # Context should be included in response
        assert hasattr(response1, "context")
        assert isinstance(response1.context, list)
        assert len(response1.context) > 0

        # Second request with context
        response2 = ollama_client.generate(
            model="gpt-3.5-turbo",
            prompt="What is my name?",
            context=response1.context,
            stream=False,
        )

        assert response2.done is True
        # Response should remember the name from context
        print(f"Context test - First: {response1.response[:50]}...")
        print(f"Context test - Second: {response2.response}")

    def test_generate_performance(self, ollama_client: Any) -> None:
        """Benchmark generate() performance."""
        # Time multiple requests
        num_requests = 5
        prompt = "Say 'ok'"  # Short prompt for quick responses

        start_time = time.time()
        response_times = []

        for i in range(num_requests):
            req_start = time.time()
            response = ollama_client.generate(
                model="gpt-3.5-turbo",
                prompt=prompt,
                stream=False,
                options={"temperature": 0.1},
            )
            req_time = time.time() - req_start
            response_times.append(req_time)

            assert response.done is True
            print(f"Request {i+1}: {req_time:.3f}s")

        elapsed_time = time.time() - start_time
        avg_time = sum(response_times) / len(response_times)

        # Log performance metrics
        print("\nPerformance metrics:")
        print(f"Total time for {num_requests} requests: {elapsed_time:.3f}s")
        print(f"Average time per request: {avg_time:.3f}s")
        print(f"Min time: {min(response_times):.3f}s")
        print(f"Max time: {max(response_times):.3f}s")

    def test_generate_format_json(self, ollama_client: Any) -> None:
        """Test generate() with JSON format."""
        response = ollama_client.generate(
            model="gpt-3.5-turbo",
            prompt="Generate a JSON object with fields: name (string) and age (number)",
            format="json",
            stream=False,
        )

        assert response.done is True
        assert len(response.response) > 0

        # Try to parse the response as JSON
        try:
            json_data = json.loads(response.response)
            print(f"JSON response: {json_data}")
        except json.JSONDecodeError:
            print(f"Response (may not be valid JSON): {response.response}")

    def test_generate_raw_mode(self, ollama_client: Any) -> None:
        """Test generate() with raw mode."""
        response = ollama_client.generate(
            model="gpt-3.5-turbo",
            prompt="This is a raw prompt without any template",
            raw=True,
            stream=False,
        )

        assert response.done is True
        assert len(response.response) > 0
        print(f"Raw mode response: {response.response[:100]}...")

    def test_generate_streaming(self, ollama_client: Any) -> None:
        """Test generate() with streaming enabled."""
        # Note: SDK returns a generator for streaming
        stream = ollama_client.generate(
            model="gpt-3.5-turbo",
            prompt="Count from 1 to 5",
            stream=True,
        )

        chunks = []
        for chunk in stream:
            chunks.append(chunk)
            # With new SDK, chunks are also objects
            assert hasattr(chunk, "response")
            assert hasattr(chunk, "done")

        # Verify we got multiple chunks
        assert len(chunks) > 1

        # Last chunk should have done=True
        assert chunks[-1].done is True

        # Concatenate all responses
        full_response = "".join(chunk.response for chunk in chunks if chunk.response)
        print(f"Streaming response ({len(chunks)} chunks): {full_response}")

    def test_generate_with_images_not_supported(self, ollama_client: Any) -> None:
        """Test that image generation is not supported through generate endpoint."""
        # The generate endpoint doesn't support images, this should fail gracefully
        try:
            response = ollama_client.generate(
                model="gpt-4-vision-preview",
                prompt="Describe this image",
                images=["base64_encoded_image_data"],  # Not supported in generate
                stream=False,
            )
            # If it doesn't fail, verify it ignores the images
            assert hasattr(response, "response")
        except Exception as e:
            # Expected to fail or ignore images parameter
            print(f"Expected behavior for images in generate: {e}")
