"""Data models for Ollama API compatibility."""
from .ollama import (
    OllamaChatMessage,
    OllamaChatRequest,
    OllamaChatResponse,
    OllamaChatStreamChunk,
    OllamaError,
    OllamaGenerateRequest,
    OllamaGenerateResponse,
    OllamaGenerateStreamChunk,
    OllamaModel,
    OllamaTagsResponse,
)

__all__ = [
    "OllamaChatMessage",
    "OllamaChatRequest",
    "OllamaChatResponse",
    "OllamaChatStreamChunk",
    "OllamaError",
    "OllamaGenerateRequest",
    "OllamaGenerateResponse",
    "OllamaGenerateStreamChunk",
    "OllamaModel",
    "OllamaTagsResponse",
]
