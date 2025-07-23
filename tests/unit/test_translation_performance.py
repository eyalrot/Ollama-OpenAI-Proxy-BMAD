"""Performance tests for translation service."""
import time
import pytest
from openai.types import Model

from ollama_openai_proxy.services.enhanced_translation_service import EnhancedTranslationService


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