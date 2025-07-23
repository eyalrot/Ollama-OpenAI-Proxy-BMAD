# Ollama SDK Usage Guide

This guide demonstrates how to use the Ollama Python SDK with the Ollama-OpenAI Proxy.

## Installation

```bash
pip install ollama
```

## Configuration

Point the Ollama client to your proxy instance:

```python
import ollama

# Create client pointing to proxy
client = ollama.Client(host="http://localhost:11434")
```

## Listing Models

The proxy translates OpenAI models to Ollama format:

```python
# List available models
response = client.list()

# Response format
# {
#   "models": [
#     {
#       "name": "gpt-3.5-turbo",
#       "modified_at": "2024-01-20T10:30:00Z",
#       "size": 1500000000,
#       "digest": "sha256:abc123..."
#     },
#     ...
#   ]
# }

# Print available models
for model in response["models"]:
    size_gb = model["size"] / 1e9
    print(f"{model['name']}: {size_gb:.1f} GB")
```

## Model Compatibility

The proxy automatically translates the following OpenAI models:

### Chat Models
- `gpt-3.5-turbo` → Available as `gpt-3.5-turbo`
- `gpt-4` → Available as `gpt-4`
- `gpt-4-turbo` → Available as `gpt-4-turbo`
- `gpt-4o` → Available as `gpt-4o`

### Embedding Models
- `text-embedding-ada-002` → Available as `text-embedding-ada-002`
- `text-embedding-3-small` → Available as `text-embedding-3-small`
- `text-embedding-3-large` → Available as `text-embedding-3-large`

## Environment Variables

For CLI compatibility:

```bash
# Set Ollama host to proxy
export OLLAMA_HOST=http://localhost:11434

# Now Ollama CLI will use the proxy
ollama list
```

## Error Handling

```python
try:
    models = client.list()
except Exception as e:
    print(f"Error listing models: {e}")
```

## Testing SDK Compatibility

Run the SDK compatibility tests:

```bash
# Run all SDK tests
pytest tests/integration/test_ollama_sdk_list.py -v -m sdk

# Run with performance benchmarks
pytest tests/integration/test_performance_benchmarks.py -v -s
```

## Example: Complete Usage

```python
import ollama
import os

# Ensure OpenAI API key is set
os.environ["OPENAI_API_KEY"] = "your-key-here"

# Create client
client = ollama.Client(host="http://localhost:11434")

# List models
try:
    response = client.list()
    print(f"Found {len(response['models'])} models:")
    
    for model in response['models']:
        print(f"- {model['name']}")
        print(f"  Size: {model['size'] / 1e9:.1f} GB")
        print(f"  Modified: {model['modified_at']}")
        print()
        
except Exception as e:
    print(f"Error: {e}")
```

## Performance Considerations

- Model listing typically completes in < 100ms
- The proxy adds minimal overhead (< 10ms)
- Concurrent requests are supported
- Large model lists (1000+) are handled efficiently

## Troubleshooting

### Connection Refused
- Ensure proxy is running: `python -m ollama_openai_proxy`
- Check port 11434 is not blocked
- Verify no other service is using port 11434

### No Models Listed
- Check `OPENAI_API_KEY` is set correctly
- Verify OpenAI API access is working
- Check proxy logs for errors

### Format Issues
- Ensure you're using ollama SDK version >= 0.1.7
- Update SDK: `pip install --upgrade ollama`