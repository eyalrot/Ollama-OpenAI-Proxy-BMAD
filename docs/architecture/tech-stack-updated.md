# Tech Stack

## Development Environment Philosophy - Updated for Docker-First Strategy

- **Local Development:** Docker-based development with multi-stage builds (transitioning from venv)
- **CI/CD:** Docker-based testing and builds with GitHub Container Registry integration
- **Production:** Optimized Docker containers with minimal attack surface
- **Future:** Dev containers for consistent development environments (separate epic)

This Docker-first approach ensures identical environments across development, CI, and production while optimizing for security and performance at each stage.

## Container Architecture Strategy

### Multi-Stage Docker Philosophy

- **Base Stage:** Common foundation with security updates and user setup
- **Dev Stage:** Development tools and hot-reload capabilities
- **CI Stage:** Testing frameworks and automation tools  
- **Prod Stage:** Minimal runtime with security hardening

### Registry and Distribution

- **Image Registry:** GitHub Container Registry (ghcr.io)
- **Image Distribution:** Public registry with automatic vulnerability scanning
- **Tagging Strategy:** Semantic versioning + SHA-based tags for traceability

## Cloud Infrastructure

- **Target Deployment:** Simple Linux hosts with Docker Compose
- **Container Runtime:** Docker 24.0+ with multi-stage build support
- **Orchestration Options:** Docker Compose (primary), Kubernetes (future)
- **Registry Integration:** GitHub Container Registry with GitHub Actions

## Updated Technology Stack Table

| Category | Technology | Version | Purpose | Docker Integration | Rationale |
|----------|------------|---------|---------|-------------------|-----------|
| **Language** | Python | 3.12 | Primary development language | python:3.12-slim base image | Latest stable, enhanced async performance |
| **Runtime** | Python | 3.12 | Application runtime | Containerized execution | Per-interpreter GIL, better error messages |
| **Framework** | FastAPI | 0.109.0 | Web framework | Optimized for container deployment | Native async, automatic OpenAPI docs |
| **HTTP Server** | Uvicorn | 0.27.0 | ASGI server | Container-native ASGI server | High performance, production-ready |
| **SDK** | OpenAI Python | 1.10.0 | OpenAI API client | Included in all Docker stages | Official SDK with retry, streaming |
| **Validation** | Pydantic | 2.5.3 | Data validation | Runtime validation in containers | Type safety, automatic validation |
| **Container Base** | Docker | 24.0 | Containerization platform | Multi-stage builds | Industry standard, security updates |
| **Container Orchestration** | Docker Compose | 2.23 | Multi-container orchestration | Development and production deployment | Simple orchestration, environment-specific configs |
| **Image Registry** | GHCR | N/A | Container image hosting | ghcr.io/[username]/ollama-openai-proxy | GitHub integration, vulnerability scanning |
| **Build System** | Docker Multi-stage | N/A | Optimized container builds | 4-stage build (base/dev/ci/prod) | Build optimization, security isolation |
| **Packaging** | setuptools | 69.0 | Python packaging | Packaged within containers | PEP 517 compliance, wheel generation |
| **Package Dist** | GHCR + PyPI | dual | Distribution channels | Container + pip distribution | Multiple deployment options |
| **Testing** | pytest | 7.4.4 | Test framework | Containerized test execution | Consistent test environments |
| **Testing** | pytest-asyncio | 0.23.3 | Async test support | CI stage dependency | Required for async endpoint testing |
| **Testing** | pytest-cov | 4.1.0 | Coverage reporting | CI container integration | Code coverage in Docker CI |
| **Linting** | ruff | 0.1.14 | Code linting | CI stage linting | Fast, comprehensive Python linter |
| **Type Checking** | mypy | 1.8.0 | Static type checking | CI stage type checking | Catches type errors in CI containers |
| **CI/CD Platform** | GitHub Actions | N/A | Continuous Integration | Docker build and test automation | GitHub integration, GHCR publishing |
| **CI/CD Registry** | GHCR | N/A | Image publishing | ghcr.io automated publishing | Secure, integrated with GitHub |
| **Pre-commit** | pre-commit | 3.6.0 | Git hooks | Local development quality gates | Automated code quality checks |

## Container-Specific Dependencies

### Base Stage Dependencies
```dockerfile
# Security and foundation
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user setup
RUN useradd -m appuser && chown -R appuser:appuser /app
```

### Development Stage Dependencies  
```dockerfile
# Development tools (future dev containers)
RUN pip install --no-cache-dir \
    debugpy \
    ipython \
    jupyterlab
```

### CI Stage Dependencies
```dockerfile
# Testing and quality tools
RUN pip install --no-cache-dir \
    pytest==7.4.4 \
    pytest-asyncio==0.23.3 \
    pytest-cov==4.1.0 \
    ruff==0.1.14 \
    mypy==1.8.0
```

### Production Stage Dependencies
```dockerfile
# Runtime only - minimal installation
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

## Environment-Specific Configurations

### Development Environment
- **Docker Target:** `dev`
- **Port Mapping:** 11434:11434 with hot-reload
- **Volume Mounts:** Source code mounted for development
- **Environment:** `.env.local` with development settings

### CI Environment  
- **Docker Target:** `ci`
- **Test Execution:** Isolated container with test dependencies
- **Environment:** GitHub Actions secrets and environment variables
- **Output:** Test results, coverage reports, built images

### Production Environment
- **Docker Target:** `prod`
- **Security:** Non-root user, minimal dependencies
- **Health Checks:** Comprehensive health endpoint validation
- **Environment:** Production secrets via environment variables

## Build and Deployment Pipeline

### Docker Build Strategy
```yaml
# Multi-stage build targets
Build Stages:
  - base: python:3.12-slim + security setup
  - dev: base + development tools
  - ci: base + testing frameworks  
  - prod: base + runtime only

Image Tags:
  - latest: Latest stable production
  - v1.0.0: Semantic version tags
  - sha-abc123: Commit-based traceability
  - dev: Development builds
```

### GitHub Actions Integration
```yaml
Pipeline Stages:
  1. Build multi-stage images (dev, ci, prod)
  2. Run tests in CI container
  3. Security scan production image
  4. Publish to GHCR on successful builds
  5. Tag and release on version bumps
```

## Performance Characteristics

### Container Optimization Metrics
- **Base Image Size:** ~100MB (python:3.12-slim)
- **Production Image Size:** ~200MB (with dependencies)  
- **Dev Image Size:** ~300MB (with dev tools)
- **CI Image Size:** ~250MB (with test frameworks)
- **Build Time:** ~2-3 minutes with layer caching

### Runtime Performance
- **Startup Time:** <5 seconds for production containers
- **Memory Usage:** ~50MB baseline + request handling
- **Response Time:** <100ms proxy overhead maintained
- **Health Check:** <1 second response time

## Security Considerations

### Container Security
- **Base Image:** Regular security updates via python:3.12-slim
- **User Context:** Non-root execution (appuser:appuser)
- **Attack Surface:** Minimal dependencies in production stage
- **Network Isolation:** Container networking with defined ports

### Registry Security
- **Access Control:** GitHub token-based authentication
- **Vulnerability Scanning:** Automatic GHCR scanning
- **Image Signing:** Docker Content Trust capability
- **Audit Trail:** Complete build and deployment traceability

## Migration Path

### From Current State (venv-based)
1. **Phase 1:** Implement multi-stage Dockerfile (Story 3.6)
2. **Phase 2:** Migrate CI to Docker-based builds
3. **Phase 3:** Update production deployment to GHCR images
4. **Phase 4:** Future dev containers integration (separate epic)

### Backwards Compatibility
- **PyPI Distribution:** Maintained alongside container distribution
- **Local Development:** Docker Compose replaces venv (gradual transition)
- **CI/CD:** GitHub Actions enhanced, not replaced
- **Documentation:** Updated deployment guides

## Future Technology Considerations

### Container Orchestration Evolution
- **Kubernetes Migration:** Container architecture ready for K8s
- **Service Mesh:** Istio/Linkerd integration capability
- **Monitoring:** Prometheus/Grafana container metrics

### Development Environment Evolution  
- **Dev Containers:** VS Code integration (separate epic)
- **Remote Development:** Cloud-based development environments
- **Debugging:** Container-native debugging workflows