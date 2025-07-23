"""Unit tests for embeddings translation functions."""
import pytest
from ollama_openai_proxy.models.ollama import (
    OllamaEmbeddingsRequest,
    OllamaEmbeddingsResponse,
)
from ollama_openai_proxy.services.enhanced_translation_service import (
    EnhancedTranslationService,
)
from openai.types import CreateEmbeddingResponse, Embedding
from openai.types.create_embedding_response import Usage


class TestEmbeddingsTranslation:
    """Test cases for embeddings translation functions."""

    @pytest.fixture
    def translation_service(self):
        """Create translation service instance."""
        return EnhancedTranslationService()

    @pytest.mark.asyncio
    async def test_translate_embeddings_request_basic(self, translation_service):
        """Test basic translation of Ollama embeddings request to OpenAI format."""
        # Create Ollama request
        ollama_request = OllamaEmbeddingsRequest(model="text-embedding-ada-002", prompt="Hello, world!")

        # Translate to OpenAI format
        openai_request = await translation_service.translate_embeddings_request(ollama_request)

        # Verify translation
        assert openai_request["model"] == "text-embedding-ada-002"
        assert openai_request["input"] == "Hello, world!"
        assert len(openai_request) == 2  # Only model and input fields

    @pytest.mark.asyncio
    async def test_translate_embeddings_request_with_options(self, translation_service):
        """Test translation of embeddings request with options."""
        # Create Ollama request with options
        ollama_request = OllamaEmbeddingsRequest(
            model="text-embedding-ada-002",
            prompt="Test prompt",
            options={"temperature": 0.5},  # Options should be ignored for embeddings
            keep_alive="5m",
        )

        # Translate to OpenAI format
        openai_request = await translation_service.translate_embeddings_request(ollama_request)

        # Verify translation - options are not passed to OpenAI embeddings
        assert openai_request["model"] == "text-embedding-ada-002"
        assert openai_request["input"] == "Test prompt"
        assert "temperature" not in openai_request
        assert "keep_alive" not in openai_request

    @pytest.mark.asyncio
    async def test_translate_embeddings_response_basic(self, translation_service):
        """Test basic translation of OpenAI embeddings response to Ollama format."""
        # Create OpenAI response
        mock_embedding = Embedding(index=0, embedding=[0.1, 0.2, 0.3, -0.4, 0.5], object="embedding")

        openai_response = CreateEmbeddingResponse(
            data=[mock_embedding],
            model="text-embedding-ada-002",
            object="list",
            usage=Usage(prompt_tokens=10, total_tokens=10),
        )

        # Translate to Ollama format
        ollama_response = await translation_service.translate_embeddings_response(openai_response)

        # Verify translation
        assert isinstance(ollama_response, OllamaEmbeddingsResponse)
        assert ollama_response.embedding == [0.1, 0.2, 0.3, -0.4, 0.5]

    @pytest.mark.asyncio
    async def test_translate_embeddings_response_high_dimensional(self, translation_service):
        """Test translation preserves high-dimensional embeddings."""
        # Create high-dimensional embedding (1536 dimensions)
        large_embedding = [float(i) / 1536 for i in range(1536)]

        mock_embedding = Embedding(index=0, embedding=large_embedding, object="embedding")

        openai_response = CreateEmbeddingResponse(
            data=[mock_embedding],
            model="text-embedding-ada-002",
            object="list",
            usage=Usage(prompt_tokens=20, total_tokens=20),
        )

        # Translate to Ollama format
        ollama_response = await translation_service.translate_embeddings_response(openai_response)

        # Verify dimensions are preserved
        assert len(ollama_response.embedding) == 1536
        # Verify values are preserved
        for i, val in enumerate(ollama_response.embedding):
            assert abs(val - (float(i) / 1536)) < 1e-6

    @pytest.mark.asyncio
    async def test_translate_embeddings_response_empty_data(self, translation_service):
        """Test handling of empty embedding data."""
        # Create OpenAI response with empty data
        openai_response = CreateEmbeddingResponse(
            data=[], model="text-embedding-ada-002", object="list", usage=Usage(prompt_tokens=0, total_tokens=0)
        )

        # Translate to Ollama format
        ollama_response = await translation_service.translate_embeddings_response(openai_response)

        # Verify empty embedding array
        assert isinstance(ollama_response, OllamaEmbeddingsResponse)
        assert ollama_response.embedding == []

    @pytest.mark.asyncio
    async def test_translate_embeddings_prompt_formats(self, translation_service):
        """Test translation handles different prompt formats."""
        test_prompts = [
            "Simple text",
            "Text with\nnewlines",
            "Text with special chars: !@#$%^&*()",
            "Unicode text: 你好世界 🌍",
            " " * 100,  # Spaces only
            "A" * 10000,  # Very long text
        ]

        for prompt in test_prompts:
            ollama_request = OllamaEmbeddingsRequest(model="text-embedding-ada-002", prompt=prompt)

            openai_request = await translation_service.translate_embeddings_request(ollama_request)

            # Verify prompt is preserved exactly
            assert openai_request["input"] == prompt

    @pytest.mark.asyncio
    async def test_translate_embeddings_model_names(self, translation_service):
        """Test translation handles different model names."""
        test_models = [
            "text-embedding-ada-002",
            "text-embedding-3-small",
            "text-embedding-3-large",
            "custom-embedding-model",
            "llama2",  # Non-embedding model (should still translate)
        ]

        for model in test_models:
            ollama_request = OllamaEmbeddingsRequest(model=model, prompt="Test")

            openai_request = await translation_service.translate_embeddings_request(ollama_request)

            # Verify model name is preserved
            assert openai_request["model"] == model

    @pytest.mark.asyncio
    async def test_embeddings_response_field_names(self, translation_service):
        """Test that response uses correct field names for Ollama format."""
        # Create OpenAI response
        mock_embedding = Embedding(index=0, embedding=[0.1, 0.2, 0.3], object="embedding")

        openai_response = CreateEmbeddingResponse(
            data=[mock_embedding],
            model="text-embedding-ada-002",
            object="list",
            usage=Usage(prompt_tokens=5, total_tokens=5),
        )

        # Translate to Ollama format
        ollama_response = await translation_service.translate_embeddings_response(openai_response)

        # Verify Ollama response structure
        response_dict = ollama_response.model_dump()
        assert "embedding" in response_dict  # Ollama uses singular "embedding"
        assert "embeddings" not in response_dict  # Not "embeddings" (plural)
        assert "data" not in response_dict  # Not OpenAI's "data" structure
        assert isinstance(response_dict["embedding"], list)

    @pytest.mark.asyncio
    async def test_embeddings_precision_preserved(self, translation_service):
        """Test that floating point precision is preserved in translation."""
        # Create embedding with precise float values
        precise_embedding = [
            0.123456789012345,
            -0.987654321098765,
            1.23456789012345e-10,
            -1.23456789012345e10,
            float("inf"),
            float("-inf"),
            0.0,
            -0.0,
        ]

        # Remove inf values as they may not serialize properly
        precise_embedding = [x for x in precise_embedding if not abs(x) == float("inf")]

        mock_embedding = Embedding(index=0, embedding=precise_embedding, object="embedding")

        openai_response = CreateEmbeddingResponse(
            data=[mock_embedding],
            model="text-embedding-ada-002",
            object="list",
            usage=Usage(prompt_tokens=5, total_tokens=5),
        )

        # Translate to Ollama format
        ollama_response = await translation_service.translate_embeddings_response(openai_response)

        # Verify precision is maintained
        for i, val in enumerate(ollama_response.embedding):
            assert val == precise_embedding[i]
