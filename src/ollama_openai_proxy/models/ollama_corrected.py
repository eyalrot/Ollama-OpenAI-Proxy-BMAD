"""
Corrected Ollama API data models that match the actual API specification.

Based on analysis of the Postman collection, the actual Ollama API
returns BOTH 'name' and 'model' fields with the same value.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class OllamaModelCorrected(BaseModel):
    """Model information in corrected Ollama format."""

    name: str = Field(..., description="Model name/ID")
    model: str = Field(..., description="Model name/ID (duplicate of name field)")
    modified_at: str = Field(..., description="RFC3339 timestamp with timezone")
    size: int = Field(..., description="Model size in bytes")
    digest: str = Field(..., description="Model digest/hash (sha256:...)")
    details: Optional[Dict[str, Any]] = Field(
        default_factory=dict,  # type: ignore[arg-type]
        description="Optional model details",
    )

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


class OllamaTagsResponseCorrected(BaseModel):
    """Corrected response format for /api/tags endpoint."""

    models: List[OllamaModelCorrected] = Field(
        default_factory=list, description="List of available models"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "models": [
                    {
                        "name": "llama3.1:latest",
                        "model": "llama3.1:latest",
                        "modified_at": "2025-01-21T16:53:57.496699591-08:00",
                        "size": 4920753328,
                        "digest": (
                            "sha256:46e0c10c039e019119339687c3c1757"
                            "cc81b9da49709a3b3924863ba87ca666e"
                        ),
                        "details": {
                            "parent_model": "",
                            "format": "gguf",
                            "family": "llama",
                            "families": ["llama"],
                            "parameter_size": "8.0B",
                            "quantization_level": "Q4_K_M",
                        },
                    }
                ]
            }
        }
    )


class ModelDetails(BaseModel):
    """Detailed model information from /api/show endpoint."""

    parent_model: str = Field(default="", description="Parent model if any")
    format: str = Field(default="gguf", description="Model format")
    family: str = Field(default="", description="Model family")
    families: Optional[List[str]] = Field(default=None, description="Model families")
    parameter_size: str = Field(default="", description="Parameter count (e.g., '7B')")
    quantization_level: str = Field(default="", description="Quantization (e.g., 'Q4_K_M')")


def convert_openai_to_ollama_corrected(
    openai_model_id: str, created_timestamp: int, size_estimate: int, digest: str
) -> OllamaModelCorrected:
    """
    Convert OpenAI model to corrected Ollama format.

    Args:
        openai_model_id: OpenAI model ID (e.g., "gpt-3.5-turbo")
        created_timestamp: Unix timestamp
        size_estimate: Estimated size in bytes
        digest: Model digest (sha256:...)

    Returns:
        OllamaModelCorrected with both name and model fields
    """
    # Convert timestamp to RFC3339 with timezone
    created_dt = datetime.fromtimestamp(created_timestamp)
    # Use timezone offset format instead of just 'Z'
    modified_at = created_dt.strftime("%Y-%m-%dT%H:%M:%S.%f") + "-00:00"

    return OllamaModelCorrected(
        name=openai_model_id,
        model=openai_model_id,  # Duplicate!
        modified_at=modified_at,
        size=size_estimate,
        digest=digest,
        details={
            "parent_model": "",
            "format": "gguf",
            "family": "gpt" if "gpt" in openai_model_id else "unknown",
            "families": ["gpt"] if "gpt" in openai_model_id else [],
            "parameter_size": _estimate_parameter_size(openai_model_id),
            "quantization_level": "Q4_K_M",  # Default for OpenAI models
        },
    )


def _estimate_parameter_size(model_id: str) -> str:
    """Estimate parameter size from model ID."""
    size_map = {
        "gpt-3.5": "3.5B",
        "gpt-4": "175B",
        "gpt-4-turbo": "175B",
        "text-embedding-ada-002": "1.3B",
        "text-embedding-3-small": "1.3B",
        "text-embedding-3-large": "3B",
    }

    for key, size in size_map.items():
        if key in model_id:
            return size
    return "Unknown"
