# Ollama API Analysis: Chat Completion, Embeddings & Generate

## Generate Endpoint (`/api/generate`)

The generate endpoint provides single-turn text generation with extensive configuration options. This is the primary completion endpoint in Ollama.

### Request Format

```json
POST /api/generate
{
  "model": "llama3.1:latest",
  "prompt": "Why is the sky blue?",
  "stream": true,  // Default: true (streaming response)
  "raw": false,    // Default: false (use model's prompt template)
  "format": "json", // Optional: Forces JSON output
  "system": "You are a helpful assistant", // Optional: System prompt
  "template": "{{ .System }}\n\n{{ .Prompt }}", // Optional: Custom template
  "context": [128006, 882, 128007, ...], // Optional: Context from previous response
  "options": {
    "temperature": 0.8,
    "top_p": 0.9,
    "top_k": 40,
    "seed": 42,
    "num_predict": 128,
    "num_ctx": 2048,
    "stop": ["User:", "Assistant:"]
  },
  "keep_alive": "5m"
}
```

### Response Format (Non-Streaming)

When `"stream": false`:

```json
{
  "model": "llama3.1:latest",
  "created_at": "2025-01-23T10:30:00.123456Z",
  "response": "The sky appears blue because of a phenomenon called Rayleigh scattering...",
  "done": true,
  "done_reason": "stop",  // "stop", "length", or "load"
  "context": [128006, 882, 128007, ...], // Token IDs for conversation context
  "total_duration": 5835463784,
  "load_duration": 534986708,
  "prompt_eval_count": 26,
  "prompt_eval_duration": 342546000,
  "eval_count": 298,
  "eval_duration": 4956026000
}
```

### Response Format (Streaming)

When `"stream": true` (default), responses are newline-delimited JSON:

```json
{"model":"llama3.1:latest","created_at":"2025-01-23T10:30:00.123456Z","response":"The","done":false}
{"model":"llama3.1:latest","created_at":"2025-01-23T10:30:00.234567Z","response":" sky","done":false}
{"model":"llama3.1:latest","created_at":"2025-01-23T10:30:00.345678Z","response":" appears","done":false}
...
{"model":"llama3.1:latest","created_at":"2025-01-23T10:30:01.123456Z","response":"","done":true,"done_reason":"stop","context":[...],"total_duration":5835463784,"load_duration":534986708,"prompt_eval_count":26,"prompt_eval_duration":342546000,"eval_count":298,"eval_duration":4956026000}
```

### Key Features

1. **Raw Mode**: When `"raw": true`, bypasses the model's prompt template
   - Useful for debugging or custom formatting
   - No context returned in raw mode
   - Direct control over prompt structure

2. **Context Preservation**: The `context` field allows continuing conversations
   - Pass the context from previous response to maintain state
   - Essential for multi-turn interactions without using `/api/chat`

3. **JSON Mode**: When `"format": "json"`, ensures valid JSON output
   - Model will structure response as JSON
   - Important to instruct model in prompt to respond with JSON

4. **System Prompts**: Can be included directly in the request
   - Alternative to embedding in the prompt
   - Cleaner separation of system instructions

## Chat Completion Endpoint (`/api/chat`)

The chat endpoint supports multi-turn conversations with extensive features including streaming, structured outputs, tool calling, and multimodal inputs.

### Request Format

```json
POST /api/chat
{
  "model": "llama3.1:latest",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "Hello, how are you?",
      "images": ["base64_encoded_image_data"]  // Optional: for multimodal models
    },
    {
      "role": "assistant",
      "content": "I'm doing well, thank you! How can I help you today?"
    },
    {
      "role": "user",
      "content": "What's the weather like?"
    }
  ],
  "stream": true,  // Default: true (streaming response)
  "format": "json",  // Optional: Forces JSON output or structured format
  "options": {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "seed": 42,
    "num_predict": 100,
    "num_ctx": 4096,
    "stop": ["Human:", "Assistant:"]
  },
  "tools": [  // Optional: for function calling
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get the current weather for a location",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {
              "type": "string",
              "description": "The city and state"
            }
          },
          "required": ["location"]
        }
      }
    }
  ],
  "keep_alive": "5m"  // How long to keep model in memory
}
```

### Response Format (Non-Streaming)

When `"stream": false`:

```json
{
  "model": "llama3.1:latest",
  "created_at": "2025-01-23T10:30:00.123456Z",
  "message": {
    "role": "assistant",
    "content": "Based on my last update, I don't have access to real-time weather data...",
    "tool_calls": [  // Only if tools were provided
      {
        "id": "call_123",
        "type": "function",
        "function": {
          "name": "get_weather",
          "arguments": "{\"location\": \"San Francisco, CA\"}"
        }
      }
    ]
  },
  "done": true,
  "done_reason": "stop",  // "stop", "length", or "load"
  "total_duration": 1234567890,
  "load_duration": 123456789,
  "prompt_eval_count": 45,
  "prompt_eval_duration": 234567890,
  "eval_count": 120,
  "eval_duration": 890123456
}
```

### Response Format (Streaming)

When `"stream": true` (default), responses are newline-delimited JSON:

```json
{"model":"llama3.1:latest","created_at":"2025-01-23T10:30:00.123456Z","message":{"role":"assistant","content":"Based"},"done":false}
{"model":"llama3.1:latest","created_at":"2025-01-23T10:30:00.234567Z","message":{"role":"assistant","content":" on"},"done":false}
{"model":"llama3.1:latest","created_at":"2025-01-23T10:30:00.345678Z","message":{"role":"assistant","content":" my"},"done":false}
...
{"model":"llama3.1:latest","created_at":"2025-01-23T10:30:01.123456Z","message":{"role":"assistant","content":""},"done":true,"done_reason":"stop","total_duration":1234567890,"load_duration":123456789,"prompt_eval_count":45,"prompt_eval_duration":234567890,"eval_count":120,"eval_duration":890123456}
```

### Message Roles

- **`system`**: System instructions (typically first message)
- **`user`**: User input
- **`assistant`**: Model responses
- **`tool`**: Tool/function responses (when using function calling)

### Structured Output Format

When providing a JSON schema in the `format` field:

```json
{
  "model": "llama3.1:latest",
  "messages": [
    {
      "role": "user",
      "content": "Extract the name and age from: John is 25 years old."
    }
  ],
  "format": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "age": {"type": "integer"}
    },
    "required": ["name", "age"]
  },
  "stream": false
}
```

Response will be constrained to match the schema:

```json
{
  "model": "llama3.1:latest",
  "created_at": "2025-01-23T10:30:00.123456Z",
  "message": {
    "role": "assistant",
    "content": "{\"name\": \"John\", \"age\": 25}"
  },
  "done": true,
  "done_reason": "stop",
  ...
}
```

### Multimodal Chat (Images)

For models like `llava` or `bakllava`:

```json
{
  "model": "llava:latest",
  "messages": [
    {
      "role": "user",
      "content": "What's in this image?",
      "images": ["iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="]
    }
  ]
}
```

## Embeddings Endpoint (`/api/embed`)

The embeddings endpoint generates vector representations of text for semantic search, similarity, and other applications.

### Request Format

```json
POST /api/embed
{
  "model": "llama3.1:latest",  // Must be an embedding-capable model
  "input": "The quick brown fox jumps over the lazy dog"
}
```

### Response Format

```json
{
  "embeddings": [
    [
      -0.0234375,
      0.0126953125,
      -0.0078125,
      0.0205078125,
      // ... many more float values (dimension depends on model)
      0.0146484375,
      -0.0185546875
    ]
  ]
}
```

### Important Notes for Embeddings

1. **Model Requirements**: Not all models support embeddings. Common embedding models:
   - Models with embedding capabilities built-in
   - Some general models can also generate embeddings

2. **Input Format**: Currently only supports single text input (not array)

3. **Output Dimensions**: Vary by model:
   - Typical dimensions: 384, 768, 1024, 1536, etc.

4. **Performance**: Embedding generation is typically faster than text generation

## Model Options Reference

Both chat and generate endpoints support these options:

```json
{
  "options": {
    // Temperature (0.0-2.0): Controls randomness
    "temperature": 0.8,
    
    // Top-p (0.0-1.0): Nucleus sampling threshold
    "top_p": 0.9,
    
    // Top-k (1+): Number of top tokens to consider
    "top_k": 40,
    
    // Seed: For reproducible outputs
    "seed": 42,
    
    // Maximum tokens to generate
    "num_predict": 128,
    
    // Context window size
    "num_ctx": 4096,
    
    // Stop sequences
    "stop": ["\\n", "User:", "Human:"],
    
    // Repeat penalty (1.0 = no penalty)
    "repeat_penalty": 1.1,
    
    // Frequency penalty
    "frequency_penalty": 0.0,
    
    // Presence penalty
    "presence_penalty": 0.0,
    
    // Mirostat sampling
    "mirostat": 0,  // 0 (disabled), 1, or 2
    "mirostat_tau": 5.0,
    "mirostat_eta": 0.1,
    
    // Token generation settings
    "tfs_z": 1.0,
    "typical_p": 1.0
  }
}
```

## Keep Alive Parameter

Controls how long models stay loaded in memory:

```json
{
  "keep_alive": "5m"     // Keep for 5 minutes (default)
  "keep_alive": "1h"     // Keep for 1 hour
  "keep_alive": "24h"    // Keep for 24 hours
  "keep_alive": "0"      // Unload immediately after request
  "keep_alive": "-1"     // Keep loaded indefinitely
}
```

## Error Responses

All endpoints return consistent error format:

```json
{
  "error": "model 'nonexistent:latest' not found"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad request (invalid parameters)
- `404`: Model not found
- `500`: Internal server error

## Performance Metrics

All generation responses include performance metrics:

- **`total_duration`**: Total time in nanoseconds
- **`load_duration`**: Model loading time
- **`prompt_eval_count`**: Number of tokens in prompt
- **`prompt_eval_duration`**: Time to process prompt
- **`eval_count`**: Number of tokens generated
- **`eval_duration`**: Time to generate response

Calculate tokens per second:
```
prompt_tps = prompt_eval_count / (prompt_eval_duration / 1e9)
generation_tps = eval_count / (eval_duration / 1e9)
```

## SDK vs API Differences

### Chat Response in SDK

The Ollama Python SDK may transform the response:

```python
# What the API returns
api_response = {
    "model": "llama3.1:latest",
    "message": {"role": "assistant", "content": "Hello!"},
    "done": true
}

# What the SDK exposes
sdk_response = client.chat(...)
# sdk_response.message.content = "Hello!"
# sdk_response.message.role = "assistant"
```

### Streaming in SDK

```python
# SDK handles streaming internally
for chunk in client.chat(model="llama3.1", messages=messages, stream=True):
    print(chunk['message']['content'], end='')
```

## OpenAI to Ollama Translation Guide

### Generate/Completion Mapping

| OpenAI | Ollama | Notes |
|--------|--------|-------|
| `model` | `model` | Direct mapping |
| `prompt` | `prompt` | Direct mapping |
| `temperature` | `options.temperature` | Nested in options |
| `max_tokens` | `options.num_predict` | Different name |
| `top_p` | `options.top_p` | Nested in options |
| `frequency_penalty` | `options.frequency_penalty` | Nested in options |
| `presence_penalty` | `options.presence_penalty` | Nested in options |
| `stop` | `options.stop` | Nested in options |
| `stream` | `stream` | Direct mapping |
| `suffix` | N/A | Not supported in Ollama |
| `echo` | N/A | Not supported (use raw mode instead) |
| `logprobs` | N/A | Not supported |

### Chat Completion Mapping

| OpenAI | Ollama | Notes |
|--------|--------|-------|
| `model` | `model` | Direct mapping |
| `messages` | `messages` | Same format |
| `temperature` | `options.temperature` | Nested in options |
| `max_tokens` | `options.num_predict` | Different name |
| `top_p` | `options.top_p` | Nested in options |
| `frequency_penalty` | `options.frequency_penalty` | Nested in options |
| `presence_penalty` | `options.presence_penalty` | Nested in options |
| `stop` | `options.stop` | Nested in options |
| `stream` | `stream` | Direct mapping |
| `functions` | `tools` | Different format |
| `response_format` | `format` | Different structure |

### Embeddings Mapping

| OpenAI | Ollama | Notes |
|--------|--------|-------|
| `model` | `model` | Direct mapping |
| `input` (array) | `input` (string) | Ollama only supports single input |
| `encoding_format` | N/A | Not supported |
| Response: `data[0].embedding` | Response: `embeddings[0]` | Different structure |

## Key Differences: Generate vs Chat

1. **Single vs Multi-turn**:
   - `/api/generate`: Single-turn completion, uses `prompt` field
   - `/api/chat`: Multi-turn conversation, uses `messages` array

2. **Context Handling**:
   - `/api/generate`: Manual context management via `context` field
   - `/api/chat`: Automatic context management through message history

3. **System Prompts**:
   - `/api/generate`: Via `system` field or embedded in prompt
   - `/api/chat`: Via message with `role: "system"`

4. **Use Cases**:
   - `/api/generate`: Simple completions, one-off generations, custom templates
   - `/api/chat`: Conversations, assistant interactions, tool calling

## Testing Recommendations

1. **Test streaming and non-streaming modes** separately
2. **Validate performance metrics** are present and reasonable
3. **Test with multimodal inputs** if supporting vision models
4. **Verify tool calling format** matches exactly
5. **Check structured output** with various JSON schemas
6. **Test edge cases**:
   - Empty messages array
   - Very long conversations
   - Invalid model names
   - Malformed images
   - Invalid tool schemas
