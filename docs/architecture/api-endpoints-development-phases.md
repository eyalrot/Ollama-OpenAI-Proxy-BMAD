# API Endpoints & Development Phases

## Development Phase 1: Foundation

### GET /api/tags

- **Purpose**: List available models (Ollama API endpoint)
- **Ollama SDK Method**: `client.list()`
- **Implementation**: Use OpenAI SDK's `client.models.list()` to fetch models
- **Priority**: MUST be implemented first to establish basic connectivity
- **Testing**: Verify Ollama SDK can list models through proxy

```text
Request Flow:
Ollama Client → GET /api/tags → Proxy → GET /v1/models → OpenAI
                                  ↓
                            Transform Response
                                  ↓
Ollama Client ← Ollama Format ← Proxy ← Model List ← OpenAI
```

## Development Phase 2: Core Generation

### POST /api/generate

- **Purpose**: Generate text completion (Ollama API endpoint)
- **Ollama SDK Method**: `client.generate()`
- **Implementation**: Use OpenAI SDK's `client.chat.completions.create()`
- **Priority**: Second implementation priority
- **Key Features**: Must support both streaming and non-streaming modes
- **Testing**: Verify both streaming and non-streaming generation

## Development Phase 3: Advanced Features

### POST /api/chat

- **Purpose**: Chat conversation with message history (Ollama API endpoint)
- **Ollama SDK Method**: `client.chat()`
- **Implementation**: Use OpenAI SDK's `client.chat.completions.create()` with messages
- **Note**: Similar to generate but with conversation context
- **Testing**: Multi-turn conversations through SDK

### POST /api/embeddings, /api/embed

- **Purpose**: Generate text embeddings (Ollama API endpoints)
- **Ollama SDK Method**: `client.embeddings()`
- **Implementation**: Use OpenAI SDK's `client.embeddings.create()`
- **Note**: Two endpoint aliases for same functionality
- **Testing**: Verify embedding generation and format
