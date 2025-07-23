# Ollama API Analysis and Key Findings

Based on the official Ollama API specification extracted from the Postman collection, here are the critical findings for implementing a compatible proxy:

## Critical API Structure for `/api/tags`

The **exact** response format for `/api/tags` is:

```json
{
  "models": [
    {
      "name": "llama3.1:latest",
      "model": "llama3.1:latest",    // DUPLICATE of name field!
      "modified_at": "2025-01-21T16:53:57.496699591-08:00",
      "size": 4920753328,
      "digest": "46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e",
      "details": {
        "parent_model": "",
        "format": "gguf",
        "family": "llama",
        "families": ["llama"],
        "parameter_size": "8.0B",
        "quantization_level": "Q4_K_M"
      }
    }
  ]
}
```

### Key Observations:

1. **Both `name` AND `model` fields are required** - They contain the same value
2. **Timestamp format** - Uses RFC3339 with timezone offset (not just 'Z')
3. **Size is integer** - In bytes, not floating point
4. **Details object** - Optional but includes model metadata when present

## SDK vs API Discrepancy

The Ollama Python SDK internally transforms the response:
- API returns: `{"name": "modelname", "model": "modelname", ...}`
- SDK exposes: `model.model` (often None), other fields mapped differently

This is why your Epic 1 tests failed - the SDK does its own transformation.

## Complete Endpoint List

From the Postman collection, Ollama exposes these endpoints:

### Model Management
- `GET /api/tags` - List downloaded models
- `POST /api/show` - Show model details
- `POST /api/create` - Create model from Modelfile
- `POST /api/copy` - Copy a model
- `DELETE /api/delete` - Delete a model
- `POST /api/pull` - Download model from library
- `POST /api/push` - Upload model to library
- `GET /api/ps` - List running models

### Generation
- `POST /api/generate` - Single-turn text generation
- `POST /api/chat` - Multi-turn chat conversations
- `POST /api/embed` - Generate embeddings

### System
- `GET /api/version` - Get Ollama version

## Important Implementation Notes

### 1. Streaming Responses
Most endpoints support both streaming and non-streaming modes:
- Default: `"stream": true` (newline-delimited JSON)
- Non-streaming: `"stream": false` (single JSON response)

### 2. Model Options
Runtime options can be passed in requests:
```json
{
  "options": {
    "temperature": 0.7,
    "top_p": 0.9,
    "seed": 42,
    "num_ctx": 4096
  }
}
```

### 3. Keep Alive
Models can be kept in memory or unloaded:
- `"keep_alive": "5m"` - Keep loaded for 5 minutes
- `"keep_alive": "0"` - Unload immediately

### 4. Special Features
- **Raw mode**: `"raw": true` - Bypass templating
- **JSON format**: `"format": "json"` - Force JSON output
- **Structured output**: Provide JSON schema in format field
- **Images**: Base64-encoded in `images` array
- **Tools/Functions**: Supported in chat endpoint

## Validation Strategy

To prevent future API compliance issues:

1. **Use the OpenAPI spec** at `api-specs/ollama-openapi.yaml`
2. **Validate responses** with `tools/validate_against_openapi.py`
3. **Test with real Ollama** to ensure compatibility
4. **Monitor SDK changes** as it may transform responses

## Example Usage

```bash
# Validate your proxy implementation
python tools/validate_against_openapi.py api-specs/ollama-openapi.yaml http://localhost:11434

# Compare with real Ollama
python tools/validate_against_openapi.py api-specs/ollama-openapi.yaml http://localhost:11434
```