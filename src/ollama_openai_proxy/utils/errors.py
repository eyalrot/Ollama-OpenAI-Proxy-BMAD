"""Error handling utilities for Ollama-OpenAI proxy."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import Request
from ollama_openai_proxy.models.ollama import OllamaErrorDetails, OllamaErrorResponse
from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableEntityError,
)

logger = logging.getLogger(__name__)


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracking."""
    return f"req_{uuid.uuid4().hex[:12]}"


def get_correlation_id(request: Request) -> str:
    """Get or generate correlation ID from request."""
    # Check for existing correlation ID in headers
    correlation_id = request.headers.get("x-correlation-id") or request.headers.get("x-request-id")

    if not correlation_id:
        # Generate new one if not present
        correlation_id = generate_correlation_id()

    return correlation_id


def translate_openai_error(
    error: Exception,
    model: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Translate OpenAI SDK exceptions to Ollama error format.

    Args:
        error: The OpenAI SDK exception
        model: The model that was requested
        correlation_id: Request correlation ID

    Returns:
        Dictionary with Ollama error format
    """
    if not correlation_id:
        correlation_id = generate_correlation_id()

    # Default error info
    error_type = "unknown_error"
    status_code = 500
    message = str(error)
    details = {}

    # Map specific OpenAI errors
    if isinstance(error, RateLimitError):
        error_type = "rate_limit_error"
        status_code = 429
        message = "Rate limit exceeded. Please try again later."
        # Extract retry-after if available
        if hasattr(error, "response") and hasattr(error.response, "headers"):
            retry_after = error.response.headers.get("retry-after")
            if retry_after:
                details["retry_after"] = int(retry_after)

    elif isinstance(error, AuthenticationError):
        error_type = "authentication_error"
        status_code = 401
        message = "Authentication failed. Please check your API key."

    elif isinstance(error, NotFoundError):
        error_type = "model_not_found"
        status_code = 404
        message = f"The model '{model or 'requested'}' does not exist or you do not have access to it."

    elif isinstance(error, BadRequestError):
        error_type = "invalid_request_error"
        status_code = 400
        message = "Invalid request parameters."
        if hasattr(error, "body") and isinstance(error.body, dict):
            details = error.body.get("error", {}).get("details", {})

    elif isinstance(error, PermissionDeniedError):
        error_type = "permission_denied"
        status_code = 403
        message = "Permission denied. You do not have access to this resource."

    elif isinstance(error, ConflictError):
        error_type = "conflict_error"
        status_code = 409
        message = "Request conflicts with current state."

    elif isinstance(error, UnprocessableEntityError):
        error_type = "validation_error"
        status_code = 422
        message = "Request validation failed."

    elif isinstance(error, InternalServerError):
        error_type = "internal_server_error"
        status_code = 500
        message = "An internal server error occurred."

    elif isinstance(error, APIConnectionError):
        error_type = "connection_error"
        status_code = 503
        message = "Failed to connect to the API service."

    elif isinstance(error, APIStatusError):
        # Generic API status error
        status_code = error.status_code if hasattr(error, "status_code") else 500
        error_type = f"api_error_{status_code}"

    elif isinstance(error, TimeoutError):
        error_type = "timeout_error"
        status_code = 504
        message = "Request timed out."

    # Log the error with context
    logger.error(
        f"API Error: {error_type}",
        extra={
            "correlation_id": correlation_id,
            "error_type": error_type,
            "status_code": status_code,
            "model": model,
            "error_details": str(error),
        },
    )

    # Build Ollama error response
    error_response = {
        "error": {
            "message": message,
            "type": error_type,
            "code": status_code,
        },
        "correlation_id": correlation_id,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

    if details:
        # Type ignore needed as dict construction is dynamic
        error_response["error"]["details"] = details  # type: ignore[index]

    if model:
        error_response["model"] = model

    return error_response


def create_ollama_error_response(
    message: str,
    error_type: str = "error",
    status_code: int = 500,
    model: Optional[str] = None,
    correlation_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> OllamaErrorResponse:
    """Create an Ollama error response object.

    Args:
        message: Human-readable error message
        error_type: Type of error
        status_code: HTTP status code
        model: Model that was requested
        correlation_id: Request correlation ID
        details: Additional error details

    Returns:
        OllamaErrorResponse object
    """
    if not correlation_id:
        correlation_id = generate_correlation_id()

    error_details = OllamaErrorDetails(
        message=message,
        type=error_type,
        code=status_code,
        details=details,
    )

    return OllamaErrorResponse(
        error=error_details,
        correlation_id=correlation_id,
        model=model,
        created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )


def create_simple_ollama_error(message: str) -> Dict[str, str]:
    """Create a simple Ollama error response (just error field).

    This matches the basic Ollama error format for backwards compatibility.

    Args:
        message: Error message

    Returns:
        Dictionary with error field
    """
    return {"error": message}


def handle_streaming_error(
    error: Exception,
    model: str,
    correlation_id: Optional[str] = None,
) -> str:
    """Format error for streaming response.

    Args:
        error: The exception that occurred
        model: Model being used
        correlation_id: Request correlation ID

    Returns:
        JSON string formatted as streaming error chunk
    """
    import json

    if not correlation_id:
        correlation_id = generate_correlation_id()

    # Log the streaming error
    logger.error(
        f"Streaming error: {type(error).__name__}",
        extra={
            "correlation_id": correlation_id,
            "model": model,
            "error": str(error),
        },
    )

    # Create error chunk in streaming format
    error_chunk = {
        "model": model,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "response": "",  # Empty response
        "done": True,
        "error": str(error),
        "correlation_id": correlation_id,
    }

    return json.dumps(error_chunk) + "\n"
