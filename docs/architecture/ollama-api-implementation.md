# Ollama API Implementation

This service implements the Ollama API specification to maintain compatibility with Ollama clients. The OpenAI SDK is used solely as a client library to communicate with OpenAI-compatible backends.

## Critical API Compliance Guidelines

### 1. Always Validate Against Official API Specification
- **Reference**: Use the Ollama OpenAPI specification at `/docs/architecture/ollama-api-analysis.md`
- **Postman Collection**: Refer to `/docs/architecture/Ollama REST API.postman_collection.json`
- **Contract Testing**: Run contract tests before implementing any endpoint

### 2. Known API Quirks and Requirements

#### The `/api/tags` Duplicate Field Issue
**CRITICAL**: The Ollama API requires BOTH `name` and `model` fields with identical values:
```json
{
  "models": [
    {
      "name": "llama2:latest",
      "model": "llama2:latest",  // REQUIRED: Duplicate of name!
      "modified_at": "2023-08-04T19:56:02.647Z",
      "size": 3826793677,
      "digest": "sha256:..."
    }
  ]
}
```

### 3. SDK vs API Response Differences
- The Ollama SDK may transform API responses differently than expected
- Always test with BOTH:
  - Raw API calls (curl/httpie)
  - Ollama SDK/CLI (`ollama list`, etc.)

### 4. Development Process to Prevent Errors

1. **Before Implementation**:
   - Review the OpenAPI spec for the endpoint
   - Check the Postman collection for examples
   - Look for any special field requirements

2. **During Implementation**:
   - Use the corrected models in `/src/ollama_openai_proxy/models/ollama_corrected.py`
   - Implement contract tests first (TDD approach)
   - Validate responses against OpenAPI schema

3. **After Implementation**:
   - Run contract tests: `pytest tests/contract/`
   - Test with Ollama CLI: `ollama list`
   - Test with Ollama SDK
   - Use validation tool: `python tools/validate_against_openapi.py`

### 5. Common Pitfalls to Avoid

- **Missing Duplicate Fields**: Always check if Ollama expects duplicate fields
- **Timestamp Formats**: Use RFC3339 with timezone offset, not just 'Z'
- **Streaming Format**: Newline-delimited JSON, not arrays
- **Context Fields**: Some endpoints return token arrays that must be preserved

## Ollama API Endpoints

### GET /api/tags
```json
// Ollama Request
GET /api/tags

// Ollama Response (CORRECT - includes both name and model)
{
  "models": [
    {
      "name": "llama2:latest",
      "model": "llama2:latest",  // REQUIRED: Must duplicate name field!
      "modified_at": "2023-08-04T19:56:02.647Z",
      "size": 3826793677,
      "digest": "sha256:46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e",
      "details": {  // Optional
        "parent_model": "",
        "format": "gguf",
        "family": "llama",
        "families": ["llama"],
        "parameter_size": "7B",
        "quantization_level": "Q4_K_M"
      }
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
