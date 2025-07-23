"""Enhanced translation service with comprehensive model handling."""
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, ClassVar, Dict, List, Optional, Set

from openai.types import Model
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from ..models.ollama import (
    OllamaGenerateRequest,
    OllamaGenerateResponse,
    OllamaGenerateStreamChunk,
    OllamaModel,
    OllamaTagsResponse,
)
from .translation_service import TranslationService

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Registry for model metadata and mappings."""

    # Model aliases (Ollama name -> OpenAI ID)
    MODEL_ALIASES: ClassVar[Dict[str, str]] = {
        "llama2": "gpt-3.5-turbo",  # Fallback mapping
        "mistral": "gpt-3.5-turbo",  # Fallback mapping
        "codellama": "gpt-3.5-turbo-16k",  # For code-specific tasks
    }

    # Model categories
    CHAT_MODELS: ClassVar[Set[str]] = {
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
        "gpt-4",
        "gpt-4-32k",
        "gpt-4-turbo",
        "gpt-4o",
        "gpt-4o-mini",
    }

    EMBEDDING_MODELS: ClassVar[Set[str]] = {
        "text-embedding-ada-002",
        "text-embedding-3-small",
        "text-embedding-3-large",
    }

    # Model metadata
    MODEL_METADATA: ClassVar[Dict[str, Dict]] = {
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
            return int(metadata["size"])

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
        cls, openai_model: Model, include_digest: bool = True, custom_metadata: Optional[Dict] = None
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
        ollama_model = OllamaModel(name=openai_model.id, modified_at=modified_at, size=size, digest=digest)

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
    def translate_with_metadata(cls, openai_models: List[Model], include_metadata: bool = False) -> OllamaTagsResponse:
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
                    ollama_model = cls.create_ollama_model(openai_model, include_digest=True, custom_metadata=metadata)

                    ollama_models.append(ollama_model)
                    included_count += 1
                else:
                    excluded_count += 1
                    logger.debug(f"Excluded model: {openai_model.id}")

            except Exception as e:
                logger.error(f"Failed to translate model {openai_model.id}: {e}", exc_info=True)
                continue

        # Sort models by name for consistent output
        ollama_models.sort(key=lambda m: m.name)

        logger.info(
            "Model translation complete",
            extra={
                "total_models": len(openai_models),
                "included": included_count,
                "excluded": excluded_count,
                "errors": len(openai_models) - included_count - excluded_count,
            },
        )

        return OllamaTagsResponse(models=ollama_models)

    async def translate_generate_request(self, request: OllamaGenerateRequest) -> Dict[str, Any]:
        """
        Translate Ollama generate request to OpenAI chat completion format.

        Args:
            request: Ollama generate request

        Returns:
            Dict with OpenAI chat completion parameters
        """
        # Build messages array
        messages = []

        # Add system message if provided
        if request.system:
            messages.append({"role": "system", "content": request.system})

        # Add user prompt
        messages.append({"role": "user", "content": request.prompt})

        # Build OpenAI request
        openai_request = {
            "model": ModelRegistry.MODEL_ALIASES.get(request.model, request.model),
            "messages": messages,
        }

        # Only add stream parameter for non-streaming requests
        # (streaming requests use a different method that always streams)
        if not request.stream:
            openai_request["stream"] = False

        # Add options if provided
        if request.options:
            # Map Ollama options to OpenAI parameters
            if "temperature" in request.options:
                openai_request["temperature"] = request.options["temperature"]
            if "top_p" in request.options:
                openai_request["top_p"] = request.options["top_p"]
            if "seed" in request.options:
                openai_request["seed"] = request.options["seed"]
            if "num_predict" in request.options:
                openai_request["max_tokens"] = request.options["num_predict"]
            if "stop" in request.options:
                openai_request["stop"] = request.options["stop"]

        logger.debug(f"Translated generate request: {request.model} -> {openai_request['model']}")

        return openai_request

    async def translate_generate_response(self, openai_response: ChatCompletion, model: str) -> OllamaGenerateResponse:
        """
        Translate OpenAI chat completion to Ollama generate response.

        Args:
            openai_response: OpenAI chat completion
            model: Original model name from request

        Returns:
            OllamaGenerateResponse
        """
        # Extract the response text
        response_text = ""
        finish_reason = "stop"

        if openai_response.choices:
            choice = openai_response.choices[0]
            if choice.message and choice.message.content:
                response_text = choice.message.content
            if choice.finish_reason:
                finish_reason = choice.finish_reason

        # Create Ollama response
        # Format timestamp as RFC3339 with Z suffix
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        ollama_response = OllamaGenerateResponse(
            model=model,
            created_at=timestamp,
            response=response_text,
            done=True,
            done_reason=finish_reason,
            # Generate a dummy context for compatibility
            # In a real implementation, this would be actual token IDs
            context=[128006, 882, 128007, 128006, 78191, 128007],
        )

        # Add usage stats if available
        if openai_response.usage:
            if openai_response.usage.prompt_tokens:
                ollama_response.prompt_eval_count = openai_response.usage.prompt_tokens
            if openai_response.usage.completion_tokens:
                ollama_response.eval_count = openai_response.usage.completion_tokens

        return ollama_response

    async def translate_generate_stream_chunk(
        self, openai_chunk: ChatCompletionChunk, model: str
    ) -> OllamaGenerateStreamChunk:
        """
        Translate OpenAI streaming chunk to Ollama generate stream chunk.

        Args:
            openai_chunk: OpenAI chat completion chunk
            model: Original model name from request

        Returns:
            OllamaGenerateStreamChunk
        """
        # Extract content from chunk
        content = ""
        done = False
        finish_reason = None

        if openai_chunk.choices:
            choice = openai_chunk.choices[0]
            if choice.delta and choice.delta.content:
                content = choice.delta.content
            if choice.finish_reason:
                done = True
                finish_reason = choice.finish_reason

        # Create Ollama chunk
        # Format timestamp as RFC3339 with Z suffix
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        chunk = OllamaGenerateStreamChunk(
            model=model,
            created_at=timestamp,
            response=content,
            done=done,
        )

        if done and finish_reason:
            chunk.done_reason = finish_reason

        return chunk
