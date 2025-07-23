"""Tags endpoint for listing models."""
import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from fastapi.responses import JSONResponse

from ..config import Settings
from ..models.ollama import OllamaError, OllamaTagsResponse
from ..services.openai_service import OpenAIService
from ..services.enhanced_translation_service import EnhancedTranslationService

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
        
        # Translate to Ollama format using enhanced service
        ollama_response = EnhancedTranslationService.translate_with_metadata(
            openai_models,
            include_metadata=False  # Keep response lean for now
        )
        
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