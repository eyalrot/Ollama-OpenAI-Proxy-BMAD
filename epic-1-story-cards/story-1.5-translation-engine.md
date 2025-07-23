# Story 1.5: Translation Engine for Model Listing

**Story Points**: 2  
**Priority**: P0 (Core functionality)  
**Type**: Feature  
**Dependencies**: Story 1.4 implementation started

## Story Summary
**As a** developer,  
**I want to** implement the translation logic for model listing,  
**So that** OpenAI model data is correctly converted to Ollama format.

## Technical Implementation Guide

### Pre-Implementation Checklist
- [ ] Story 1.4 basic endpoint structure in place
- [ ] Understanding of Ollama's model format
- [ ] Virtual environment activated

### Important Note
This story focuses on refining and testing the translation logic that was initially created in Story 1.4. The goal is to ensure robust, well-tested translation with proper edge case handling.

### Implementation Steps

#### Step 1: Enhance Translation Service
Update **src/ollama_openai_proxy/services/translation_service.py** with additional features:

```python
"""Enhanced translation service with comprehensive model handling."""
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set

from openai.types import Model

from ..models.ollama import OllamaModel, OllamaTagsResponse

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Registry for model metadata and mappings."""
    
    # Model aliases (Ollama name -> OpenAI ID)
    MODEL_ALIASES: Dict[str, str] = {
        "llama2": "gpt-3.5-turbo",  # Fallback mapping
        "mistral": "gpt-3.5-turbo",  # Fallback mapping
        "codellama": "gpt-3.5-turbo-16k",  # For code-specific tasks
    }
    
    # Model categories
    CHAT_MODELS: Set[str] = {
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
        "gpt-4",
        "gpt-4-32k",
        "gpt-4-turbo",
        "gpt-4o",
        "gpt-4o-mini",
    }
    
    EMBEDDING_MODELS: Set[str] = {
        "text-embedding-ada-002",
        "text-embedding-3-small",
        "text-embedding-3-large",
    }
    
    # Model metadata
    MODEL_METADATA: Dict[str, Dict] = {
        "gpt-3.5-turbo": {
            "size": 1_500_000_000,
            "description": "Most capable GPT-3.5 model",
            "context_length": 4096,
        },
        "gpt-3.5-turbo-16k": {
            "size": 1_600_000_000,
            "description": "GPT-3.5 with 16k context",
            "context_length": 16384,
        },
        "gpt-4": {
            "size": 20_000_000_000,
            "description": "Most capable GPT-4 model",
            "context_length": 8192,
        },
        "gpt-4-32k": {
            "size": 20_500_000_000,
            "description": "GPT-4 with 32k context",
            "context_length": 32768,
        },
        "gpt-4-turbo": {
            "size": 25_000_000_000,
            "description": "GPT-4 Turbo with 128k context",
            "context_length": 128000,
        },
        "text-embedding-ada-002": {
            "size": 350_000_000,
            "description": "Most capable v2 embedding model",
            "dimensions": 1536,
        },
        "text-embedding-3-small": {
            "size": 100_000_000,
            "description": "Smaller, faster embedding model",
            "dimensions": 512,
        },
        "text-embedding-3-large": {
            "size": 600_000_000,
            "description": "Most capable v3 embedding model",
            "dimensions": 3072,
        },
    }


class EnhancedTranslationService(TranslationService):
    """Enhanced translation service with better model handling."""
    
    @classmethod
    def generate_model_digest(cls, model_id: str) -> str:
        """
        Generate a digest/hash for a model.
        
        Args:
            model_id: Model identifier
            
        Returns:
            str: Digest in format "sha256:hash"
        """
        # Create a stable hash based on model ID
        hash_object = hashlib.sha256(f"openai:{model_id}".encode())
        return f"sha256:{hash_object.hexdigest()[:12]}"
    
    @classmethod
    def estimate_model_size(cls, model: Model) -> int:
        """
        Estimate model size with fallback logic.
        
        Args:
            model: OpenAI model
            
        Returns:
            int: Estimated size in bytes
        """
        # Check registry first
        metadata = ModelRegistry.MODEL_METADATA.get(model.id)
        if metadata and "size" in metadata:
            return metadata["size"]
        
        # Fallback based on model type
        model_id_lower = model.id.lower()
        
        if "embedding" in model_id_lower:
            # Smaller size for embedding models
            return 500_000_000  # 500MB
        elif "gpt-4" in model_id_lower:
            # Larger size for GPT-4 variants
            return 20_000_000_000  # 20GB
        elif "gpt-3.5" in model_id_lower:
            # Medium size for GPT-3.5 variants
            return 2_000_000_000  # 2GB
        else:
            # Default fallback
            return cls.DEFAULT_MODEL_SIZE
    
    @classmethod
    def create_ollama_model(
        cls,
        openai_model: Model,
        include_digest: bool = True,
        custom_metadata: Optional[Dict] = None
    ) -> OllamaModel:
        """
        Create Ollama model with enhanced metadata.
        
        Args:
            openai_model: OpenAI model
            include_digest: Whether to include digest
            custom_metadata: Additional metadata to include
            
        Returns:
            OllamaModel: Enhanced Ollama model
        """
        # Convert timestamp
        created_dt = datetime.fromtimestamp(openai_model.created)
        modified_at = created_dt.isoformat() + "Z"
        
        # Get size estimate
        size = cls.estimate_model_size(openai_model)
        
        # Generate digest if requested
        digest = cls.generate_model_digest(openai_model.id) if include_digest else ""
        
        # Create base model
        ollama_model = OllamaModel(
            name=openai_model.id,
            modified_at=modified_at,
            size=size,
            digest=digest
        )
        
        # Add custom metadata if provided
        if custom_metadata:
            for key, value in custom_metadata.items():
                if hasattr(ollama_model, key):
                    setattr(ollama_model, key, value)
        
        return ollama_model
    
    @classmethod
    def should_include_model(cls, model: Model) -> bool:
        """
        Enhanced model filtering with registry.
        
        Args:
            model: OpenAI model
            
        Returns:
            bool: True if model should be included
        """
        model_id = model.id
        
        # Check if in known models
        if model_id in ModelRegistry.CHAT_MODELS:
            return True
        if model_id in ModelRegistry.EMBEDDING_MODELS:
            return True
        
        # Check aliases
        if model_id in ModelRegistry.MODEL_ALIASES.values():
            return True
        
        # Use parent class logic as fallback
        return cls._should_include_model(model)
    
    @classmethod
    def translate_with_metadata(
        cls,
        openai_models: List[Model],
        include_metadata: bool = False
    ) -> OllamaTagsResponse:
        """
        Translate with optional metadata inclusion.
        
        Args:
            openai_models: List of OpenAI models
            include_metadata: Whether to include extra metadata
            
        Returns:
            OllamaTagsResponse: Response with translated models
        """
        ollama_models = []
        included_count = 0
        excluded_count = 0
        
        for openai_model in openai_models:
            try:
                if cls.should_include_model(openai_model):
                    # Get metadata if requested
                    metadata = None
                    if include_metadata:
                        metadata = ModelRegistry.MODEL_METADATA.get(openai_model.id, {})
                    
                    # Create Ollama model
                    ollama_model = cls.create_ollama_model(
                        openai_model,
                        include_digest=True,
                        custom_metadata=metadata
                    )
                    
                    ollama_models.append(ollama_model)
                    included_count += 1
                else:
                    excluded_count += 1
                    logger.debug(f"Excluded model: {openai_model.id}")
                    
            except Exception as e:
                logger.error(
                    f"Failed to translate model {openai_model.id}: {e}",
                    exc_info=True
                )
                continue
        
        # Sort models by name for consistent output
        ollama_models.sort(key=lambda m: m.name)
        
        logger.info(
            f"Model translation complete",
            extra={
                "total_models": len(openai_models),
                "included": included_count,
                "excluded": excluded_count,
                "errors": len(openai_models) - included_count - excluded_count
            }
        )
        
        return OllamaTagsResponse(models=ollama_models)
```

#### Step 2: Create Comprehensive Unit Tests
**tests/unit/test_enhanced_translation.py**:

```python
"""Comprehensive tests for enhanced translation service."""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from openai.types import Model

from ollama_openai_proxy.services.translation_service import (
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
        (1234567890, "2009-02-13"),  # Specific date
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
```

#### Step 3: Create Performance Tests
**tests/unit/test_translation_performance.py**:

```python
"""Performance tests for translation service."""
import time
import pytest
from openai.types import Model

from ollama_openai_proxy.services.translation_service import EnhancedTranslationService


class TestTranslationPerformance:
    """Test translation performance."""
    
    def test_large_model_list_performance(self):
        """Test performance with large model list."""
        # Create 1000 models
        models = []
        for i in range(1000):
            models.append(
                Model(
                    id=f"model-{i}",
                    created=1234567890 + i,
                    object="model",
                    owned_by="openai"
                )
            )
        
        start_time = time.time()
        response = EnhancedTranslationService.translate_with_metadata(models)
        duration = time.time() - start_time
        
        # Should complete in reasonable time
        assert duration < 1.0  # Less than 1 second for 1000 models
        
        # Most models should be excluded (not matching patterns)
        assert len(response.models) < 100
    
    def test_digest_generation_performance(self):
        """Test digest generation is fast."""
        start_time = time.time()
        
        # Generate 10000 digests
        for i in range(10000):
            EnhancedTranslationService.generate_model_digest(f"model-{i}")
        
        duration = time.time() - start_time
        
        # Should be very fast
        assert duration < 0.5  # Less than 0.5 seconds for 10000 digests
```

### Verification Steps

1. **Run enhanced translation tests:**
   ```bash
   pytest tests/unit/test_enhanced_translation.py -v
   pytest tests/unit/test_translation_performance.py -v
   ```

2. **Test with real models:**
   ```python
   from ollama_openai_proxy.services.translation_service import EnhancedTranslationService
   from openai.types import Model
   
   # Test model
   model = Model(
       id="gpt-3.5-turbo",
       created=1234567890,
       object="model",
       owned_by="openai"
   )
   
   # Test translation
   ollama_model = EnhancedTranslationService.create_ollama_model(model)
   print(f"Name: {ollama_model.name}")
   print(f"Size: {ollama_model.size:,} bytes")
   print(f"Digest: {ollama_model.digest}")
   ```

3. **Verify edge cases:**
   ```bash
   # Test with empty list
   curl http://localhost:11434/api/tags
   
   # Test with invalid API key (should handle gracefully)
   OPENAI_API_KEY=invalid python -m ollama_openai_proxy
   ```

### Definition of Done Checklist

- [ ] Translation function handles all OpenAI model types
- [ ] Model IDs preserved as Ollama names
- [ ] Timestamps converted to ISO format with 'Z'
- [ ] Model sizes estimated accurately
- [ ] Edge cases handled (empty lists, errors)
- [ ] Unknown models handled gracefully
- [ ] Model filtering excludes irrelevant models
- [ ] Metadata preserved for future use
- [ ] Unit tests achieve 100% coverage
- [ ] Performance tests pass
- [ ] Translation is a pure function
- [ ] Logging provides debugging information

### Integration Notes

- The enhanced translation service can replace the basic one
- Model registry allows easy addition of new models
- Digest generation provides stable identifiers
- Metadata structure allows future expansion

### Next Steps

After completing this story:
1. Run all tests to ensure quality
2. Update Story 1.4 to use enhanced service
3. Commit changes
4. Create PR for review
5. Move to Story 1.6: Testing Infrastructure Setup