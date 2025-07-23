"""Embeddings endpoints for Ollama API compatibility."""
import logging
from typing import Union

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from openai import (
    APIConnectionError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    RateLimitError,
)

from ollama_openai_proxy.models.ollama import (
    OllamaEmbeddingsRequest,
    OllamaEmbeddingsResponse,
)
from ollama_openai_proxy.services.enhanced_translation_service import (
    EnhancedTranslationService,
)
from ollama_openai_proxy.utils.errors import (
    create_simple_ollama_error,
    get_correlation_id,
    translate_openai_error,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["embeddings"])


async def handle_embeddings(
    request: OllamaEmbeddingsRequest,
    req: Request,
) -> Union[OllamaEmbeddingsResponse, JSONResponse]:
    """Common handler for both embeddings endpoints."""
    # Get correlation ID for request tracking
    correlation_id = get_correlation_id(req)

    # Add correlation ID to response headers
    headers = {"X-Correlation-ID": correlation_id}

    try:
        # Get services from app state
        openai_service = req.app.state.openai_service
        translation_service = EnhancedTranslationService()

        logger.info(
            "Embeddings request",
            extra={
                "correlation_id": correlation_id,
                "model": request.model,
                "prompt_length": len(request.prompt),
            },
        )

        # Validate request parameters
        if not request.prompt:
            error_response = create_simple_ollama_error("Prompt cannot be empty")
            return JSONResponse(
                status_code=400,
                content=error_response,
                headers=headers,
            )

        # Translate Ollama request to OpenAI format
        openai_request = await translation_service.translate_embeddings_request(request)

        # Get embeddings from OpenAI
        openai_response = await openai_service.create_embedding(**openai_request)

        # Translate OpenAI response to Ollama format
        ollama_response = await translation_service.translate_embeddings_response(openai_response)

        return ollama_response

    except RateLimitError as e:
        # Handle rate limit errors
        error_data = translate_openai_error(e, request.model, correlation_id)
        return JSONResponse(
            status_code=429,
            content=create_simple_ollama_error(error_data["error"]["message"]),
            headers=headers,
        )

    except AuthenticationError as e:
        # Handle authentication errors
        error_data = translate_openai_error(e, request.model, correlation_id)
        return JSONResponse(
            status_code=401,
            content=create_simple_ollama_error(error_data["error"]["message"]),
            headers=headers,
        )

    except NotFoundError as e:
        # Handle model not found errors
        error_data = translate_openai_error(e, request.model, correlation_id)
        return JSONResponse(
            status_code=404,
            content=create_simple_ollama_error(error_data["error"]["message"]),
            headers=headers,
        )

    except BadRequestError as e:
        # Handle bad request errors
        error_data = translate_openai_error(e, request.model, correlation_id)
        return JSONResponse(
            status_code=400,
            content=create_simple_ollama_error(error_data["error"]["message"]),
            headers=headers,
        )

    except APIConnectionError as e:
        # Handle connection errors
        error_data = translate_openai_error(e, request.model, correlation_id)
        return JSONResponse(
            status_code=503,
            content=create_simple_ollama_error("Service temporarily unavailable"),
            headers=headers,
        )

    except TimeoutError as e:
        # Handle timeout errors
        logger.error(
            "Request timeout",
            extra={
                "correlation_id": correlation_id,
                "model": request.model,
                "error": str(e),
            },
        )
        return JSONResponse(
            status_code=504,
            content=create_simple_ollama_error("Request timed out"),
            headers=headers,
        )

    except ValueError as e:
        # Handle validation errors
        logger.error(
            "Validation error",
            extra={
                "correlation_id": correlation_id,
                "model": request.model,
                "error": str(e),
            },
        )
        return JSONResponse(
            status_code=422,
            content=create_simple_ollama_error(str(e)),
            headers=headers,
        )

    except Exception as e:
        # Handle unexpected errors
        logger.error(
            "Unexpected error in embeddings endpoint",
            extra={
                "correlation_id": correlation_id,
                "model": request.model,
                "error_type": type(e).__name__,
                "error": str(e),
            },
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content=create_simple_ollama_error("Internal server error"),
            headers=headers,
        )


@router.post("/embeddings", response_model=None)
async def embeddings(
    request: OllamaEmbeddingsRequest,
    req: Request,
) -> Union[OllamaEmbeddingsResponse, JSONResponse]:
    """Generate embeddings endpoint."""
    return await handle_embeddings(request, req)


@router.post("/embed", response_model=None)
async def embed(
    request: OllamaEmbeddingsRequest,
    req: Request,
) -> Union[OllamaEmbeddingsResponse, JSONResponse]:
    """Generate embeddings endpoint (alias)."""
    return await handle_embeddings(request, req)
