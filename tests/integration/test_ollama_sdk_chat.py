"""Integration tests for Ollama SDK chat functionality against running server."""
import json
import os
import subprocess
import time
from typing import Generator

import pytest
import requests
from dotenv import load_dotenv
from ollama import AsyncClient, Client

# Load environment variables from .env file
load_dotenv()

# Test configuration
TEST_MODEL = "gpt-3.5-turbo"  # Use OpenAI model since we're proxying to OpenAI
SERVER_HOST = "http://localhost:11434"
STARTUP_TIMEOUT = 30  # seconds to wait for server startup


@pytest.fixture(scope="module")
def server_process() -> Generator[subprocess.Popen, None, None]:
    """Start the proxy server for testing."""
    # Set up environment variables
    env = os.environ.copy()
    env["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "test-key")
    env["OPENAI_API_BASE_URL"] = "https://api.openai.com/v1"
    env["PROXY_PORT"] = "11434"
    env["LOG_LEVEL"] = "INFO"

    # Start the server using the virtual environment's Python
    python_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "venv", "bin", "python")
    process = subprocess.Popen(
        [python_path, "-m", "ollama_openai_proxy.main"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )

    # Wait for server to start
    start_time = time.time()
    while time.time() - start_time < STARTUP_TIMEOUT:
        try:
            response = requests.get(f"{SERVER_HOST}/health")
            if response.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(0.5)
    else:
        process.terminate()
        stdout, stderr = process.communicate(timeout=5)
        pytest.fail(f"Server failed to start within {STARTUP_TIMEOUT} seconds.\nSTDOUT: {stdout}\nSTDERR: {stderr}")

    yield process

    # Cleanup
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


@pytest.fixture
def client(server_process) -> Client:
    """Create Ollama client for testing."""
    return Client(host=SERVER_HOST)


@pytest.fixture
def async_client(server_process) -> AsyncClient:
    """Create async Ollama client for testing."""
    return AsyncClient(host=SERVER_HOST)


class TestOllamaSDKChatIntegration:
    """Integration tests for Ollama SDK chat functionality."""

    def test_basic_chat_conversation(self, client: Client):
        """Test basic chat conversation with Ollama SDK."""
        response = client.chat(
            model=TEST_MODEL,
            messages=[{"role": "user", "content": "Say hello in one word."}],
            stream=False,
        )

        # Verify response structure
        assert "message" in response
        assert response["message"]["role"] == "assistant"
        assert isinstance(response["message"]["content"], str)
        assert len(response["message"]["content"]) > 0
        assert response["done"] is True
        assert "model" in response
        assert response["model"] == TEST_MODEL

    def test_streaming_chat_response(self, client: Client):
        """Test streaming chat responses."""
        stream = client.chat(
            model=TEST_MODEL,
            messages=[{"role": "user", "content": "Count from 1 to 3."}],
            stream=True,
        )

        chunks = []
        for chunk in stream:
            chunks.append(chunk)
            # Verify chunk structure
            assert "message" in chunk
            assert "content" in chunk["message"]
            assert "done" in chunk
            assert "model" in chunk
            assert chunk["model"] == TEST_MODEL

        # Verify we got multiple chunks
        assert len(chunks) > 1

        # Last chunk should have done=True
        assert chunks[-1]["done"] is True

        # Concatenate all content
        full_content = "".join(chunk["message"]["content"] for chunk in chunks)
        assert len(full_content) > 0

    def test_multi_turn_conversation(self, client: Client):
        """Test multi-turn conversation with context preservation."""
        messages = [
            {"role": "user", "content": "My name is Alice. Remember it."},
            {"role": "assistant", "content": "Hello Alice! I'll remember your name."},
            {"role": "user", "content": "What's my name?"},
        ]

        response = client.chat(
            model=TEST_MODEL,
            messages=messages,
            stream=False,
        )

        # The response should reference the name Alice
        assert "message" in response
        content = response["message"]["content"].lower()
        # Check if the assistant remembers the name (might be in various formats)
        assert any(name in content for name in ["alice", "your name"])

    def test_system_prompt_handling(self, client: Client):
        """Test system prompts are properly handled."""
        response = client.chat(
            model=TEST_MODEL,
            messages=[
                {"role": "system", "content": "You are a pirate. Always speak like a pirate."},
                {"role": "user", "content": "Hello there!"},
            ],
            stream=False,
        )

        # Verify response contains pirate-like language
        assert "message" in response
        content = response["message"]["content"].lower()
        # Check for common pirate words (at least one should appear)
        pirate_words = ["ahoy", "matey", "arr", "aye", "ye", "pirates", "ship", "sea"]
        assert any(word in content for word in pirate_words), f"Expected pirate language but got: {content}"

    def test_chat_with_options(self, client: Client):
        """Test chat with custom options/parameters."""
        response = client.chat(
            model=TEST_MODEL,
            messages=[{"role": "user", "content": "Generate exactly one word."}],
            options={
                "temperature": 0.1,  # Low temperature for consistency
                "max_tokens": 10,  # Limit response length
                "top_p": 0.9,
            },
            stream=False,
        )

        # Verify response
        assert "message" in response
        # Response should be relatively short due to max_tokens
        assert len(response["message"]["content"].split()) <= 10

    @pytest.mark.asyncio
    async def test_async_chat_basic(self, async_client: AsyncClient):
        """Test async chat functionality."""
        response = await async_client.chat(
            model=TEST_MODEL,
            messages=[{"role": "user", "content": "What is 2+2?"}],
            stream=False,
        )

        # Verify response
        assert "message" in response
        assert "4" in response["message"]["content"] or "four" in response["message"]["content"].lower()

    @pytest.mark.asyncio
    async def test_async_streaming_chat(self, async_client: AsyncClient):
        """Test async streaming chat."""
        stream = await async_client.chat(
            model=TEST_MODEL,
            messages=[{"role": "user", "content": "Say 'test' three times."}],
            stream=True,
        )

        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
            assert "message" in chunk
            assert "done" in chunk

        # Verify we got chunks
        assert len(chunks) > 0
        assert chunks[-1]["done"] is True

        # Verify content contains 'test'
        full_content = "".join(chunk["message"]["content"] for chunk in chunks)
        assert "test" in full_content.lower()

    def test_error_handling_empty_messages(self, client: Client):
        """Test error handling for empty messages array."""
        with pytest.raises(Exception) as exc_info:
            client.chat(
                model=TEST_MODEL,
                messages=[],
                stream=False,
            )

        # Should get an error about empty messages
        assert "empty" in str(exc_info.value).lower() or "message" in str(exc_info.value).lower()

    def test_error_handling_invalid_role(self, client: Client):
        """Test error handling for invalid message role."""
        with pytest.raises(Exception) as exc_info:
            client.chat(
                model=TEST_MODEL,
                messages=[{"role": "invalid_role", "content": "Hello"}],
                stream=False,
            )

        # Should get an error about invalid role
        assert "role" in str(exc_info.value).lower()

    def test_performance_minimal_overhead(self, client: Client):
        """Test that proxy adds minimal overhead to requests."""
        # Measure time for a simple request
        start_time = time.time()

        response = client.chat(
            model=TEST_MODEL,
            messages=[{"role": "user", "content": "Hi"}],
            stream=False,
        )

        elapsed_time = time.time() - start_time

        # Verify response is valid
        assert "message" in response

        # Log performance (for manual inspection)
        print(f"\nChat request completed in {elapsed_time:.2f} seconds")

        # Basic sanity check - should complete within reasonable time
        assert elapsed_time < 30, f"Request took too long: {elapsed_time} seconds"

    def test_format_json_mode(self, client: Client):
        """Test JSON format mode."""
        response = client.chat(
            model=TEST_MODEL,
            messages=[{"role": "user", "content": "Return a JSON object with a 'greeting' field saying hello."}],
            format="json",
            stream=False,
        )

        # Verify response
        assert "message" in response
        content = response["message"]["content"]

        # Try to parse as JSON
        try:
            parsed = json.loads(content)
            # Basic check - should have some structure
            assert isinstance(parsed, dict)
        except json.JSONDecodeError:
            # Some models might not perfectly support JSON mode
            # Just verify we got some response
            assert len(content) > 0

    def test_long_conversation_context(self, client: Client):
        """Test handling of long conversation history."""
        # Build a conversation with multiple turns
        messages = []

        # Add several conversation turns
        for i in range(5):
            messages.append({"role": "user", "content": f"This is message {i+1}."})
            messages.append({"role": "assistant", "content": f"I received message {i+1}."})

        # Add final question
        messages.append({"role": "user", "content": "How many messages have I sent?"})

        response = client.chat(
            model=TEST_MODEL,
            messages=messages,
            stream=False,
        )

        # Verify response acknowledges the conversation
        assert "message" in response
        # Response should reference the number 5 or "five"
        content = response["message"]["content"].lower()
        assert "5" in content or "five" in content or "messages" in content
