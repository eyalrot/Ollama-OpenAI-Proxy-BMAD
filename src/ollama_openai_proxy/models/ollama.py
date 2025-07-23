"""Ollama API data models.

Based on analysis of the Postman collection, the actual Ollama API
returns BOTH 'name' and 'model' fields with the same value.
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class OllamaModel(BaseModel):
    """Model information in Ollama format."""

    name: str = Field(..., description="Model name/ID")
    model: str = Field(..., description="Model name/ID (duplicate of name field)")
    modified_at: str = Field(..., description="RFC3339 timestamp with timezone")
    size: int = Field(..., description="Model size in bytes")
    digest: str = Field(..., description="Model digest/hash (sha256:...)")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Optional model details")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "llama3.1:latest",
                "model": "llama3.1:latest",
                "modified_at": "2025-01-21T16:53:57.496699591-08:00",
                "size": 4920753328,
                "digest": "sha256:46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e",
                "details": {
                    "parent_model": "",
                    "format": "gguf",
                    "family": "llama",
                    "families": ["llama"],
                    "parameter_size": "8.0B",
                    "quantization_level": "Q4_K_M",
                },
            }
        }
    )

    def __init__(self, **data: Any) -> None:
        """Initialize model, automatically duplicating name to model field."""
        # If only name is provided, duplicate it to model field
        if "name" in data and "model" not in data:
            data["model"] = data["name"]
        # If only model is provided, duplicate it to name field
        elif "model" in data and "name" not in data:
            data["name"] = data["model"]
        super().__init__(**data)


class OllamaTagsResponse(BaseModel):
    """Response format for /api/tags endpoint."""

    models: List[OllamaModel] = Field(default_factory=list, description="List of available models")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "models": [
                    {
                        "name": "llama3.1:latest",
                        "model": "llama3.1:latest",
                        "modified_at": "2025-01-21T16:53:57.496699591-08:00",
                        "size": 4920753328,
                        "digest": "sha256:46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e",
                    },
                    {
                        "name": "gpt-4",
                        "model": "gpt-4",
                        "modified_at": "2024-01-20T10:30:00Z",
                        "size": 2000000000,
                        "digest": "sha256:def456789012",
                    },
                ]
            }
        }
    )


class OllamaError(BaseModel):
    """Error response in Ollama format."""

    error: str = Field(..., description="Error message")

    model_config = ConfigDict(json_schema_extra={"example": {"error": "model not found"}})


class OllamaErrorDetails(BaseModel):
    """Detailed error information."""

    message: str = Field(..., description="Human-readable error message")
    type: str = Field(..., description="Error type identifier")
    code: Optional[int] = Field(default=None, description="HTTP status code")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")


class OllamaErrorResponse(BaseModel):
    """Enhanced error response with correlation ID and metadata."""

    error: OllamaErrorDetails = Field(..., description="Error details")
    correlation_id: Optional[str] = Field(default=None, description="Request correlation ID for debugging")
    model: Optional[str] = Field(default=None, description="Model that was requested")
    created_at: Optional[str] = Field(default=None, description="RFC3339 timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": {
                    "message": "Rate limit exceeded",
                    "type": "rate_limit_error",
                    "code": 429,
                    "details": {"retry_after": 60},
                },
                "correlation_id": "req_12345",
                "model": "llama2",
                "created_at": "2023-08-04T19:56:02.647Z",
            }
        }
    )


class OllamaGenerateRequest(BaseModel):
    """Request format for /api/generate endpoint."""

    model: str = Field(..., description="Model name/ID to use for generation")
    prompt: str = Field(..., description="The prompt to generate from")
    stream: Optional[bool] = Field(default=True, description="Whether to stream the response")
    raw: Optional[bool] = Field(default=False, description="Whether to use raw mode (bypass prompt template)")
    format: Optional[str] = Field(default=None, description="Output format (e.g., 'json')")
    system: Optional[str] = Field(default=None, description="System prompt to use")
    template: Optional[str] = Field(default=None, description="Custom prompt template")
    context: Optional[List[int]] = Field(default=None, description="Context from previous response for continuation")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Model parameters")
    keep_alive: Optional[str] = Field(default=None, description="How long to keep model loaded")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model": "llama2",
                "prompt": "Why is the sky blue?",
                "stream": False,
                "options": {"temperature": 0.7, "top_p": 0.9, "seed": 42},
            }
        }
    )


class OllamaGenerateResponse(BaseModel):
    """Response format for /api/generate endpoint (non-streaming)."""

    model: str = Field(..., description="Model used for generation")
    created_at: str = Field(..., description="RFC3339 timestamp with timezone")
    response: str = Field(..., description="Generated text")
    done: bool = Field(..., description="Whether generation is complete")
    done_reason: Optional[str] = Field(default=None, description="Reason for completion: 'stop', 'length', or 'load'")
    context: Optional[List[int]] = Field(default=None, description="Context for continuing conversation")
    total_duration: Optional[int] = Field(default=None, description="Total time in nanoseconds")
    load_duration: Optional[int] = Field(default=None, description="Model load time in nanoseconds")
    prompt_eval_count: Optional[int] = Field(default=None, description="Number of tokens in prompt")
    prompt_eval_duration: Optional[int] = Field(default=None, description="Time to evaluate prompt in nanoseconds")
    eval_count: Optional[int] = Field(default=None, description="Number of tokens generated")
    eval_duration: Optional[int] = Field(default=None, description="Time to generate response in nanoseconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model": "llama2",
                "created_at": "2023-08-04T19:56:02.647Z",
                "response": "The sky appears blue because of a phenomenon called Rayleigh scattering.",
                "done": True,
                "done_reason": "stop",
                "context": [128006, 882, 128007],
                "total_duration": 5589157167,
                "load_duration": 3013701500,
                "prompt_eval_count": 26,
                "prompt_eval_duration": 342546000,
                "eval_count": 298,
                "eval_duration": 4956026000,
            }
        }
    )


class OllamaGenerateStreamChunk(BaseModel):
    """Response format for /api/generate endpoint (streaming chunk)."""

    model: str = Field(..., description="Model used for generation")
    created_at: str = Field(..., description="RFC3339 timestamp with timezone")
    response: str = Field(..., description="Generated text chunk")
    done: bool = Field(..., description="Whether generation is complete")
    # These fields are only present in the final chunk when done=True
    done_reason: Optional[str] = Field(default=None, description="Reason for completion (final chunk only)")
    context: Optional[List[int]] = Field(default=None, description="Context for continuation (final chunk only)")
    total_duration: Optional[int] = Field(default=None, description="Total time (final chunk only)")
    load_duration: Optional[int] = Field(default=None, description="Model load time (final chunk only)")
    prompt_eval_count: Optional[int] = Field(default=None, description="Prompt token count (final chunk only)")
    prompt_eval_duration: Optional[int] = Field(default=None, description="Prompt eval time (final chunk only)")
    eval_count: Optional[int] = Field(default=None, description="Generated token count (final chunk only)")
    eval_duration: Optional[int] = Field(default=None, description="Generation time (final chunk only)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"model": "llama2", "created_at": "2023-08-04T19:56:02.647Z", "response": "The", "done": False}
        }
    )


class OllamaChatMessage(BaseModel):
    """Chat message format."""

    role: str = Field(..., description="Message role: 'system', 'user', or 'assistant'")
    content: str = Field(..., description="Message content")
    images: Optional[List[str]] = Field(default=None, description="Base64 encoded images for multimodal models")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "user",
                "content": "Hello, how are you?",
            }
        }
    )


class OllamaChatRequest(BaseModel):
    """Request format for /api/chat endpoint."""

    model: str = Field(..., description="Model name/ID to use for chat")
    messages: List[OllamaChatMessage] = Field(..., description="Array of message objects")
    stream: Optional[bool] = Field(default=True, description="Whether to stream the response")
    format: Optional[str] = Field(default=None, description="Output format (e.g., 'json')")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Model parameters")
    keep_alive: Optional[str] = Field(default=None, description="How long to keep model loaded")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model": "llama2",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello!"},
                ],
                "stream": False,
                "options": {"temperature": 0.7},
            }
        }
    )


class OllamaChatResponse(BaseModel):
    """Response format for /api/chat endpoint (non-streaming)."""

    model: str = Field(..., description="Model used for chat")
    created_at: str = Field(..., description="RFC3339 timestamp with timezone")
    message: OllamaChatMessage = Field(..., description="Assistant's response message")
    done: bool = Field(..., description="Whether response is complete")
    done_reason: Optional[str] = Field(default=None, description="Reason for completion: 'stop', 'length', or 'load'")
    total_duration: Optional[int] = Field(default=None, description="Total time in nanoseconds")
    load_duration: Optional[int] = Field(default=None, description="Model load time in nanoseconds")
    prompt_eval_count: Optional[int] = Field(default=None, description="Number of tokens in prompt")
    prompt_eval_duration: Optional[int] = Field(default=None, description="Time to evaluate prompt in nanoseconds")
    eval_count: Optional[int] = Field(default=None, description="Number of tokens generated")
    eval_duration: Optional[int] = Field(default=None, description="Time to generate response in nanoseconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model": "llama2",
                "created_at": "2023-08-04T19:56:02.647Z",
                "message": {
                    "role": "assistant",
                    "content": "Hello! How can I help you today?",
                },
                "done": True,
                "done_reason": "stop",
                "total_duration": 1234567890,
                "load_duration": 123456789,
                "prompt_eval_count": 45,
                "prompt_eval_duration": 234567890,
                "eval_count": 120,
                "eval_duration": 890123456,
            }
        }
    )


class OllamaChatStreamChunk(BaseModel):
    """Response format for /api/chat endpoint (streaming chunk)."""

    model: str = Field(..., description="Model used for chat")
    created_at: str = Field(..., description="RFC3339 timestamp with timezone")
    message: OllamaChatMessage = Field(..., description="Partial message with accumulated content")
    done: bool = Field(..., description="Whether response is complete")
    # These fields are only present in the final chunk when done=True
    done_reason: Optional[str] = Field(default=None, description="Reason for completion (final chunk only)")
    total_duration: Optional[int] = Field(default=None, description="Total time (final chunk only)")
    load_duration: Optional[int] = Field(default=None, description="Model load time (final chunk only)")
    prompt_eval_count: Optional[int] = Field(default=None, description="Prompt token count (final chunk only)")
    prompt_eval_duration: Optional[int] = Field(default=None, description="Prompt eval time (final chunk only)")
    eval_count: Optional[int] = Field(default=None, description="Generated token count (final chunk only)")
    eval_duration: Optional[int] = Field(default=None, description="Generation time (final chunk only)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model": "llama2",
                "created_at": "2023-08-04T19:56:02.647Z",
                "message": {"role": "assistant", "content": "Hello"},
                "done": False,
            }
        }
    )
