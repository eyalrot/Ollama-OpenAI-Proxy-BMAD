# Infrastructure and Deployment

## Infrastructure as Code

- **Tool:** Docker 24.0 with multi-stage builds, Docker Compose 2.23
- **Location:** `docker/Dockerfile` (multi-stage), `docker/docker-compose.*.yml`
- **Approach:** Docker-first strategy with multi-stage optimization for dev, CI, and production
- **CI/CD:** GitHub Actions with Docker-based builds and GHCR publishing
- **Registry:** GitHub Container Registry (ghcr.io) for image hosting

## Multi-Stage Docker Architecture

### Docker Strategy Overview

The project uses a single multi-stage Dockerfile to optimize for different environments:

```dockerfile
# Stage 1: base - Common foundation
FROM python:3.12-slim as base
# Security updates, user creation, common dependencies

# Stage 2: dev - Development environment  
FROM base as dev
# Development dependencies, debugging tools
# Hot-reload configuration (for future dev containers)

# Stage 3: ci - CI/Testing environment
FROM base as ci
# Testing dependencies (pytest, coverage, ruff, mypy)
# Optimized for automated testing in GitHub Actions

# Stage 4: prod - Production runtime
FROM base as prod
# Only runtime dependencies
# Minimal attack surface, security hardened
```

### Stage-Specific Optimizations

| Stage | Purpose | Dependencies | Size Target | Security |
|-------|---------|--------------|-------------|----------|
| `base` | Common foundation | Core Python deps | Minimal base | User setup, security updates |
| `dev` | Local development | + dev tools, debuggers | Medium | Dev-friendly |
| `ci` | CI/CD testing | + test frameworks, linting | Medium | Test-optimized |
| `prod` | Production runtime | Runtime only | Minimal | Hardened, non-root |

## Deployment Strategy

### Docker-First Approach

- **Primary Strategy:** Containerized deployment across all environments
- **CI/CD Platform:** GitHub Actions with Docker builds
- **Image Registry:** GitHub Container Registry (ghcr.io)
- **Pipeline Configuration:** 
  - `.github/workflows/docker-build.yml` (Docker builds + GHCR)
  - `.github/workflows/test.yml` (updated for Docker-based testing)

### Image Tagging Strategy

```text
ghcr.io/[username]/ollama-openai-proxy:latest     # Latest stable
ghcr.io/[username]/ollama-openai-proxy:v1.0.0     # Version tags
ghcr.io/[username]/ollama-openai-proxy:sha-abc123  # Commit-based
ghcr.io/[username]/ollama-openai-proxy:dev        # Development builds
```

## Environment Architecture

### Development Environment Strategy

**Multi-Stage Target: `dev`**
```bash
# Build dev image
docker build --target dev -t ollama-proxy:dev .

# Run with hot-reload (future dev containers support)
docker-compose -f docker/docker-compose.dev.yml up
```

**Characteristics:**
- Hot-reload volumes for code changes
- Development tools and debuggers included
- Port 11434 exposed for local testing
- Environment variables from `.env.local`

### CI/CD Environment Strategy

**Multi-Stage Target: `ci`**
```yaml
# GitHub Actions CI Pipeline
- name: Build CI image
  run: docker build --target ci -t ollama-proxy:ci .
  
- name: Run tests in Docker
  run: docker run --rm ollama-proxy:ci pytest
```

**Characteristics:**
- Isolated test environment matching production base
- All test dependencies included (pytest, coverage, ruff, mypy)
- No external dependencies required
- Faster builds with layer caching

### Production Environment Strategy

**Multi-Stage Target: `prod`**
```bash
# Production deployment
docker-compose -f docker/docker-compose.prod.yml up -d
```

**Characteristics:**
- Minimal attack surface (runtime dependencies only)
- Non-root user execution (appuser)
- Health checks and monitoring hooks
- Optimized for container orchestration

## Updated CI/CD Pipeline Architecture

### Docker-Based Testing Pipeline

```yaml
name: Docker Build and Test
on:
  push:
    branches: [master, main]
  pull_request:
    branches: [master, main]

jobs:
  docker-build-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      # Build multi-stage images
      - name: Build CI image
        run: docker build --target ci -t ollama-proxy:ci .
        
      - name: Build production image
        run: docker build --target prod -t ollama-proxy:prod .
      
      # Run tests in Docker
      - name: Run tests in CI container
        run: |
          docker run --rm \
            -e OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }} \
            ollama-proxy:ci \
            pytest --cov=src --cov-report=xml
      
      # Test production image
      - name: Test production image health
        run: |
          docker run -d --name test-prod -p 11434:11434 ollama-proxy:prod
          sleep 5
          curl -f http://localhost:11434/health
          docker stop test-prod
```

### GitHub Container Registry Integration

```yaml
  publish:
    needs: docker-build-test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/master'
    steps:
      - name: Login to GHCR
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push production image
        run: |
          docker build --target prod -t ghcr.io/${{ github.repository }}:latest .
          docker push ghcr.io/${{ github.repository }}:latest
```

## Production Deployment Architecture

### Target Environment: Simple Linux with Docker Compose

**Production docker-compose.prod.yml:**
```yaml
version: '3.8'

services:
  ollama-proxy:
    image: ghcr.io/[username]/ollama-openai-proxy:latest
    container_name: ollama-openai-proxy
    restart: unless-stopped
    ports:
      - "11434:11434"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ./logs:/app/logs:rw
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:11434/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - proxy-network

networks:
  proxy-network:
    driver: bridge
```

### Production Deployment Process

```bash
# Production deployment steps
1. Pull latest image: docker pull ghcr.io/[username]/ollama-openai-proxy:latest
2. Update environment: cp .env.prod .env
3. Deploy service: docker-compose -f docker/docker-compose.prod.yml up -d
4. Verify health: curl http://localhost:11434/health
5. Monitor logs: docker-compose logs -f ollama-proxy
```

## Security Architecture

### Container Security

- **Base Image:** python:3.12-slim with regular security updates
- **User Context:** Non-root user (appuser) in all stages
- **File Permissions:** Minimal required permissions
- **Attack Surface:** Production image contains only runtime dependencies
- **Network:** Isolated container networks in production

### Registry Security

- **Authentication:** GitHub token-based authentication
- **Vulnerability Scanning:** Automatic GHCR vulnerability scanning
- **Access Control:** Repository-based access permissions
- **Image Signing:** Docker Content Trust (optional)

## Monitoring and Observability

### Health Checks

```python
# Enhanced health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": __version__,
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv("ENV", "production")
    }
```

### Container Monitoring

- **Health Checks:** Docker HEALTHCHECK instruction
- **Logging:** Structured JSON logs to stdout/stderr  
- **Metrics:** Application metrics endpoint (/metrics)
- **Graceful Shutdown:** SIGTERM handling for clean container stops

## Rollback Strategy

### Container Image Rollback

- **Method:** Tag-based rollback via docker-compose
- **Command:** `docker-compose pull && docker-compose up -d [service]`
- **Recovery Time:** < 2 minutes (image pull + container restart)
- **Rollback Triggers:** Failed health checks, error rate > 5%

### Rollback Process

```bash
# Emergency rollback procedure
1. Identify last known good version: docker image ls ghcr.io/[username]/ollama-openai-proxy
2. Update docker-compose to use specific tag: image: ghcr.io/[username]/ollama-openai-proxy:v1.0.0
3. Redeploy: docker-compose -f docker/docker-compose.prod.yml up -d
4. Verify service: curl http://localhost:11434/health
5. Monitor metrics and logs
```

## Performance Optimizations

### Build Optimization

- **Layer Caching:** Optimized layer order for maximum cache hits
- **Multi-stage Benefits:** Smaller production images (~50% size reduction)
- **Dependency Caching:** Requirements installed in separate layer
- **Build Context:** .dockerignore excludes unnecessary files

### Runtime Optimization

- **Resource Limits:** Memory and CPU limits in production
- **Health Check Tuning:** Optimized intervals and timeouts
- **Log Rotation:** Container log rotation policies
- **Network Optimization:** Bridge networks for service isolation

## Future Architecture Considerations

### Dev Containers Integration (Separate Epic)

The `dev` stage is prepared for future dev containers implementation:
- VS Code dev container configuration
- Consistent development environment across team
- Integrated debugging and testing tools

### Container Orchestration Evolution

Current architecture supports future migration to:
- **Kubernetes:** Container-ready for orchestration
- **Docker Swarm:** Service-based deployment model
- **Cloud Services:** AWS ECS, Azure Container Instances, GCP Cloud Run