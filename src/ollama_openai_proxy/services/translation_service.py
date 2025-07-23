"""Translation service for converting between Ollama and OpenAI formats."""
import logging
from datetime import datetime
from typing import List

from openai.types import Model

from ..models.ollama import OllamaModel, OllamaTagsResponse

logger = logging.getLogger(__name__)


class TranslationService:
    """Service for translating between Ollama and OpenAI formats."""
    
    # Default size for models (1GB)
    DEFAULT_MODEL_SIZE = 1_000_000_000
    
    # Model size estimates (in bytes)
    MODEL_SIZES = {
        "gpt-3.5-turbo": 1_500_000_000,
        "gpt-3.5-turbo-16k": 1_600_000_000,
        "gpt-4": 20_000_000_000,
        "gpt-4-32k": 20_500_000_000,
        "gpt-4-turbo": 25_000_000_000,
        "text-embedding-ada-002": 350_000_000,
        "text-embedding-3-small": 100_000_000,
        "text-embedding-3-large": 600_000_000,
    }
    
    @classmethod
    def openai_to_ollama_model(cls, openai_model: Model) -> OllamaModel:
        """
        Convert OpenAI model to Ollama format.
        
        Args:
            openai_model: OpenAI model object
            
        Returns:
            OllamaModel: Model in Ollama format
        """
        # Convert timestamp to ISO format
        created_dt = datetime.fromtimestamp(openai_model.created)
        modified_at = created_dt.isoformat() + "Z"
        
        # Estimate model size
        model_size = cls.MODEL_SIZES.get(
            openai_model.id,
            cls.DEFAULT_MODEL_SIZE
        )
        
        # Create Ollama model
        return OllamaModel(
            name=openai_model.id,
            modified_at=modified_at,
            size=model_size,
            digest=f"openai:{openai_model.id}"
        )
    
    @classmethod
    def translate_model_list(cls, openai_models: List[Model]) -> OllamaTagsResponse:
        """
        Translate list of OpenAI models to Ollama tags response.
        
        Args:
            openai_models: List of OpenAI models
            
        Returns:
            OllamaTagsResponse: Ollama-formatted response
        """
        ollama_models = []
        
        for openai_model in openai_models:
            try:
                # Filter out non-chat/embedding models
                if cls._should_include_model(openai_model):
                    ollama_model = cls.openai_to_ollama_model(openai_model)
                    ollama_models.append(ollama_model)
                    
                    logger.debug(
                        f"Translated model {openai_model.id}",
                        extra={
                            "openai_id": openai_model.id,
                            "ollama_name": ollama_model.name,
                            "size": ollama_model.size
                        }
                    )
            except Exception as e:
                logger.warning(
                    f"Failed to translate model {openai_model.id}: {e}",
                    extra={"model_id": openai_model.id, "error": str(e)}
                )
                continue
        
        logger.info(
            f"Translated {len(ollama_models)} models from {len(openai_models)} OpenAI models"
        )
        
        return OllamaTagsResponse(models=ollama_models)
    
    @staticmethod
    def _should_include_model(model: Model) -> bool:
        """
        Determine if a model should be included in Ollama response.
        
        Args:
            model: OpenAI model
            
        Returns:
            bool: True if model should be included
        """
        # Include chat and embedding models
        include_prefixes = (
            "gpt-",
            "text-embedding-",
            "chatgpt-",
            "o1-",
            "o3-"
        )
        
        # Exclude deprecated or special models
        exclude_keywords = (
            "deprecated",
            "preview",
            "instruct",
            "davinci",
            "curie",
            "babbage"
        )
        
        # Also exclude old model names that start with these
        exclude_starts = (
            "text-ada-",
            "code-ada-",
            "ada-"
        )
        
        model_id_lower = model.id.lower()
        
        # Check exclusions first
        if any(keyword in model_id_lower for keyword in exclude_keywords):
            return False
        
        # Check if model starts with excluded patterns
        if any(model_id_lower.startswith(prefix) for prefix in exclude_starts):
            return False
        
        # Check inclusions
        return any(model_id_lower.startswith(prefix) for prefix in include_prefixes)