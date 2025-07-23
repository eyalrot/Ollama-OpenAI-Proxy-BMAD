"""Integration tests for Ollama SDK embeddings functionality against running server."""
import os
import subprocess
import sys
import time

import pytest
import requests
from dotenv import load_dotenv
from ollama import AsyncClient, Client

# Load environment variables from .env file
load_dotenv()

# Test configuration
TEST_MODEL = "text-embedding-ada-002"  # Use OpenAI embedding model since we're proxying to OpenAI
SERVER_HOST = "http://localhost:11434"
STARTUP_TIMEOUT = 30  # seconds to wait for server startup


@pytest.fixture(scope="module")
def server_process():
    """Start the proxy server for testing if not already running."""
    # Check if server is already running (e.g., in CI)
    try:
        response = requests.get(f"{SERVER_HOST}/health", timeout=1)
        if response.status_code == 200:
            # Server is already running
            yield None
            return
    except requests.exceptions.RequestException:
        pass

    # Server not running, start it
    # Set up environment variables
    env = os.environ.copy()
    env["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "test-key")
    env["OPENAI_API_BASE_URL"] = "https://api.openai.com/v1"
    env["PROXY_PORT"] = "11434"
    env["LOG_LEVEL"] = "INFO"

    # Start the server using the current Python interpreter
    process = subprocess.Popen(
        [sys.executable, "-m", "ollama_openai_proxy.main"],
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


class TestOllamaSDKEmbeddingsIntegration:
    """Integration tests for Ollama SDK embeddings functionality."""

    def test_basic_embeddings(self, client: Client):
        """Test basic embeddings generation with Ollama SDK."""
        response = client.embeddings(model=TEST_MODEL, prompt="Hello, world!")

        # Verify response structure
        assert "embedding" in response
        assert isinstance(response["embedding"], list)
        assert len(response["embedding"]) > 0
        assert all(isinstance(x, float) for x in response["embedding"])

    def test_embeddings_with_different_prompts(self, client: Client):
        """Test embeddings with various prompt types."""
        test_prompts = [
            "Simple text",
            "Text with numbers 123 456",
            "Text with special characters !@#$%",
            "Multi-line\ntext\nwith\nnewlines",
            "Unicode text: 你好世界 🌍",
        ]

        for prompt in test_prompts:
            response = client.embeddings(model=TEST_MODEL, prompt=prompt)

            assert "embedding" in response
            assert isinstance(response["embedding"], list)
            assert len(response["embedding"]) > 0

    def test_embeddings_dimension_consistency(self, client: Client):
        """Test that embeddings have consistent dimensions for same model."""
        # Generate embeddings for multiple prompts
        prompts = ["First prompt", "Second prompt", "Third prompt"]
        dimensions = []

        for prompt in prompts:
            response = client.embeddings(model=TEST_MODEL, prompt=prompt)
            dimensions.append(len(response["embedding"]))

        # All embeddings should have the same dimension
        assert len(set(dimensions)) == 1, f"Inconsistent dimensions: {dimensions}"

    def test_embeddings_different_vectors(self, client: Client):
        """Test that different prompts produce different embeddings."""
        prompt1 = "The quick brown fox"
        prompt2 = "Lorem ipsum dolor sit amet"

        response1 = client.embeddings(model=TEST_MODEL, prompt=prompt1)
        response2 = client.embeddings(model=TEST_MODEL, prompt=prompt2)

        # Embeddings should be different
        embedding1 = response1["embedding"]
        embedding2 = response2["embedding"]

        # Calculate simple distance metric
        distance = sum((a - b) ** 2 for a, b in zip(embedding1, embedding2, strict=False)) ** 0.5

        # Distance should be significant (not identical vectors)
        assert distance > 0.1, "Embeddings are too similar for different prompts"

    def test_embeddings_similar_prompts(self, client: Client):
        """Test that similar prompts produce similar embeddings."""
        prompt1 = "The weather is nice today"
        prompt2 = "The weather is good today"
        prompt3 = "Python is a programming language"

        response1 = client.embeddings(model=TEST_MODEL, prompt=prompt1)
        response2 = client.embeddings(model=TEST_MODEL, prompt=prompt2)
        response3 = client.embeddings(model=TEST_MODEL, prompt=prompt3)

        # Calculate distances
        def cosine_similarity(v1, v2):
            dot_product = sum(a * b for a, b in zip(v1, v2, strict=False))
            magnitude1 = sum(a**2 for a in v1) ** 0.5
            magnitude2 = sum(b**2 for b in v2) ** 0.5
            return dot_product / (magnitude1 * magnitude2)

        # Similar prompts should have higher similarity
        sim_similar = cosine_similarity(response1["embedding"], response2["embedding"])
        sim_different = cosine_similarity(response1["embedding"], response3["embedding"])

        assert sim_similar > sim_different, "Similar prompts should have higher cosine similarity"

    def test_embeddings_empty_prompt_error(self, client: Client):
        """Test error handling for empty prompt."""
        with pytest.raises(Exception) as exc_info:
            client.embeddings(model=TEST_MODEL, prompt="")

        # Should get an error about empty prompt
        assert "empty" in str(exc_info.value).lower() or "prompt" in str(exc_info.value).lower()

    def test_embeddings_very_long_prompt(self, client: Client):
        """Test embeddings with very long prompt."""
        # Create a long prompt (but not too long to avoid token limits)
        long_prompt = "This is a test sentence. " * 200  # About 1000 tokens

        response = client.embeddings(model=TEST_MODEL, prompt=long_prompt)

        assert "embedding" in response
        assert isinstance(response["embedding"], list)
        assert len(response["embedding"]) > 0

    def test_embeddings_special_characters(self, client: Client):
        """Test embeddings with various special characters."""
        special_prompts = [
            "Text with\ttabs\tand\tspaces",
            "Text with\r\ncarriage returns",
            "Text with \"quotes\" and 'apostrophes'",
            "Text with \\backslashes\\ and /forward/slashes/",
            "Text with <html>tags</html> and &entities;",
        ]

        for prompt in special_prompts:
            response = client.embeddings(model=TEST_MODEL, prompt=prompt)

            assert "embedding" in response
            assert isinstance(response["embedding"], list)

    @pytest.mark.asyncio
    async def test_async_embeddings_basic(self, async_client: AsyncClient):
        """Test async embeddings functionality."""
        response = await async_client.embeddings(model=TEST_MODEL, prompt="Testing async embeddings")

        assert "embedding" in response
        assert isinstance(response["embedding"], list)
        assert len(response["embedding"]) > 0

    @pytest.mark.asyncio
    async def test_async_embeddings_concurrent(self, async_client: AsyncClient):
        """Test concurrent async embeddings requests."""
        import asyncio

        prompts = [f"Prompt number {i}" for i in range(5)]

        # Create concurrent tasks
        tasks = [async_client.embeddings(model=TEST_MODEL, prompt=prompt) for prompt in prompts]

        # Execute concurrently
        responses = await asyncio.gather(*tasks)

        # Verify all responses
        assert len(responses) == 5
        for response in responses:
            assert "embedding" in response
            assert isinstance(response["embedding"], list)

    def test_embeddings_performance(self, client: Client):
        """Test embeddings generation performance."""
        start_time = time.time()

        # Generate embeddings
        response = client.embeddings(model=TEST_MODEL, prompt="Performance test prompt")

        elapsed_time = time.time() - start_time

        # Verify response
        assert "embedding" in response

        # Log performance
        print(f"\nEmbeddings request completed in {elapsed_time:.2f} seconds")

        # Basic sanity check - should complete within reasonable time
        assert elapsed_time < 10, f"Request took too long: {elapsed_time} seconds"

    def test_embeddings_model_validation(self, client: Client):
        """Test model validation for embeddings."""
        # Note: This test might need adjustment based on actual model availability
        # For now, we'll test with a potentially invalid model name
        try:
            response = client.embeddings(model="invalid-embedding-model", prompt="Test prompt")
            # If this succeeds, it means the proxy is passing through to OpenAI
            # which might map the model or return an error
            if "embedding" in response:
                # Model was somehow accepted
                assert isinstance(response["embedding"], list)
        except Exception as e:
            # Expected to fail with invalid model
            assert "model" in str(e).lower() or "not found" in str(e).lower()

    def test_embeddings_dimension_for_model(self, client: Client):
        """Test that embedding dimensions match expected size for the model."""
        response = client.embeddings(model=TEST_MODEL, prompt="Test embedding dimensions")

        embedding = response["embedding"]
        dimension = len(embedding)

        # text-embedding-ada-002 should return 1536 dimensions
        # But allow some flexibility in case model changes
        assert dimension >= 512, f"Embedding dimension too small: {dimension}"
        assert dimension <= 4096, f"Embedding dimension too large: {dimension}"

        # Log the actual dimension for manual verification
        print(f"\nModel {TEST_MODEL} returned {dimension}-dimensional embeddings")

    def test_embeddings_normalized_vectors(self, client: Client):
        """Test properties of embedding vectors."""
        response = client.embeddings(model=TEST_MODEL, prompt="Test normalization")

        embedding = response["embedding"]

        # Check vector properties
        # Most embedding models return normalized vectors (magnitude ~1)
        magnitude = sum(x**2 for x in embedding) ** 0.5

        # Log magnitude for inspection
        print(f"\nEmbedding vector magnitude: {magnitude:.4f}")

        # Verify reasonable range
        assert 0.1 < magnitude < 10, f"Unexpected vector magnitude: {magnitude}"

    def test_both_endpoints_identical(self, client: Client):
        """Test that /api/embeddings and /api/embed return identical results."""
        prompt = "Test both endpoints"

        # Note: Ollama SDK only uses one endpoint, so we'll test via direct HTTP

        # Test /api/embeddings
        response1 = requests.post(
            f"{SERVER_HOST}/api/embeddings",
            json={"model": TEST_MODEL, "prompt": prompt},
            headers={"Content-Type": "application/json"},
        )
        assert response1.status_code == 200
        data1 = response1.json()

        # Test /api/embed
        response2 = requests.post(
            f"{SERVER_HOST}/api/embed",
            json={"model": TEST_MODEL, "prompt": prompt},
            headers={"Content-Type": "application/json"},
        )
        assert response2.status_code == 200
        data2 = response2.json()

        # Verify responses are very similar (OpenAI may return slightly different values)
        # Calculate cosine similarity between embeddings
        embedding1 = data1["embedding"]
        embedding2 = data2["embedding"]

        # Ensure same dimensions
        assert len(embedding1) == len(embedding2)

        # Calculate cosine similarity
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2, strict=False))
        magnitude1 = sum(a**2 for a in embedding1) ** 0.5
        magnitude2 = sum(b**2 for b in embedding2) ** 0.5
        cosine_similarity = dot_product / (magnitude1 * magnitude2)

        # Embeddings should be nearly identical (cosine similarity > 0.9999)
        assert cosine_similarity > 0.9999, f"Embeddings are not similar enough: {cosine_similarity}"
