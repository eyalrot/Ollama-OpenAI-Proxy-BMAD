# Ollama-OpenAI Proxy

OpenAI-compatible proxy service for Ollama API, enabling Ollama applications to use OpenAI backends.

## Features

- ✅ **Ollama SDK Compatible** - Works with the official Ollama Python SDK
- ✅ **Model Translation** - Automatically translates OpenAI models to Ollama format
- ✅ **High Performance** - < 100ms response time with minimal overhead
- ✅ **Production Ready** - Comprehensive test coverage (87%+)

## Quick Start

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ollama-openai-proxy
   ```

2. **Set up virtual environment (required for local development):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Set up pre-commit hooks:**
   ```bash
   pre-commit install
   ```

5. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

6. **Run the service:**
   ```bash
   python -m ollama_openai_proxy
   ```

7. **Verify health:**
   ```bash
   curl http://localhost:11434/health
   ```

### Docker Development

```bash
cd docker
docker-compose up --build
```

## Development Workflow

Always work within the activated virtual environment:
```bash
source venv/bin/activate  # Activate before working
deactivate              # Deactivate when done
```

## Testing

```bash
# Run all tests (from venv)
pytest

# Run with coverage
pytest --cov=src
```

## Ollama SDK Usage

The proxy is fully compatible with the Ollama Python SDK:

```python
import ollama

# Point to proxy instead of Ollama
client = ollama.Client(host="http://localhost:11434")

# List available models
models = client.list()
for model in models["models"]:
    print(f"- {model['name']} ({model['size'] / 1e9:.1f} GB)")
```

See [SDK Usage Guide](docs/sdk-usage.md) for more details.

## License

MIT