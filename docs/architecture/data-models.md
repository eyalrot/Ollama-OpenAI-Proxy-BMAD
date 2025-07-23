# Data Models

## OllamaGenerateRequest

**Purpose:** Represents an Ollama API text generation request

**Key Attributes:**

- model: str - The model identifier to use
- prompt: str - The text prompt to generate from
- stream: bool - Whether to stream the response
- options: Dict[str, Any] - Additional generation parameters

**Relationships:**

- Translated to OpenAI ChatCompletionRequest
- Response mapped to OllamaGenerateResponse

## OllamaGenerateResponse

**Purpose:** Represents an Ollama API generation response

**Key Attributes:**

- model: str - The model that generated the response
- created_at: str - ISO timestamp of generation
- response: str - The generated text
- done: bool - Whether generation is complete

**Relationships:**

- Created from OpenAI ChatCompletionResponse
- Streamed as JSON chunks for streaming requests

## OllamaChatRequest

**Purpose:** Represents an Ollama API chat conversation request

**Key Attributes:**

- model: str - The model identifier to use
- messages: List[Dict[str, str]] - Conversation history
- stream: bool - Whether to stream the response
- options: Dict[str, Any] - Additional chat parameters

**Relationships:**

- Direct mapping to OpenAI ChatCompletionRequest
- Response mapped to OllamaChatResponse

## OllamaEmbeddingRequest

**Purpose:** Represents an Ollama API embedding generation request

**Key Attributes:**

- model: str - The embedding model to use
- prompt: str - The text to embed

**Relationships:**

- Translated to OpenAI EmbeddingRequest
- Response mapped to OllamaEmbeddingResponse
