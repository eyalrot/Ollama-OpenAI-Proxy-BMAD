# Docker Deployment Guide

This guide provides comprehensive instructions for deploying the Ollama-OpenAI Proxy using Docker.

## Table of Contents

- [Overview](#overview)
- [Multi-Stage Build Architecture](#multi-stage-build-architecture)
- [Development Setup](#development-setup)
- [Production Deployment](#production-deployment)
- [CI/CD Integration](#cicd-integration)
- [Monitoring and Health Checks](#monitoring-and-health-checks)
- [Troubleshooting](#troubleshooting)

## Overview

The Ollama-OpenAI Proxy uses a multi-stage Docker build strategy to optimize for different deployment scenarios:

- **Development**: Hot-reload, debugging tools, full development environment
- **CI/CD**: Automated testing, linting, and quality checks
- **Production**: Minimal, secure, optimized runtime

## Multi-Stage Build Architecture

### Stage 1: Base

The base stage provides a secure foundation for all other stages:

```dockerfile
FROM python:3.12-slim as base

# Security updates and non-root user setup
# Common dependencies installation
# Sets up /app directory with proper permissions
```

**Key Features:**
- Non-root user (`appuser:1000`)
- Security updates applied
- Minimal system packages
- Base Python dependencies

### Stage 2: Development

Extends base with development tools:

```dockerfile
FROM base as dev

# Development tools: debugpy, ipython, watchdog
# Hot-reload configuration
# Volume mount support
```

**Key Features:**
- Hot-reload support via watchdog
- Remote debugging with debugpy
- Interactive Python shell (ipython)
- Development dependencies

### Stage 3: CI

Optimized for automated testing:

```dockerfile
FROM base as ci

# Testing frameworks: pytest, coverage, mypy, ruff
# Source code included for testing
# Default command runs full test suite
```

**Key Features:**
- Complete test framework
- Code quality tools
- Coverage reporting
- Optimized for CI pipelines

### Stage 4: Production

Minimal runtime for production:

```dockerfile
FROM base as prod

# Only runtime dependencies
# Security hardening
# Health check configuration
# Optimized for size and security
```

**Key Features:**
- < 200MB image size
- Security hardened
- No development tools
- Production logging

## Development Setup

### Prerequisites

- Docker 24.0+
- Docker Compose 2.23+
- Git

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ollama-openai-proxy
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key
   ```

3. **Start development environment:**
   ```bash
   docker-compose -f docker/docker-compose.dev.yml up
   ```

4. **Access the service:**
   ```bash
   curl http://localhost:11434/health
   ```

### Development Commands

```bash
# Run tests in container
docker-compose -f docker/docker-compose.dev.yml exec ollama-proxy-dev pytest

# Access container shell
docker-compose -f docker/docker-compose.dev.yml exec ollama-proxy-dev bash

# Run linting
docker-compose -f docker/docker-compose.dev.yml exec ollama-proxy-dev ruff check src/

# Run type checking
docker-compose -f docker/docker-compose.dev.yml exec ollama-proxy-dev mypy src/

# View logs
docker-compose -f docker/docker-compose.dev.yml logs -f

# Rebuild after dependency changes
docker-compose -f docker/docker-compose.dev.yml up --build
```

### Hot Reload

The development environment supports hot-reload:
- Source code changes are automatically detected
- Service restarts automatically
- No need to rebuild the image for code changes

## Production Deployment

### Using Pre-built Images

Images are automatically published to GitHub Container Registry:

```bash
# Pull latest stable
docker pull ghcr.io/[your-username]/ollama-openai-proxy:latest

# Pull specific version
docker pull ghcr.io/[your-username]/ollama-openai-proxy:v1.0.0

# Pull by commit SHA
docker pull ghcr.io/[your-username]/ollama-openai-proxy:sha-abc123
```

### Docker Compose Deployment

1. **Create production environment file:**
   ```bash
   cp .env.example .env.prod
   ```

2. **Configure production values:**
   ```env
   OPENAI_API_KEY=your-production-key
   LOG_LEVEL=INFO
   ENV=production
   GITHUB_REPOSITORY=your-username/ollama-openai-proxy
   VERSION=v1.0.0
   ```

3. **Deploy the service:**
   ```bash
   docker-compose -f docker/docker-compose.prod.yml up -d
   ```

4. **Verify deployment:**
   ```bash
   # Check health
   curl http://localhost:11434/health
   
   # Check readiness
   curl http://localhost:11434/ready
   
   # View metrics
   curl http://localhost:11434/metrics
   ```

### Manual Docker Deployment

```bash
# Run production container
docker run -d \
  --name ollama-proxy \
  -p 11434:11434 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e LOG_LEVEL=INFO \
  -e ENV=production \
  --restart unless-stopped \
  ghcr.io/[your-username]/ollama-openai-proxy:latest

# Check logs
docker logs -f ollama-proxy

# Stop container
docker stop ollama-proxy
```

### Resource Configuration

Default resource limits (adjust as needed):

```yaml
resources:
  limits:
    memory: 256M
    cpus: '0.5'
  reservations:
    memory: 128M
    cpus: '0.1'
```

## CI/CD Integration

### GitHub Actions Workflow

The project includes automated Docker builds via GitHub Actions:

1. **On Push/PR**: Builds and tests all stages
2. **On Tag**: Publishes production images to GHCR
3. **Security Scanning**: Trivy scans for vulnerabilities

### Building in CI

```bash
# Build and test in CI
docker build --target ci -t test-image .
docker run --rm test-image

# Extract coverage report
docker run --rm test-image > coverage.xml
```

### Publishing Images

Images are automatically published with multiple tags:
- `latest` - Latest stable release
- `v1.0.0` - Semantic version tags
- `sha-abc123` - Commit SHA tags
- `pr-123` - Pull request builds

## Monitoring and Health Checks

### Health Endpoints

The service provides multiple health check endpoints:

#### `/health` - Comprehensive Health Check
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2024-01-24T10:00:00Z",
  "environment": "production",
  "container_id": "abc123",
  "configured": true,
  "port": 11434,
  "uptime_seconds": 3600,
  "openai": {
    "status": "healthy",
    "models_available": 5
  }
}
```

#### `/ready` - Readiness Probe
Checks if the service is ready to handle requests:
- Configuration loaded
- OpenAI service connected
- All dependencies initialized

#### `/live` - Liveness Probe
Simple check to verify the process is alive:
```json
{
  "status": "alive",
  "timestamp": "2024-01-24T10:00:00Z",
  "container_id": "abc123",
  "uptime_seconds": 3600
}
```

#### `/metrics` - Application Metrics
```json
{
  "app_info": {
    "name": "ollama-openai-proxy",
    "version": "0.1.0",
    "environment": "production",
    "container_id": "abc123"
  },
  "uptime_seconds": 3600,
  "requests": {
    "total": 1000,
    "success": 980,
    "failed": 20,
    "success_rate_percent": 98.0,
    "last_request_time": "2024-01-24T10:00:00Z"
  }
}
```

### Docker Health Check

The Dockerfile includes a health check configuration:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:11434/health')"
```

### Monitoring Integration

The service outputs structured JSON logs compatible with:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Prometheus (via metrics endpoint)
- CloudWatch Logs
- Datadog

Example log entry:
```json
{
  "time": "2024-01-24T10:00:00Z",
  "level": "INFO",
  "logger": "ollama_openai_proxy.main",
  "message": "Request completed",
  "container_id": "abc123",
  "environment": "production",
  "method": "POST",
  "path": "/api/generate",
  "status_code": 200,
  "duration_seconds": 0.123
}
```

## Troubleshooting

### Common Issues

#### Container Won't Start

1. **Check logs:**
   ```bash
   docker logs ollama-proxy
   ```

2. **Verify environment variables:**
   ```bash
   docker exec ollama-proxy env | grep OPENAI
   ```

3. **Check health endpoint:**
   ```bash
   curl http://localhost:11434/health
   ```

#### High Memory Usage

1. **Check current usage:**
   ```bash
   docker stats ollama-proxy
   ```

2. **Adjust limits in docker-compose.prod.yml:**
   ```yaml
   resources:
     limits:
       memory: 512M  # Increase if needed
   ```

#### Connection Issues

1. **Verify OpenAI connectivity:**
   ```bash
   curl http://localhost:11434/openai/health
   ```

2. **Check network configuration:**
   ```bash
   docker network ls
   docker network inspect proxy-network
   ```

### Debug Commands

```bash
# Access production container
docker exec -it ollama-proxy /bin/sh

# View real-time logs
docker logs -f ollama-proxy

# Check resource usage
docker stats ollama-proxy

# Inspect container
docker inspect ollama-proxy

# Test from inside container
docker exec ollama-proxy curl http://localhost:11434/health
```

### Rolling Back

If deployment fails:

```bash
# List available images
docker images | grep ollama-openai-proxy

# Run previous version
docker run -d \
  --name ollama-proxy \
  -p 11434:11434 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  ghcr.io/[your-username]/ollama-openai-proxy:v1.0.0
```

## Security Best Practices

1. **Always use specific version tags in production**
2. **Regularly update base images for security patches**
3. **Use secrets management for API keys**
4. **Enable container security scanning**
5. **Implement network policies**
6. **Use read-only root filesystem where possible**
7. **Monitor container logs for suspicious activity**

## Next Steps

- Set up monitoring dashboards
- Configure alerting rules
- Implement auto-scaling (if using Kubernetes)
- Set up backup strategies for persistent data
- Configure SSL/TLS termination