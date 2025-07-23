# Story 1.3: OpenAI SDK Client Wrapper

**Story Points**: 3  
**Priority**: P0 (Required before endpoints)  
**Type**: Feature  
**Dependencies**: Story 1.2 must be complete

## Story Summary
**As a** developer,  
**I want to** create a wrapper around the OpenAI SDK client,  
**So that** I can manage API communication consistently.

## Technical Implementation Guide

### Pre-Implementation Checklist
- [ ] Story 1.2 complete (configuration management working)
- [ ] Virtual environment activated
- [ ] OpenAI SDK installed via requirements.txt

### Implementation Steps

#### Step 1: Create OpenAI Client Service
**src/ollama_openai_proxy/services/__init__.py**:
```python
"""Services package for Ollama-OpenAI Proxy."""
```

**src/ollama_openai_proxy/services/openai_service.py**:
```python
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
```

#### Step 2: Create Unit Tests
**tests/unit/test_openai_service.py**:
```python
"""Tests for OpenAI service wrapper."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import APIError, APITimeoutError, RateLimitError
from openai.types import Model

from ollama_openai_proxy.config import Settings
from ollama_openai_proxy.exceptions import OpenAIError
from ollama_openai_proxy.services.openai_service import OpenAIService


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = MagicMock(spec=Settings)
    settings.get_openai_api_key.return_value = "test-api-key"
    settings.openai_api_base_url = "https://api.test.com/v1"
    settings.request_timeout = 30
    return settings


@pytest.fixture
def openai_service(mock_settings):
    """Create OpenAI service with mock settings."""
    return OpenAIService(mock_settings)


class TestOpenAIService:
    """Test OpenAI service functionality."""
    
    def test_initialization(self, openai_service, mock_settings):
        """Test service initialization."""
        assert openai_service.settings == mock_settings
        assert openai_service._client is None
        assert openai_service._request_count == 0
        assert openai_service._error_count == 0
    
    def test_client_lazy_initialization(self, openai_service):
        """Test client is created on first access."""
        assert openai_service._client is None
        
        with patch("ollama_openai_proxy.services.openai_service.AsyncOpenAI") as mock_client:
            client = openai_service.client
            assert client is not None
            assert openai_service._client is not None
            mock_client.assert_called_once()
    
    def test_generate_request_id(self, openai_service):
        """Test request ID generation."""
        id1 = openai_service._generate_request_id()
        id2 = openai_service._generate_request_id()
        
        assert id1.startswith("req_")
        assert id2.startswith("req_")
        assert id1 != id2
        assert len(id1) == 12  # "req_" + 8 hex chars
    
    @pytest.mark.parametrize("error,should_retry", [
        (APITimeoutError("Timeout"), True),
        (RateLimitError("Rate limited", response=None, body=None), True),
        (APIError("Server error", response=None, body=None, code=503), True),
        (APIError("Bad request", response=None, body=None, code=400), False),
        (ValueError("Invalid input"), False),
    ])
    def test_should_retry(self, openai_service, error, should_retry):
        """Test retry logic for different errors."""
        # Mock status_code property for APIError
        if isinstance(error, APIError):
            error.status_code = error.code
        
        assert openai_service._should_retry(error) == should_retry
    
    @pytest.mark.asyncio
    async def test_list_models_success(self, openai_service):
        """Test successful model listing."""
        mock_models = [
            Model(id="gpt-3.5-turbo", created=1234567890, object="model", owned_by="openai"),
            Model(id="gpt-4", created=1234567891, object="model", owned_by="openai"),
        ]
        
        with patch.object(openai_service, "client") as mock_client:
            mock_response = MagicMock()
            mock_response.data = mock_models
            mock_client.models.list = AsyncMock(return_value=mock_response)
            
            models = await openai_service.list_models()
            
            assert len(models) == 2
            assert models[0].id == "gpt-3.5-turbo"
            assert models[1].id == "gpt-4"
            assert openai_service._request_count == 1
            assert openai_service._error_count == 0
    
    @pytest.mark.asyncio
    async def test_retry_on_timeout(self, openai_service):
        """Test retry logic on timeout errors."""
        with patch.object(openai_service, "client") as mock_client:
            # First two calls timeout, third succeeds
            mock_client.models.list = AsyncMock(
                side_effect=[
                    APITimeoutError("Timeout 1"),
                    APITimeoutError("Timeout 2"),
                    MagicMock(data=[])
                ]
            )
            
            # Speed up test by reducing retry delay
            openai_service.retry_delay = 0.01
            
            models = await openai_service.list_models()
            
            assert models == []
            assert mock_client.models.list.call_count == 3
            assert openai_service._request_count == 3
            assert openai_service._error_count == 2
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, openai_service):
        """Test behavior when max retries are exceeded."""
        with patch.object(openai_service, "client") as mock_client:
            # All calls fail
            mock_client.models.list = AsyncMock(
                side_effect=APITimeoutError("Persistent timeout")
            )
            
            openai_service.retry_delay = 0.01
            
            with pytest.raises(OpenAIError) as exc_info:
                await openai_service.list_models()
            
            assert "after 4 attempts" in str(exc_info.value)
            assert mock_client.models.list.call_count == 4  # Initial + 3 retries
    
    @pytest.mark.asyncio
    async def test_create_chat_completion(self, openai_service):
        """Test chat completion creation."""
        mock_completion = MagicMock()
        mock_completion.id = "chat-123"
        
        with patch.object(openai_service, "client") as mock_client:
            mock_client.chat.completions.create = AsyncMock(
                return_value=mock_completion
            )
            
            result = await openai_service.create_chat_completion(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                temperature=0.7
            )
            
            assert result.id == "chat-123"
            mock_client.chat.completions.create.assert_called_once_with(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                stream=False,
                temperature=0.7
            )
    
    @pytest.mark.asyncio
    async def test_create_chat_completion_stream(self, openai_service):
        """Test streaming chat completion."""
        mock_chunks = [
            MagicMock(id="chunk-1"),
            MagicMock(id="chunk-2"),
            MagicMock(id="chunk-3"),
        ]
        
        async def mock_stream():
            for chunk in mock_chunks:
                yield chunk
        
        with patch.object(openai_service, "client") as mock_client:
            mock_client.chat.completions.create = AsyncMock(
                return_value=mock_stream()
            )
            
            chunks = []
            async for chunk in openai_service.create_chat_completion_stream(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}]
            ):
                chunks.append(chunk)
            
            assert len(chunks) == 3
            assert chunks[0].id == "chunk-1"
    
    @pytest.mark.asyncio
    async def test_create_embedding(self, openai_service):
        """Test embedding creation."""
        mock_embedding = MagicMock()
        mock_embedding.data = [{"embedding": [0.1, 0.2, 0.3]}]
        
        with patch.object(openai_service, "client") as mock_client:
            mock_client.embeddings.create = AsyncMock(
                return_value=mock_embedding
            )
            
            result = await openai_service.create_embedding(
                model="text-embedding-ada-002",
                input="Test text"
            )
            
            assert result.data[0]["embedding"] == [0.1, 0.2, 0.3]
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self, openai_service):
        """Test health check when service is healthy."""
        with patch.object(openai_service, "list_models") as mock_list:
            mock_list.return_value = [MagicMock(), MagicMock()]
            
            health = await openai_service.health_check()
            
            assert health["status"] == "healthy"
            assert health["models_available"] == 2
            assert health["error_rate"] == 0
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, openai_service):
        """Test health check when service is unhealthy."""
        with patch.object(openai_service, "list_models") as mock_list:
            mock_list.side_effect = Exception("API is down")
            
            health = await openai_service.health_check()
            
            assert health["status"] == "unhealthy"
            assert "API is down" in health["error"]
    
    @pytest.mark.asyncio
    async def test_close(self, openai_service):
        """Test service cleanup."""
        mock_client = AsyncMock()
        openai_service._client = mock_client
        
        await openai_service.close()
        
        mock_client.close.assert_called_once()
        assert openai_service._client is None
```

#### Step 3: Update Main Application to Use Service
Update **src/ollama_openai_proxy/main.py** to include service in app state:
```python
# Add to imports
from .services.openai_service import OpenAIService

# Update lifespan function
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    try:
        # Load and validate settings
        settings = get_settings()
        
        # Configure logging with the specified level
        configure_logging(settings.log_level)
        
        # Initialize OpenAI service
        openai_service = OpenAIService(settings)
        
        # Log startup information
        logger.info(
            "Starting Ollama-OpenAI Proxy Service",
            extra={
                "version": __version__,
                "port": settings.proxy_port,
                "log_level": settings.log_level,
                "openai_base_url": settings.openai_api_base_url
            }
        )
        
        # Store in app state
        app.state.settings = settings
        app.state.openai_service = openai_service
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise ConfigurationError(f"Application startup failed: {e}") from e
    finally:
        # Cleanup
        if hasattr(app.state, "openai_service"):
            await app.state.openai_service.close()
        logger.info("Shutting down Ollama-OpenAI Proxy Service")

# Add new endpoint for OpenAI health check
@app.get("/openai/health")
async def openai_health_check() -> JSONResponse:
    """Check OpenAI API connectivity."""
    try:
        service = app.state.openai_service
        health = await service.health_check()
        
        status_code = 200 if health["status"] == "healthy" else 503
        return JSONResponse(
            status_code=status_code,
            content=health
        )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "error": str(e)
            }
        )
```

### Verification Steps

1. **Test service initialization:**
   ```bash
   # From activated venv
   python -c "from ollama_openai_proxy.services.openai_service import OpenAIService; print('Service imported successfully')"
   ```

2. **Run unit tests:**
   ```bash
   pytest tests/unit/test_openai_service.py -v --cov=ollama_openai_proxy.services
   ```

3. **Test with real API (requires valid API key):**
   ```bash
   # Start the service
   python -m ollama_openai_proxy
   
   # In another terminal:
   curl http://localhost:11434/openai/health
   ```

4. **Test retry behavior:**
   ```python
   # Create a test script to simulate failures
   import asyncio
   from ollama_openai_proxy.config import get_settings
   from ollama_openai_proxy.services.openai_service import OpenAIService
   
   async def test_retry():
       settings = get_settings()
       service = OpenAIService(settings)
       try:
           models = await service.list_models()
           print(f"Found {len(models)} models")
       finally:
           await service.close()
   
   asyncio.run(test_retry())
   ```

### Definition of Done Checklist

- [ ] OpenAI service wrapper created with all required methods
- [ ] Connection pooling configured for HTTP client
- [ ] Retry logic implemented with exponential backoff
- [ ] Request/response logging without sensitive data
- [ ] Error handling translates OpenAI errors appropriately
- [ ] Request ID tracking for debugging
- [ ] Unit tests achieve 100% coverage
- [ ] Health check endpoint for OpenAI connectivity
- [ ] Service properly closes resources on shutdown
- [ ] Integration with main application via app state

### Common Issues & Solutions

1. **SSL/Certificate errors:**
   - Ensure system certificates are up to date
   - Can disable SSL verification for testing (not for production)

2. **Timeout errors:**
   - Adjust REQUEST_TIMEOUT in configuration
   - Check network connectivity to OpenAI

3. **Rate limit errors:**
   - Service automatically retries with backoff
   - Consider implementing request queuing in future

### Performance Considerations

- Connection pooling reduces latency
- Retry logic prevents transient failures
- Request logging helps identify slow operations
- Consider caching model list in future stories

### Next Steps

After completing this story:
1. Ensure all tests pass
2. Test with real OpenAI API key
3. Commit changes
4. Create PR for review
5. Move to Story 1.4: Implement /api/tags Endpoint