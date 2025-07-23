# Story 1.4: Implement /api/tags Endpoint

**Story Points**: 3  
**Priority**: P0 (First user-facing endpoint)  
**Type**: Feature  
**Dependencies**: Stories 1.1, 1.2, 1.3 must be complete

## Story Summary
**As an** Ollama SDK user,  
**I want to** list available models using the standard client.list() method,  
**So that** I can discover what models are available through the proxy.

## Technical Implementation Guide

### Pre-Implementation Checklist
- [ ] OpenAI service wrapper (Story 1.3) is working
- [ ] Virtual environment activated
- [ ] Can successfully call OpenAI API via service

### Implementation Steps

#### Step 1: Create Ollama Data Models
**src/ollama_openai_proxy/models/__init__.py**:
```python
"""Data models for Ollama API compatibility."""
```

**src/ollama_openai_proxy/models/ollama.py**:
```python
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
```

#### Step 2: Create Translation Service
**src/ollama_openai_proxy/services/translation_service.py**:
```python
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
            "babbage",
            "ada"
        )
        
        model_id_lower = model.id.lower()
        
        # Check exclusions first
        if any(keyword in model_id_lower for keyword in exclude_keywords):
            return False
        
        # Check inclusions
        return any(model_id_lower.startswith(prefix) for prefix in include_prefixes)
```

#### Step 3: Create API Router
**src/ollama_openai_proxy/routes/__init__.py**:
```python
"""API routes for Ollama-OpenAI Proxy."""
```

**src/ollama_openai_proxy/routes/tags.py**:
```python
"""Tags endpoint for listing models."""
import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from fastapi.responses import JSONResponse

from ..config import Settings
from ..models.ollama import OllamaError, OllamaTagsResponse
from ..services.openai_service import OpenAIService
from ..services.translation_service import TranslationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Models"])


async def get_settings() -> Settings:
    """Dependency to get settings from app state."""
    from ..main import app
    return app.state.settings


async def get_openai_service() -> OpenAIService:
    """Dependency to get OpenAI service from app state."""
    from ..main import app
    return app.state.openai_service


@router.get(
    "/tags",
    response_model=OllamaTagsResponse,
    responses={
        200: {
            "description": "List of available models",
            "model": OllamaTagsResponse
        },
        500: {
            "description": "Internal server error",
            "model": OllamaError
        },
        503: {
            "description": "OpenAI API unavailable",
            "model": OllamaError
        }
    }
)
async def list_models(
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
    openai_service: Annotated[OpenAIService, Depends(get_openai_service)],
    user_agent: Annotated[str | None, Header()] = None,
) -> OllamaTagsResponse:
    """
    List available models in Ollama format.
    
    This endpoint is called by Ollama SDK's client.list() method.
    It fetches models from OpenAI and translates them to Ollama format.
    """
    start_time = time.time()
    
    logger.info(
        "Listing models",
        extra={
            "endpoint": "/api/tags",
            "user_agent": user_agent
        }
    )
    
    try:
        # Fetch models from OpenAI
        openai_models = await openai_service.list_models()
        
        # Translate to Ollama format
        ollama_response = TranslationService.translate_model_list(openai_models)
        
        # Add cache headers to reduce API calls
        response.headers["Cache-Control"] = "public, max-age=300"  # Cache for 5 minutes
        response.headers["X-Model-Count"] = str(len(ollama_response.models))
        
        # Log performance metrics
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "Successfully listed models",
            extra={
                "endpoint": "/api/tags",
                "model_count": len(ollama_response.models),
                "duration_ms": round(duration_ms, 2)
            }
        )
        
        return ollama_response
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            "Failed to list models",
            extra={
                "endpoint": "/api/tags",
                "error": str(e),
                "error_type": type(e).__name__,
                "duration_ms": round(duration_ms, 2)
            }
        )
        
        # Determine appropriate status code
        status_code = 503 if "connection" in str(e).lower() else 500
        
        # Return Ollama-formatted error
        raise HTTPException(
            status_code=status_code,
            detail={"error": f"Failed to fetch models: {str(e)}"}
        )
```

#### Step 4: Update Main Application
Update **src/ollama_openai_proxy/main.py** to include the router:
```python
# Add to imports
from .routes import tags

# After creating the app, add the router
app.include_router(tags.router)
```

#### Step 5: Create Unit Tests
**tests/unit/test_translation_service.py**:
```python
"""Tests for translation service."""
from datetime import datetime

import pytest
from openai.types import Model

from ollama_openai_proxy.models.ollama import OllamaModel, OllamaTagsResponse
from ollama_openai_proxy.services.translation_service import TranslationService


class TestTranslationService:
    """Test translation service functionality."""
    
    def test_openai_to_ollama_model(self):
        """Test single model translation."""
        openai_model = Model(
            id="gpt-3.5-turbo",
            created=1234567890,
            object="model",
            owned_by="openai"
        )
        
        ollama_model = TranslationService.openai_to_ollama_model(openai_model)
        
        assert isinstance(ollama_model, OllamaModel)
        assert ollama_model.name == "gpt-3.5-turbo"
        assert ollama_model.size == 1_500_000_000  # Known size
        assert ollama_model.digest == "openai:gpt-3.5-turbo"
        assert ollama_model.modified_at.endswith("Z")
    
    def test_translate_model_list(self):
        """Test translating list of models."""
        openai_models = [
            Model(id="gpt-3.5-turbo", created=1234567890, object="model", owned_by="openai"),
            Model(id="gpt-4", created=1234567891, object="model", owned_by="openai"),
            Model(id="text-embedding-ada-002", created=1234567892, object="model", owned_by="openai"),
        ]
        
        response = TranslationService.translate_model_list(openai_models)
        
        assert isinstance(response, OllamaTagsResponse)
        assert len(response.models) == 3
        assert response.models[0].name == "gpt-3.5-turbo"
        assert response.models[1].name == "gpt-4"
        assert response.models[2].name == "text-embedding-ada-002"
    
    def test_should_include_model(self):
        """Test model filtering logic."""
        # Should include
        assert TranslationService._should_include_model(
            Model(id="gpt-3.5-turbo", created=1, object="model", owned_by="openai")
        )
        assert TranslationService._should_include_model(
            Model(id="text-embedding-3-large", created=1, object="model", owned_by="openai")
        )
        
        # Should exclude
        assert not TranslationService._should_include_model(
            Model(id="davinci-002", created=1, object="model", owned_by="openai")
        )
        assert not TranslationService._should_include_model(
            Model(id="gpt-3.5-turbo-instruct", created=1, object="model", owned_by="openai")
        )
    
    def test_unknown_model_size(self):
        """Test handling of unknown model."""
        openai_model = Model(
            id="future-model-xyz",
            created=1234567890,
            object="model",
            owned_by="openai"
        )
        
        ollama_model = TranslationService.openai_to_ollama_model(openai_model)
        
        assert ollama_model.size == TranslationService.DEFAULT_MODEL_SIZE
    
    def test_empty_model_list(self):
        """Test handling empty model list."""
        response = TranslationService.translate_model_list([])
        
        assert isinstance(response, OllamaTagsResponse)
        assert len(response.models) == 0
```

**tests/integration/test_tags_endpoint.py**:
```python
"""Integration tests for /api/tags endpoint."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from ollama_openai_proxy.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_openai_models():
    """Mock OpenAI models response."""
    from openai.types import Model
    
    return [
        Model(id="gpt-3.5-turbo", created=1234567890, object="model", owned_by="openai"),
        Model(id="gpt-4", created=1234567891, object="model", owned_by="openai"),
    ]


class TestTagsEndpoint:
    """Test /api/tags endpoint."""
    
    def test_list_models_success(self, client, mock_openai_models, monkeypatch):
        """Test successful model listing."""
        # Mock environment
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        
        with patch("ollama_openai_proxy.services.openai_service.OpenAIService.list_models") as mock_list:
            mock_list.return_value = mock_openai_models
            
            response = client.get("/api/tags")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "models" in data
            assert len(data["models"]) == 2
            assert data["models"][0]["name"] == "gpt-3.5-turbo"
            assert data["models"][1]["name"] == "gpt-4"
            
            # Check cache headers
            assert "Cache-Control" in response.headers
            assert response.headers["X-Model-Count"] == "2"
    
    def test_list_models_empty(self, client, monkeypatch):
        """Test empty model list."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        
        with patch("ollama_openai_proxy.services.openai_service.OpenAIService.list_models") as mock_list:
            mock_list.return_value = []
            
            response = client.get("/api/tags")
            
            assert response.status_code == 200
            data = response.json()
            assert data["models"] == []
    
    def test_list_models_error(self, client, monkeypatch):
        """Test error handling."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        
        with patch("ollama_openai_proxy.services.openai_service.OpenAIService.list_models") as mock_list:
            mock_list.side_effect = Exception("API Error")
            
            response = client.get("/api/tags")
            
            assert response.status_code == 500
            data = response.json()
            assert "error" in data["detail"]
            assert "Failed to fetch models" in data["detail"]["error"]
    
    def test_response_format(self, client, mock_openai_models, monkeypatch):
        """Test response matches Ollama format exactly."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        
        with patch("ollama_openai_proxy.services.openai_service.OpenAIService.list_models") as mock_list:
            mock_list.return_value = mock_openai_models
            
            response = client.get("/api/tags")
            data = response.json()
            
            # Verify structure matches Ollama
            assert isinstance(data, dict)
            assert "models" in data
            assert isinstance(data["models"], list)
            
            # Verify model structure
            for model in data["models"]:
                assert "name" in model
                assert "modified_at" in model
                assert "size" in model
                assert isinstance(model["size"], int)
                assert model["modified_at"].endswith("Z")  # ISO format with Z
```

#### Step 6: Test with Ollama SDK
Create **tests/integration/test_ollama_sdk_compatibility.py**:
```python
"""Test compatibility with official Ollama SDK."""
import os
import pytest
from unittest.mock import patch

# Only run these tests if ollama package is installed
ollama = pytest.importorskip("ollama")


@pytest.fixture
def ollama_client(monkeypatch):
    """Create Ollama client pointing to our proxy."""
    # Set test API key
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    
    # Point Ollama client to our proxy
    client = ollama.Client(host="http://localhost:11434")
    return client


@pytest.mark.asyncio
async def test_ollama_list_models(ollama_client):
    """Test Ollama SDK list() method works with our proxy."""
    from openai.types import Model
    
    mock_models = [
        Model(id="gpt-3.5-turbo", created=1234567890, object="model", owned_by="openai"),
        Model(id="gpt-4", created=1234567891, object="model", owned_by="openai"),
    ]
    
    with patch("ollama_openai_proxy.services.openai_service.OpenAIService.list_models") as mock_list:
        mock_list.return_value = mock_models
        
        # Use Ollama SDK to list models
        models = ollama_client.list()
        
        # Verify response structure
        assert "models" in models
        assert len(models["models"]) == 2
        
        # Verify model format
        model = models["models"][0]
        assert model["name"] == "gpt-3.5-turbo"
        assert "modified_at" in model
        assert "size" in model
```

### Verification Steps

1. **Test the endpoint manually:**
   ```bash
   # Start the service
   python -m ollama_openai_proxy
   
   # Test with curl
   curl http://localhost:11434/api/tags | jq
   ```

2. **Run unit tests:**
   ```bash
   pytest tests/unit/test_translation_service.py -v
   pytest tests/integration/test_tags_endpoint.py -v
   ```

3. **Test with Ollama Python SDK:**
   ```python
   import ollama
   
   # Point to your proxy
   client = ollama.Client(host="http://localhost:11434")
   
   # List models
   models = client.list()
   print(models)
   ```

4. **Test with Ollama CLI:**
   ```bash
   # Set Ollama host to proxy
   export OLLAMA_HOST=http://localhost:11434
   
   # List models
   ollama list
   ```

5. **Verify caching:**
   ```bash
   # First request (hits OpenAI)
   time curl http://localhost:11434/api/tags
   
   # Second request (should be faster due to cache)
   time curl http://localhost:11434/api/tags
   ```

### Definition of Done Checklist

- [ ] GET /api/tags endpoint implemented
- [ ] Endpoint calls OpenAI list_models via service wrapper
- [ ] Response translated to exact Ollama format
- [ ] Model filtering excludes non-relevant models
- [ ] Cache headers reduce API calls
- [ ] Performance logging tracks response time
- [ ] Error responses use Ollama error format
- [ ] Unit tests cover translation logic
- [ ] Integration tests verify endpoint behavior
- [ ] Ollama SDK successfully lists models through proxy
- [ ] Response time logged for monitoring

### Common Issues & Solutions

1. **Models not showing in Ollama:**
   - Check model filtering logic
   - Verify response format matches exactly
   - Ensure modified_at has trailing 'Z'

2. **Ollama CLI connection refused:**
   - Verify proxy is running on port 11434
   - Check OLLAMA_HOST environment variable

3. **Empty model list:**
   - Verify OpenAI API key is valid
   - Check OpenAI service is returning models
   - Review filtering logic

### Performance Notes

- Cache headers reduce OpenAI API calls
- Model size estimates prevent additional API calls
- Translation is a pure function (fast)
- Consider Redis cache for production

### Next Steps

After completing this story:
1. Test with real Ollama SDK
2. Verify all acceptance criteria met
3. Commit changes
4. Create PR for review
5. Move to Story 1.5: Translation Engine for Model Listing