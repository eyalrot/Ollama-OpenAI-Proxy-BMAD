# Architecture Document: Ollama-OpenAI Proxy Service

## Overview

The Ollama-OpenAI Proxy Service is a lightweight translation layer that enables Ollama clients to seamlessly communicate with OpenAI-compatible API backends. This document describes the system architecture, design decisions, and implementation details.

## System Architecture

### High-Level Design

```text
┌─────────────────────┐
│   Ollama Client     │
│  (SDK/Application)  │
└──────────┬──────────┘
           │ HTTP/HTTPS
           │ Ollama API Format
           ▼
┌─────────────────────┐
│   Proxy Service     │
│                     │
│  ┌───────────────┐  │
│  │   FastAPI     │  │
│  ├───────────────┤  │
│  │  Translators  │  │
│  ├───────────────┤  │
│  │  HTTP Client  │  │
│  └───────────────┘  │
└──────────┬──────────┘
           │ HTTP/HTTPS
           │ OpenAI API Format
           ▼
┌─────────────────────┐
│  OpenAI-Compatible  │
│    API Backend      │
└─────────────────────┘
```

### Component Architecture

```text
┌─────────────────────────────────────────────────────┐
│                  Proxy Service                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │   Routers   │  │ Translators │  │   Models   │ │
│  │             │  │             │  │            │ │
│  │ • /api/tags │  │ • Tags      │  │ • Ollama   │ │
│  │ • /api/     │  │ • Generate  │  │   Request  │ │
│  │   generate  │  │ • Chat      │  │ • Ollama   │ │
│  │ • /api/chat │  │ • Embeddings│  │   Response │ │
│  │ • /api/     │  │             │  │ • OpenAI   │ │
│  │   embeddings│  │             │  │   Request  │ │
│  └──────┬──────┘  └──────┬──────┘  │ • OpenAI   │ │
│         │                │         │   Response │ │
│         ▼                ▼         └────────────┘ │
│  ┌──────────────────────────────────────────────┐ │
│  │            Core Translation Engine           │ │
│  │                                              │ │
│  │  • Request format conversion                 │ │
│  │  • Response format conversion                │ │
│  │  • Error mapping                             │ │
│  │  • Streaming transformation                  │ │
│  └─────────────────┬────────────────────────────┘ │
│                    │                               │
│                    ▼                               │
│  ┌──────────────────────────────────────────────┐ │
│  │              OpenAI SDK Client              │ │
│  │                                              │ │
│  │  • OpenAI Python SDK                         │ │
│  │  • Built-in retry & error handling           │ │
│  │  • Native streaming support                  │ │
│  │  • Compatible with all OpenAI-like APIs      │ │
│  └──────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

## Design Principles

### 1. Simplicity (KISS)
- Minimal dependencies
- Straightforward request/response translation
- No complex state management
- Clear separation of concerns

### 2. Stateless Design
- No session management
- No request history storage
- Each request is independent
- Scalable horizontally

### 3. Format Translation Focus
- Primary responsibility: Ollama ↔ OpenAI format conversion
- No business logic beyond translation
- Transparent proxy behavior

## Core Components

### 1. FastAPI Application

The main application entry point that sets up routes and middleware.

```python
# main.py structure
app = FastAPI(title="Ollama-OpenAI Proxy")

# Include routers
app.include_router(tags_router)
app.include_router(generate_router)
app.include_router(chat_router)
app.include_router(embeddings_router)
```

### 2. Request/Response Models

Pydantic models that define the exact structure of Ollama and OpenAI formats.

```python
# Ollama Models
class OllamaGenerateRequest(BaseModel):
    model: str
    prompt: str
    stream: bool = False
    options: Dict[str, Any] = {}

class OllamaGenerateResponse(BaseModel):
    model: str
    created_at: str
    response: str
    done: bool

# OpenAI Models
class OpenAICompletionRequest(BaseModel):
    model: str
    messages: List[Dict[str, str]]
    stream: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
```

### 3. Translation Layer

The core logic that converts between API formats.

```python
# Translation flow with OpenAI SDK
Ollama Request → Translator → OpenAI SDK Call
                                    ↓
                              OpenAI API
                                    ↓
OpenAI Response Object → Translator → Ollama Response
```

#### Translation Examples

**Generate Endpoint Translation**:
```python
# Ollama format input
ollama_request = {
    "model": "llama2",
    "prompt": "Hello, world!",
    "stream": false
}

# Translator converts to OpenAI SDK call
response = await client.chat.completions.create(
    model="gpt-3.5-turbo",  # Mapped model name
    messages=[{"role": "user", "content": "Hello, world!"}],
    stream=False
)

# SDK returns typed response object
# response.choices[0].message.content = "Hello! How can I help you?"

# Translate to Ollama format
ollama_response = {
    "model": "llama2",
    "created_at": datetime.now().isoformat(),
    "response": response.choices[0].message.content,
    "done": True
}
```

**Embeddings Translation**:
```python
# Ollama embeddings request
ollama_request = {
    "model": "llama2",
    "prompt": "Hello, world!"
}

# OpenAI SDK call
response = await client.embeddings.create(
    model="text-embedding-ada-002",
    input="Hello, world!"
)

# Translate response
ollama_response = {
    "embedding": response.data[0].embedding
}
```

### 4. OpenAI SDK Client

Uses the official OpenAI Python SDK for communication with OpenAI-compatible backends.

```python
from openai import AsyncOpenAI

class OpenAIClient:
    def __init__(self, base_url: str, api_key: str):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url  # Works with any OpenAI-compatible API
        )
    
    async def create_completion(self, **kwargs):
        # Direct SDK call with built-in retry, timeout, and error handling
        return await self.client.chat.completions.create(**kwargs)
    
    async def list_models(self):
        return await self.client.models.list()
    
    async def create_embeddings(self, **kwargs):
        return await self.client.embeddings.create(**kwargs)
```

**Benefits of using OpenAI SDK**:
- Built-in retry logic with exponential backoff
- Automatic error handling and typed exceptions
- Native streaming support
- Type safety with Pydantic models
- Maintained compatibility with API changes
- Works with all OpenAI-compatible providers (Groq, Together, etc.)

## API Endpoints

### Phase 1 Endpoints

#### GET /api/tags
- **Purpose**: List available models
- **Ollama SDK**: `client.list()`
- **Translation**: `/api/tags` → `/v1/models`

```text
Request Flow:
Ollama Client → GET /api/tags → Proxy → GET /v1/models → OpenAI
                                  ↓
                            Transform Response
                                  ↓
Ollama Client ← Ollama Format ← Proxy ← Model List ← OpenAI
```

#### POST /api/generate
- **Purpose**: Generate text completion
- **Ollama SDK**: `client.generate()`
- **Translation**: `/api/generate` → `/v1/chat/completions`

### Phase 2 Endpoints

#### POST /api/chat
- **Purpose**: Chat conversation
- **Ollama SDK**: `client.chat()`
- **Translation**: Direct format mapping to `/v1/chat/completions`

#### POST /api/embeddings, /api/embed
- **Purpose**: Generate text embeddings
- **Ollama SDK**: `client.embeddings()`
- **Translation**: `/api/embeddings` → `/v1/embeddings`

## Streaming Architecture

### Server-Sent Events (SSE)

Streaming responses use SSE format for real-time token delivery.

```text
Streaming Flow:
┌────────────┐  SSE   ┌─────────┐  SSE   ┌────────────┐
│   Ollama   │ ◄───── │  Proxy  │ ◄───── │   OpenAI   │
│   Client   │        │         │        │   Backend  │
└────────────┘        └─────────┘        └────────────┘

Stream Translation:
OpenAI: data: {"choices":[{"delta":{"content":"Hello"}}]}
   ↓
Ollama: {"model":"llama2","response":"Hello","done":false}
```

### Implementation Approach

```python
from openai import AsyncOpenAI

async def stream_generate(request: OllamaGenerateRequest):
    # Convert to OpenAI SDK parameters
    openai_params = {
        "model": request.model,
        "messages": [{"role": "user", "content": request.prompt}],
        "stream": True
    }
    
    # Stream using OpenAI SDK
    stream = await openai_client.chat.completions.create(**openai_params)
    
    async for chunk in stream:
        # Translate each chunk
        if chunk.choices[0].delta.content:
            ollama_chunk = {
                "model": request.model,
                "response": chunk.choices[0].delta.content,
                "done": False
            }
            yield f"data: {json.dumps(ollama_chunk)}\n\n"
    
    # Send final chunk
    final_chunk = {"model": request.model, "response": "", "done": True}
    yield f"data: {json.dumps(final_chunk)}\n\n"
```

## Error Handling

### Error Translation with SDK

```python
from openai import APIError, APIConnectionError, RateLimitError, AuthenticationError

async def handle_openai_errors(func):
    """Decorator to translate OpenAI SDK exceptions to Ollama format"""
    try:
        return await func()
    except AuthenticationError:
        raise HTTPException(
            status_code=401,
            detail={"error": "Invalid API key"}
        )
    except RateLimitError:
        raise HTTPException(
            status_code=429,
            detail={"error": "Rate limit exceeded"}
        )
    except APIConnectionError:
        raise HTTPException(
            status_code=503,
            detail={"error": "Connection to OpenAI failed"}
        )
    except APIError as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail={"error": str(e)}
        )
```

### Error Response Format

```json
{
    "error": {
        "message": "Model not found",
        "type": "not_found",
        "code": "model_not_found"
    }
}
```

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-...

# Optional with defaults
PROXY_PORT=11434              # Ollama default port
LOG_LEVEL=INFO               
REQUEST_TIMEOUT=60           
MAX_RETRIES=3                
MODEL_MAPPING_FILE=None      # Disabled by default - pass model names through
```

### Model Mapping

Model name mapping is **disabled by default** - the proxy passes model names through unchanged. This follows the KISS principle and assumes the OpenAI-compatible backend accepts the model names as provided.

Optional JSON configuration for model name translation (only if needed):

```json
{
    "llama2": "gpt-3.5-turbo",
    "llama2:13b": "gpt-3.5-turbo-16k",
    "codellama": "gpt-4",
    "mistral": "gpt-3.5-turbo"
}
```

**Default behavior**: No mapping - `request.model` is passed directly to the OpenAI API.

## Deployment Architecture

### Container Structure

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "11434"]
```

### Deployment Options

1. **Standalone Docker**:
   ```bash
   docker run -p 11434:11434 \
     -e OPENAI_API_KEY=sk-... \
     ollama-openai-proxy
   ```

2. **Docker Compose**:
   ```yaml
   services:
     proxy:
       image: ollama-openai-proxy
       ports:
         - "11434:11434"
       environment:
         - OPENAI_API_KEY=${OPENAI_API_KEY}
   ```

3. **Kubernetes** (Phase 3):
   - Deployment with configurable replicas
   - Service for load balancing
   - ConfigMap for configuration

## Performance Considerations

### Connection Management

The OpenAI SDK handles connection management internally:

```python
# SDK handles connection pooling automatically
client = AsyncOpenAI(
    api_key=api_key,
    base_url=base_url,
    timeout=60.0,  # Request timeout
    max_retries=3,  # Automatic retry with exponential backoff
)

# No manual connection pooling needed - SDK manages:
# - Connection reuse
# - Keep-alive connections  
# - Automatic reconnection
# - Request queuing
```

### Timeout Strategy

- Default request timeout: 60 seconds
- Streaming timeout: 300 seconds
- Configurable per-endpoint

### Memory Management

- Stream processing to avoid loading full responses
- Minimal in-memory state
- Garbage collection friendly design

## Security Considerations

### API Key Handling

- Never log API keys
- Pass through Authorization headers
- Environment variable configuration only

### Input Validation

- Pydantic models for all inputs
- Request size limits
- Parameter validation

### HTTPS Support

- TLS termination at proxy level
- Certificate verification for backend calls
- Secure defaults

## Testing Architecture

### Unit Test Structure

```python
tests/
├── unit/
│   ├── test_translators.py    # Format conversion
│   ├── test_models.py         # Model validation
│   └── test_routers.py        # Endpoint logic
```

### Integration Test Structure

```python
tests/
├── integration/
│   ├── test_ollama_sdk.py     # SDK compatibility
│   ├── test_streaming.py      # Streaming behavior
│   └── test_error_handling.py # Error scenarios
```

### Test Strategy

1. **Unit Tests**: Mock OpenAI responses
2. **Integration Tests**: Real OpenAI API calls
3. **SDK Tests**: Official Ollama SDK validation

## Future Considerations

### Scalability Path

1. **Horizontal Scaling**: Stateless design enables multiple instances
2. **Load Balancing**: Standard HTTP load balancers work
3. **Caching**: Optional response caching for repeated requests

### Extensibility Points

1. **New Endpoints**: Add routers for new Ollama endpoints
2. **Model Features**: Extend translators for new capabilities
3. **Backend Support**: Adapt client for different OpenAI-compatible APIs

### Monitoring Hooks (Phase 3)

- Request/response logging
- Performance metrics collection
- Error rate tracking
- Health check endpoints

## Simplified Implementation Example

Here's how the translator looks with the OpenAI SDK:

```python
# translator.py
from openai import AsyncOpenAI
from datetime import datetime

class OllamaToOpenAITranslator:
    def __init__(self, api_key: str, base_url: str, model_mapping: dict = None):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            max_retries=3
        )
        # Model mapping is optional and disabled by default
        self.model_mapping = model_mapping or {}
    
    def map_model(self, ollama_model: str) -> str:
        """Map Ollama model names to OpenAI model names (if mapping configured)"""
        # Default: pass through model name unchanged
        return self.model_mapping.get(ollama_model, ollama_model)
    
    async def list_models(self):
        """Translate /api/tags to OpenAI models list"""
        models = await self.client.models.list()
        
        # Convert to Ollama format
        return {
            "models": [
                {
                    "name": model.id,
                    "modified_at": datetime.now().isoformat(),
                    "size": 0,  # OpenAI doesn't provide size
                }
                for model in models.data
            ]
        }
    
    async def generate(self, request: OllamaGenerateRequest):
        """Translate /api/generate to OpenAI completion"""
        response = await self.client.chat.completions.create(
            model=self.map_model(request.model),
            messages=[{"role": "user", "content": request.prompt}],
            temperature=request.options.get("temperature", 1.0),
            max_tokens=request.options.get("num_predict"),
            stream=request.stream
        )
        
        if request.stream:
            return self._stream_response(response, request.model)
        else:
            return {
                "model": request.model,
                "created_at": datetime.now().isoformat(),
                "response": response.choices[0].message.content,
                "done": True
            }
    
    async def _stream_response(self, stream, model: str):
        """Convert OpenAI stream to Ollama stream format"""
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield {
                    "model": model,
                    "response": chunk.choices[0].delta.content,
                    "done": False
                }
        
        yield {
            "model": model,
            "response": "",
            "done": True
        }
```

This simplified approach leverages all the built-in features of the OpenAI SDK while maintaining clean translation logic.