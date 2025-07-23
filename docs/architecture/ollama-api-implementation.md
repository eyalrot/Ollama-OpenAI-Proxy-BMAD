# Ollama API Implementation

This service implements the Ollama API specification to maintain compatibility with Ollama clients. The OpenAI SDK is used solely as a client library to communicate with OpenAI-compatible backends.

## Ollama API Endpoints

### GET /api/tags
```json
// Ollama Request
GET /api/tags

// Ollama Response
{
  "models": [
    {
      "name": "llama2:latest",
      "modified_at": "2023-08-04T19:56:02.647Z",
      "size": 3826793677
    }
  ]
}
```

### POST /api/generate
```json
// Ollama Request
{
  "model": "llama2",
  "prompt": "Why is the sky blue?",
  "stream": false,
  "options": {
    "temperature": 0.7
  }
}

// Ollama Response (non-streaming)
{
  "model": "llama2",
  "created_at": "2023-08-04T19:56:02.647Z",
  "response": "The sky is blue because...",
  "done": true,
  "total_duration": 5589157167,
  "load_duration": 3013701500
}

// Ollama Response (streaming)
{"model":"llama2","created_at":"2023-08-04T19:56:02.647Z","response":"The","done":false}
{"model":"llama2","created_at":"2023-08-04T19:56:02.647Z","response":" sky","done":false}
{"model":"llama2","created_at":"2023-08-04T19:56:02.647Z","response":"","done":true}
```

### POST /api/chat
```json
// Ollama Request
{
  "model": "llama2",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "stream": false
}

// Ollama Response
{
  "model": "llama2",
  "created_at": "2023-08-04T19:56:02.647Z",
  "message": {
    "role": "assistant",
    "content": "Hello! How can I help you today?"
  },
  "done": true
}
```

### POST /api/embeddings or /api/embed
```json
// Ollama Request
{
  "model": "llama2",
  "prompt": "Here is some text to embed"
}

// Ollama Response
{
  "embedding": [0.1, 0.2, 0.3, ...]
}
```
