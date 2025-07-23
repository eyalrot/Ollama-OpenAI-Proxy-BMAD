"""Comprehensive tests for enhanced translation service."""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from openai.types import Model

from ollama_openai_proxy.services.enhanced_translation_service import (
    EnhancedTranslationService,
    ModelRegistry
)


class TestModelRegistry:
    """Test model registry functionality."""
    
    def test_model_categories(self):
        """Test model categorization."""
        assert "gpt-3.5-turbo" in ModelRegistry.CHAT_MODELS
        assert "text-embedding-ada-002" in ModelRegistry.EMBEDDING_MODELS
        assert "gpt-4" in ModelRegistry.CHAT_MODELS
    
    def test_model_metadata(self):
        """Test model metadata."""
        gpt35_meta = ModelRegistry.MODEL_METADATA["gpt-3.5-turbo"]
        assert gpt35_meta["size"] == 1_500_000_000
        assert gpt35_meta["context_length"] == 4096
        
        embed_meta = ModelRegistry.MODEL_METADATA["text-embedding-ada-002"]
        assert embed_meta["dimensions"] == 1536


class TestEnhancedTranslationService:
    """Test enhanced translation functionality."""
    
    def test_generate_model_digest(self):
        """Test digest generation."""
        digest1 = EnhancedTranslationService.generate_model_digest("gpt-3.5-turbo")
        digest2 = EnhancedTranslationService.generate_model_digest("gpt-3.5-turbo")
        digest3 = EnhancedTranslationService.generate_model_digest("gpt-4")
        
        # Same model should have same digest
        assert digest1 == digest2
        # Different models should have different digests
        assert digest1 != digest3
        # Should be in correct format
        assert digest1.startswith("sha256:")
        assert len(digest1) == 19  # "sha256:" + 12 chars
    
    def test_estimate_model_size_known_model(self):
        """Test size estimation for known models."""
        model = Model(
            id="gpt-4",
            created=1234567890,
            object="model",
            owned_by="openai"
        )
        
        size = EnhancedTranslationService.estimate_model_size(model)
        assert size == 20_000_000_000
    
    def test_estimate_model_size_unknown_model(self):
        """Test size estimation for unknown models."""
        # Embedding model
        embed_model = Model(
            id="new-embedding-model",
            created=1234567890,
            object="model",
            owned_by="openai"
        )
        size = EnhancedTranslationService.estimate_model_size(embed_model)
        assert size == 500_000_000
        
        # GPT-4 variant
        gpt4_model = Model(
            id="gpt-4-vision",
            created=1234567890,
            object="model",
            owned_by="openai"
        )
        size = EnhancedTranslationService.estimate_model_size(gpt4_model)
        assert size == 20_000_000_000
        
        # Unknown model
        unknown_model = Model(
            id="future-model",
            created=1234567890,
            object="model",
            owned_by="openai"
        )
        size = EnhancedTranslationService.estimate_model_size(unknown_model)
        assert size == EnhancedTranslationService.DEFAULT_MODEL_SIZE
    
    def test_create_ollama_model_with_options(self):
        """Test Ollama model creation with options."""
        openai_model = Model(
            id="gpt-3.5-turbo",
            created=1234567890,
            object="model",
            owned_by="openai"
        )
        
        # Without digest
        model1 = EnhancedTranslationService.create_ollama_model(
            openai_model,
            include_digest=False
        )
        assert model1.digest == ""
        
        # With digest
        model2 = EnhancedTranslationService.create_ollama_model(
            openai_model,
            include_digest=True
        )
        assert model2.digest.startswith("sha256:")
        
        # With custom metadata (Note: base model doesn't have these fields)
        model3 = EnhancedTranslationService.create_ollama_model(
            openai_model,
            custom_metadata={"size": 999}
        )
        assert model3.size == 999
    
    def test_should_include_model_enhanced(self):
        """Test enhanced model filtering."""
        # Known chat model
        assert EnhancedTranslationService.should_include_model(
            Model(id="gpt-3.5-turbo", created=1, object="model", owned_by="openai")
        )
        
        # Known embedding model
        assert EnhancedTranslationService.should_include_model(
            Model(id="text-embedding-3-small", created=1, object="model", owned_by="openai")
        )
        
        # Should still exclude deprecated
        assert not EnhancedTranslationService.should_include_model(
            Model(id="text-davinci-003", created=1, object="model", owned_by="openai")
        )
    
    def test_translate_with_metadata(self):
        """Test translation with metadata option."""
        models = [
            Model(id="gpt-3.5-turbo", created=1234567890, object="model", owned_by="openai"),
            Model(id="gpt-4", created=1234567891, object="model", owned_by="openai"),
            Model(id="text-davinci-003", created=1234567892, object="model", owned_by="openai"),
        ]
        
        # Without metadata
        response1 = EnhancedTranslationService.translate_with_metadata(
            models,
            include_metadata=False
        )
        assert len(response1.models) == 2  # Excludes davinci
        
        # With metadata (though base model won't show extra fields)
        response2 = EnhancedTranslationService.translate_with_metadata(
            models,
            include_metadata=True
        )
        assert len(response2.models) == 2
        
        # Check sorting
        assert response2.models[0].name == "gpt-3.5-turbo"
        assert response2.models[1].name == "gpt-4"
    
    def test_error_handling_in_translation(self):
        """Test error handling during translation."""
        # Create a model that will cause an error
        bad_model = Mock(spec=Model)
        bad_model.id = "test-model"
        bad_model.created = "not-a-timestamp"  # This will cause an error
        
        good_model = Model(
            id="gpt-3.5-turbo",
            created=1234567890,
            object="model",
            owned_by="openai"
        )
        
        models = [bad_model, good_model]
        
        # Should handle error and still translate good model
        response = EnhancedTranslationService.translate_with_metadata(models)
        assert len(response.models) == 1
        assert response.models[0].name == "gpt-3.5-turbo"


class TestEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_empty_model_list(self):
        """Test handling of empty model list."""
        response = EnhancedTranslationService.translate_with_metadata([])
        assert len(response.models) == 0
        assert response.models == []
    
    def test_all_models_excluded(self):
        """Test when all models are excluded."""
        models = [
            Model(id="davinci-002", created=1, object="model", owned_by="openai"),
            Model(id="curie-001", created=2, object="model", owned_by="openai"),
        ]
        
        response = EnhancedTranslationService.translate_with_metadata(models)
        assert len(response.models) == 0
    
    def test_duplicate_models(self):
        """Test handling of duplicate models."""
        models = [
            Model(id="gpt-3.5-turbo", created=1234567890, object="model", owned_by="openai"),
            Model(id="gpt-3.5-turbo", created=1234567890, object="model", owned_by="openai"),
        ]
        
        response = EnhancedTranslationService.translate_with_metadata(models)
        # Should include both even if duplicates
        assert len(response.models) == 2
    
    @pytest.mark.parametrize("timestamp,expected_substr", [
        (0, "1970-01-01"),  # Epoch
        (1234567890, "2009-02-1"),  # Specific date (partial match to handle timezone)
        (2147483647, "2038-01-19"),  # Max 32-bit timestamp
    ])
    def test_timestamp_conversion(self, timestamp, expected_substr):
        """Test various timestamp conversions."""
        model = Model(
            id="test-model",
            created=timestamp,
            object="model",
            owned_by="openai"
        )
        
        ollama_model = EnhancedTranslationService.create_ollama_model(model)
        assert expected_substr in ollama_model.modified_at
        assert ollama_model.modified_at.endswith("Z")