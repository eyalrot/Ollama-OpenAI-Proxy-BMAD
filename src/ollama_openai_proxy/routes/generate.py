"""Generate endpoint for Ollama API compatibility."""
import json
import logging
from typing import Any, AsyncIterator, Union

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from openai import (
    APIConnectionError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    RateLimitError,
)

from ollama_openai_proxy.models import (
    OllamaGenerateRequest,
    OllamaGenerateResponse,
)
from ollama_openai_proxy.services.enhanced_translation_service import (
    EnhancedTranslationService,
)
from ollama_openai_proxy.utils.errors import (
    create_simple_ollama_error,
    get_correlation_id,
    handle_streaming_error,
    translate_openai_error,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["generate"])


async def stream_generate_response(
    request: OllamaGenerateRequest,
    service: EnhancedTranslationService,
    openai_service: Any,
    correlation_id: str,
) -> AsyncIterator[str]:
    """Stream generate response as newline-delimited JSON."""
    try:
        # Validate request parameters
        if not request.prompt and not request.context:
            error_msg = "Either prompt or context must be provided"
            yield handle_streaming_error(ValueError(error_msg), request.model, correlation_id)
            return

        # Translate Ollama request to OpenAI format
        openai_request = await service.translate_generate_request(request)

        # Get streaming response from OpenAI (the method returns an async generator directly)
        stream = openai_service.create_chat_completion_stream(**openai_request)

        # Track generation for final chunk
        full_response = ""
        chunk_count = 0

        async for openai_chunk in stream:
            # Translate each chunk to Ollama format
            ollama_chunk = await service.translate_generate_stream_chunk(openai_chunk, request.model)

            if ollama_chunk.response:
                full_response += ollama_chunk.response
                chunk_count += 1

            # Yield chunk as newline-delimited JSON
            yield json.dumps(ollama_chunk.model_dump(exclude_none=True)) + "\n"

    except (RateLimitError, AuthenticationError, NotFoundError, BadRequestError, APIConnectionError) as e:
        # Handle specific OpenAI errors
        yield handle_streaming_error(e, request.model, correlation_id)
    except Exception as e:
        # Handle unexpected errors
        logger.error(
            f"Unexpected error in stream_generate_response: {e}",
            extra={
                "correlation_id": correlation_id,
                "model": request.model,
                "error_type": type(e).__name__,
            },
        )
        yield handle_streaming_error(e, request.model, correlation_id)


@router.post("/generate", response_model=None)
async def generate(
    request: OllamaGenerateRequest,
    req: Request,
) -> Union[OllamaGenerateResponse, StreamingResponse, JSONResponse]:
    """Generate text completion endpoint."""
    # Get correlation ID for request tracking
    correlation_id = get_correlation_id(req)

    # Add correlation ID to response headers
    headers = {"X-Correlation-ID": correlation_id}

    try:
        # Get services from app state
        openai_service = req.app.state.openai_service
        translation_service = EnhancedTranslationService()

        logger.info(
            "Generate request",
            extra={
                "correlation_id": correlation_id,
                "model": request.model,
                "prompt_length": len(request.prompt),
                "stream": request.stream,
            },
        )

        # Validate request parameters
        if not request.prompt and not request.context:
            error_response = create_simple_ollama_error("Either prompt or context must be provided")
            return JSONResponse(
                status_code=400,
                content=error_response,
                headers=headers,
            )

        # Handle streaming response
        if request.stream:
            return StreamingResponse(
                stream_generate_response(request, translation_service, openai_service, correlation_id),
                media_type="application/x-ndjson",
                headers=headers,
            )

        # Handle non-streaming response
        # Translate Ollama request to OpenAI format
        openai_request = await translation_service.translate_generate_request(request)

        # Get completion from OpenAI
        openai_response = await openai_service.create_chat_completion(**openai_request)

        # Translate OpenAI response to Ollama format
        ollama_response = await translation_service.translate_generate_response(openai_response, request.model)

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
            "Unexpected error in generate endpoint",
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
