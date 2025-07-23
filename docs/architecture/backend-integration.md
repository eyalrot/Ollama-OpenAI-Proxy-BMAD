# Backend Integration

## OpenAI-Compatible Backend Services

- **Purpose:** Backend services that the proxy communicates with
- **Communication Method:** OpenAI Python SDK (used as client library only)
- **Base URL(s):** Configurable via OPENAI_API_BASE_URL environment variable
- **Authentication:** Bearer token via API key
- **Rate Limits:** Depends on backend provider

**OpenAI SDK Client Usage:**

- `client.models.list()` - Called when Ollama client requests /api/tags
- `client.chat.completions.create()` - Called for /api/generate and /api/chat
- `client.embeddings.create()` - Called for /api/embeddings

**Important Architecture Note:** 
The OpenAI SDK is used purely as a client library to communicate with OpenAI-compatible backends. This service implements the Ollama API specification, NOT the OpenAI API. The translation happens between Ollama API format (what we expose) and OpenAI SDK method calls (how we communicate with backends).
