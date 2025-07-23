"""Data models for Ollama API compatibility."""
from .ollama import (
    OllamaError,
    OllamaGenerateRequest,
    OllamaGenerateResponse,
    OllamaGenerateStreamChunk,
    OllamaModel,
    OllamaTagsResponse,
)

__all__ = [
    "OllamaError",
    "OllamaGenerateRequest",
    "OllamaGenerateResponse",
    "OllamaGenerateStreamChunk",
    "OllamaModel",
    "OllamaTagsResponse",
]
