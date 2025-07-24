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

### Docker Quick Start

```bash
# Development with hot reload
docker-compose -f docker/docker-compose.dev.yml up

# Production deployment
docker-compose -f docker/docker-compose.prod.yml up -d
```

## Docker Deployment

### Multi-Stage Docker Build

The service uses a multi-stage Dockerfile optimized for different environments:

- **Base Stage**: Security-hardened foundation with non-root user
- **Dev Stage**: Development tools and hot-reload support
- **CI Stage**: Testing frameworks for automated testing
- **Prod Stage**: Minimal runtime with < 200MB image size

### Building Images

```bash
# Build production image
docker build -f docker/Dockerfile --target prod -t ollama-openai-proxy:latest .

# Build development image
docker build -f docker/Dockerfile --target dev -t ollama-openai-proxy:dev .

# Build CI testing image
docker build -f docker/Dockerfile --target ci -t ollama-openai-proxy:ci .
```

### Running with Docker Compose

#### Development Environment

```bash
# Start development environment with hot reload
docker-compose -f docker/docker-compose.dev.yml up

# Run tests in development container
docker-compose -f docker/docker-compose.dev.yml exec ollama-proxy-dev pytest

# Access container for debugging
docker-compose -f docker/docker-compose.dev.yml exec ollama-proxy-dev bash
```

#### Production Deployment

1. **Configure environment:**
   ```bash
   cp .env.example .env.prod
   # Edit .env.prod with production values
   ```

2. **Deploy with Docker Compose:**
   ```bash
   # Pull latest image from GitHub Container Registry
   docker pull ghcr.io/[your-username]/ollama-openai-proxy:latest

   # Or use docker-compose
   docker-compose -f docker/docker-compose.prod.yml up -d

   # Check logs
   docker-compose -f docker/docker-compose.prod.yml logs -f

   # Check health
   curl http://localhost:11434/health
   curl http://localhost:11434/ready
   curl http://localhost:11434/metrics
   ```

### Using GitHub Container Registry

The CI/CD pipeline automatically publishes images to GitHub Container Registry:

```bash
# Pull specific version
docker pull ghcr.io/[your-username]/ollama-openai-proxy:v1.0.0

# Pull latest
docker pull ghcr.io/[your-username]/ollama-openai-proxy:latest

# Pull by commit SHA
docker pull ghcr.io/[your-username]/ollama-openai-proxy:sha-abc123
```

### Health Monitoring

The service provides comprehensive health endpoints:

- `/health` - Overall application health
- `/ready` - Readiness probe (checks OpenAI connectivity)
- `/live` - Liveness probe (simple alive check)
- `/metrics` - Application metrics (requests, uptime, etc.)

### Container Resource Limits

Production deployment includes resource limits:
- Memory: 256MB limit / 128MB reserved
- CPU: 0.5 CPU limit / 0.1 CPU reserved

Adjust in `docker-compose.prod.yml` based on your needs.

### Zero-Downtime Deployment

```bash
# 1. Pull new image
docker pull ghcr.io/[your-username]/ollama-openai-proxy:latest

# 2. Start new container with different name
docker run -d --name proxy-new ghcr.io/[your-username]/ollama-openai-proxy:latest

# 3. Verify new container health
curl http://localhost:11435/ready

# 4. Switch traffic (update load balancer/proxy)
# 5. Stop old container
docker stop proxy-old && docker rm proxy-old
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