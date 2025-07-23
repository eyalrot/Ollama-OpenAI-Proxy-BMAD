"""Tests for translation service."""

from ollama_openai_proxy.models.ollama import OllamaModel, OllamaTagsResponse
from ollama_openai_proxy.services.translation_service import TranslationService
from openai.types import Model


class TestTranslationService:
    """Test translation service functionality."""

    def test_openai_to_ollama_model(self):
        """Test single model translation."""
        openai_model = Model(id="gpt-3.5-turbo", created=1234567890, object="model", owned_by="openai")

        ollama_model = TranslationService.openai_to_ollama_model(openai_model)

        assert isinstance(ollama_model, OllamaModel)
        assert ollama_model.name == "gpt-3.5-turbo"
        assert ollama_model.size == 1_500_000_000  # Known size
        assert ollama_model.digest == "openai:gpt-3.5-turbo"
        assert ollama_model.modified_at.endswith("Z")

    def test_translate_model_list(self):
        """Test translating list of models."""
        openai_models = [
            Model(id="gpt-3.5-turbo", created=1234567890, object="model", owned_by="openai"),
            Model(id="gpt-4", created=1234567891, object="model", owned_by="openai"),
            Model(id="text-embedding-3-small", created=1234567892, object="model", owned_by="openai"),
        ]

        response = TranslationService.translate_model_list(openai_models)

        assert isinstance(response, OllamaTagsResponse)
        assert len(response.models) == 3
        assert response.models[0].name == "gpt-3.5-turbo"
        assert response.models[1].name == "gpt-4"
        assert response.models[2].name == "text-embedding-3-small"

    def test_should_include_model(self):
        """Test model filtering logic."""
        # Should include
        assert TranslationService._should_include_model(
            Model(id="gpt-3.5-turbo", created=1, object="model", owned_by="openai")
        )
        assert TranslationService._should_include_model(
            Model(id="text-embedding-3-large", created=1, object="model", owned_by="openai")
        )
        assert TranslationService._should_include_model(
            Model(id="text-embedding-ada-002", created=1, object="model", owned_by="openai")
        )

        # Should exclude
        assert not TranslationService._should_include_model(
            Model(id="davinci-002", created=1, object="model", owned_by="openai")
        )
        assert not TranslationService._should_include_model(
            Model(id="gpt-3.5-turbo-instruct", created=1, object="model", owned_by="openai")
        )
        assert not TranslationService._should_include_model(
            Model(id="text-ada-001", created=1, object="model", owned_by="openai")
        )
        assert not TranslationService._should_include_model(
            Model(id="ada-search", created=1, object="model", owned_by="openai")
        )

    def test_unknown_model_size(self):
        """Test handling of unknown model."""
        openai_model = Model(id="future-model-xyz", created=1234567890, object="model", owned_by="openai")

        ollama_model = TranslationService.openai_to_ollama_model(openai_model)

        assert ollama_model.size == TranslationService.DEFAULT_MODEL_SIZE

    def test_empty_model_list(self):
        """Test handling empty model list."""
        response = TranslationService.translate_model_list([])

        assert isinstance(response, OllamaTagsResponse)
        assert len(response.models) == 0
