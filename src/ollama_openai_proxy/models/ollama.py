"""Ollama API data models."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class OllamaModel(BaseModel):
    """Model information in Ollama format."""
    
    name: str = Field(..., description="Model name/ID")
    modified_at: str = Field(..., description="ISO format timestamp")
    size: int = Field(..., description="Model size in bytes")
    digest: Optional[str] = Field(default="", description="Model digest/hash")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "name": "gpt-3.5-turbo",
                "modified_at": "2024-01-20T10:30:00Z",
                "size": 1000000000,
                "digest": "sha256:abcdef123456"
            }
        }


class OllamaTagsResponse(BaseModel):
    """Response format for /api/tags endpoint."""
    
    models: List[OllamaModel] = Field(
        default_factory=list,
        description="List of available models"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "models": [
                    {
                        "name": "gpt-3.5-turbo",
                        "modified_at": "2024-01-20T10:30:00Z",
                        "size": 1000000000
                    },
                    {
                        "name": "gpt-4",
                        "modified_at": "2024-01-20T10:30:00Z",
                        "size": 2000000000
                    }
                ]
            }
        }


class OllamaError(BaseModel):
    """Error response in Ollama format."""
    
    error: str = Field(..., description="Error message")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "error": "model not found"
            }
        }