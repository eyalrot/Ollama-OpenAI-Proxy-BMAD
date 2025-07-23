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
