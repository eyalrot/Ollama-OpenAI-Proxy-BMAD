"""OpenAI SDK client wrapper service."""
import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx
from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError
from openai.types import Model
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai.types.create_embedding_response import CreateEmbeddingResponse

from ..config import Settings
from ..exceptions import OpenAIError

logger = logging.getLogger(__name__)


class OpenAIService:
    """
    Wrapper service for OpenAI SDK client.
    
    Provides centralized OpenAI API access with:
    - Connection pooling
    - Retry logic with exponential backoff
    - Request/response logging
    - Error handling and translation
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize OpenAI service.
        
        Args:
            settings: Application settings with API configuration
        """
        self.settings = settings
        self._client: Optional[AsyncOpenAI] = None
        self._request_count = 0
        self._error_count = 0
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1.0  # Initial delay in seconds
        self.retry_multiplier = 2.0
        self.retry_max_delay = 30.0
    
    @property
    def client(self) -> AsyncOpenAI:
        """
        Get or create the OpenAI client.
        
        Returns:
            AsyncOpenAI: The configured client instance
        """
        if self._client is None:
            # Configure HTTP client with connection pooling
            http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    timeout=float(self.settings.request_timeout),
                    connect=10.0
                ),
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20
                )
            )
            
            self._client = AsyncOpenAI(
                api_key=self.settings.get_openai_api_key(),
                base_url=self.settings.openai_api_base_url,
                http_client=http_client,
                max_retries=0  # We handle retries ourselves
            )
            
            logger.info(
                "OpenAI client initialized",
                extra={
                    "base_url": self.settings.openai_api_base_url,
                    "timeout": self.settings.request_timeout
                }
            )
        
        return self._client
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID for tracking."""
        return f"req_{uuid.uuid4().hex[:8]}"
    
    def _should_retry(self, error: Exception) -> bool:
        """
        Determine if an error should trigger a retry.
        
        Args:
            error: The exception that occurred
            
        Returns:
            bool: True if should retry, False otherwise
        """
        # Retry on specific errors
        if isinstance(error, (APITimeoutError, RateLimitError)):
            return True
        
        # Retry on 5xx errors
        if isinstance(error, APIError) and error.status_code:
            return 500 <= error.status_code < 600
        
        # Retry on connection errors
        if isinstance(error, (httpx.ConnectError, httpx.ReadTimeout)):
            return True
        
        return False
    
    async def _execute_with_retry(
        self,
        operation: str,
        func: Any,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute an operation with retry logic.
        
        Args:
            operation: Name of the operation for logging
            func: The async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            The result of the function call
            
        Raises:
            OpenAIError: If all retries are exhausted
        """
        request_id = self._generate_request_id()
        attempt = 0
        delay = self.retry_delay
        
        logger.info(
            f"Starting {operation}",
            extra={"request_id": request_id}
        )
        
        while attempt <= self.max_retries:
            try:
                start_time = time.time()
                self._request_count += 1
                
                # Execute the operation
                result = await func(*args, **kwargs)
                
                # Log successful completion
                duration = time.time() - start_time
                logger.info(
                    f"Completed {operation}",
                    extra={
                        "request_id": request_id,
                        "duration_ms": round(duration * 1000),
                        "attempt": attempt + 1
                    }
                )
                
                return result
                
            except Exception as e:
                self._error_count += 1
                duration = time.time() - start_time
                
                logger.warning(
                    f"Error in {operation}",
                    extra={
                        "request_id": request_id,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "attempt": attempt + 1,
                        "duration_ms": round(duration * 1000)
                    }
                )
                
                # Check if we should retry
                if attempt < self.max_retries and self._should_retry(e):
                    attempt += 1
                    logger.info(
                        f"Retrying {operation}",
                        extra={
                            "request_id": request_id,
                            "attempt": attempt + 1,
                            "delay": delay
                        }
                    )
                    await asyncio.sleep(delay)
                    delay = min(delay * self.retry_multiplier, self.retry_max_delay)
                else:
                    # No more retries or non-retryable error
                    error_msg = f"Failed to {operation} after {attempt + 1} attempts: {str(e)}"
                    logger.error(
                        error_msg,
                        extra={
                            "request_id": request_id,
                            "final_error": True
                        }
                    )
                    raise OpenAIError(error_msg) from e
        
        # Should never reach here
        raise OpenAIError(f"Unexpected error in {operation}")
    
    async def list_models(self) -> List[Model]:
        """
        List available models from OpenAI.
        
        Returns:
            List[Model]: List of available models
            
        Raises:
            OpenAIError: If the API call fails
        """
        async def _list():
            response = await self.client.models.list()
            return list(response.data)
        
        return await self._execute_with_retry("list_models", _list)
    
    async def create_chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        stream: bool = False,
        **kwargs
    ) -> ChatCompletion:
        """
        Create a chat completion.
        
        Args:
            model: Model ID to use
            messages: List of message dictionaries
            stream: Whether to stream the response
            **kwargs: Additional parameters for the API
            
        Returns:
            ChatCompletion: The completion response
            
        Raises:
            OpenAIError: If the API call fails
        """
        async def _create():
            return await self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=stream,
                **kwargs
            )
        
        return await self._execute_with_retry(
            "create_chat_completion",
            _create
        )
    
    async def create_chat_completion_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncIterator[ChatCompletionChunk]:
        """
        Create a streaming chat completion.
        
        Args:
            model: Model ID to use
            messages: List of message dictionaries
            **kwargs: Additional parameters for the API
            
        Yields:
            ChatCompletionChunk: Streaming response chunks
            
        Raises:
            OpenAIError: If the API call fails
        """
        request_id = self._generate_request_id()
        
        logger.info(
            "Starting streaming chat completion",
            extra={"request_id": request_id, "model": model}
        )
        
        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                **kwargs
            )
            
            chunk_count = 0
            async for chunk in stream:
                chunk_count += 1
                yield chunk
            
            logger.info(
                "Completed streaming chat completion",
                extra={
                    "request_id": request_id,
                    "chunks": chunk_count
                }
            )
            
        except Exception as e:
            logger.error(
                "Error in streaming chat completion",
                extra={
                    "request_id": request_id,
                    "error": str(e)
                }
            )
            raise OpenAIError(f"Streaming error: {str(e)}") from e
    
    async def create_embedding(
        self,
        model: str,
        input: str,
        **kwargs
    ) -> CreateEmbeddingResponse:
        """
        Create embeddings for text.
        
        Args:
            model: Model ID to use
            input: Text to embed
            **kwargs: Additional parameters for the API
            
        Returns:
            CreateEmbeddingResponse: The embedding response
            
        Raises:
            OpenAIError: If the API call fails
        """
        async def _create():
            return await self.client.embeddings.create(
                model=model,
                input=input,
                **kwargs
            )
        
        return await self._execute_with_retry(
            "create_embedding",
            _create
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check by listing models.
        
        Returns:
            Dict with health status information
        """
        try:
            models = await self.list_models()
            return {
                "status": "healthy",
                "models_available": len(models),
                "request_count": self._request_count,
                "error_count": self._error_count,
                "error_rate": (
                    self._error_count / self._request_count 
                    if self._request_count > 0 else 0
                )
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "request_count": self._request_count,
                "error_count": self._error_count
            }
    
    async def close(self):
        """Close the client and cleanup resources."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("OpenAI client closed")


# Dependency injection helper
@asynccontextmanager
async def get_openai_service(settings: Settings) -> AsyncIterator[OpenAIService]:
    """
    Create and yield an OpenAI service instance.
    
    Args:
        settings: Application settings
        
    Yields:
        OpenAIService: Configured service instance
    """
    service = OpenAIService(settings)
    try:
        yield service
    finally:
        await service.close()