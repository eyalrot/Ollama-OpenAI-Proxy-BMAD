"""Generate endpoint for Ollama API compatibility."""
import json
import logging
from typing import Any, AsyncIterator, Union

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from ollama_openai_proxy.models import (
    OllamaGenerateRequest,
    OllamaGenerateResponse,
)
from ollama_openai_proxy.services.enhanced_translation_service import (
    EnhancedTranslationService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["generate"])


async def stream_generate_response(
    request: OllamaGenerateRequest,
    service: EnhancedTranslationService,
    openai_service: Any,
) -> AsyncIterator[str]:
    """Stream generate response as newline-delimited JSON."""
    try:
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

    except Exception as e:
        logger.error(f"Error in stream_generate_response: {e}")
        error_chunk = {"error": str(e), "done": True}
        yield json.dumps(error_chunk) + "\n"


@router.post("/generate", response_model=None)
async def generate(
    request: OllamaGenerateRequest,
    req: Request,
) -> Union[OllamaGenerateResponse, StreamingResponse]:
    """Generate text completion endpoint."""
    try:
        # Get services from app state
        openai_service = req.app.state.openai_service
        translation_service = EnhancedTranslationService()

        logger.info(
            f"Generate request - model: {request.model}, "
            f"prompt_length: {len(request.prompt)}, "
            f"stream: {request.stream}"
        )

        # Handle streaming response
        if request.stream:
            return StreamingResponse(
                stream_generate_response(request, translation_service, openai_service),
                media_type="application/x-ndjson",
            )

        # Handle non-streaming response
        # Translate Ollama request to OpenAI format
        openai_request = await translation_service.translate_generate_request(request)

        # Get completion from OpenAI
        openai_response = await openai_service.create_chat_completion(**openai_request)

        # Translate OpenAI response to Ollama format
        ollama_response = await translation_service.translate_generate_response(openai_response, request.model)

        return ollama_response

    except ValueError as e:
        logger.error(f"Validation error in generate: {e}")
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error in generate endpoint: {e}")
        raise HTTPException(status_code=500, detail={"error": f"Failed to generate: {e!s}"}) from e
