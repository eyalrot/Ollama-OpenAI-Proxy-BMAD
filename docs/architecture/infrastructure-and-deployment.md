# Infrastructure and Deployment

## Infrastructure as Code

- **Tool:** Docker 24.0, Docker Compose 2.23
- **Location:** `docker/`
- **Approach:** Containerized deployment with environment-based configuration
- **CI/CD:** GitHub Actions for automated testing and deployment
- **Development Environment:** Python virtual environments (venv) for local development only

## Deployment Strategy

- **Strategy:** Multiple deployment options - Docker, Docker Compose, Python wheel, PyPI
- **CI/CD Platform:** GitHub Actions
- **Pipeline Configuration:** `.github/workflows/test.yml` (testing), `.github/workflows/deploy.yml` (deployment)
- **Environment Isolation Strategy:**
  - Local Development: Python venv required
  - CI/CD: Isolated containers (no venv)
  - Production: Docker containers (no venv)

## Deployment Options

### 1. Docker Deployment
- Build Docker image with multi-stage build for optimization
- Push to container registry (Docker Hub, GitHub Container Registry, etc.)
- Deploy single container or orchestrated with Kubernetes

### 2. Docker Compose Deployment
- Local development with hot-reload
- Multi-service deployment with dependencies
- Environment-specific compose files (dev, prod)

### 3. Python Wheel Distribution
- Build universal wheel for distribution
- Include all dependencies in requirements
- Support for offline installation

### 4. PyPI Distribution
- Publish as `ollama-openai-proxy` package
- Semantic versioning (major.minor.patch)
- Installation via `pip install ollama-openai-proxy`
- CLI entry point for direct execution

## Environments

### Development Environment
- **Local Setup:** Python 3.12+ with virtual environment (venv)
- **Container Option:** Docker with hot-reload enabled - http://localhost:11434
- **Virtual Environment Requirements:**
  ```bash
  python -m venv venv
  source venv/bin/activate  # Linux/Mac
  venv\Scripts\activate     # Windows
  pip install -r requirements-dev.txt
  ```

### CI/CD Environment
- **Platform:** GitHub Actions
- **Isolation:** Fresh container for each run
- **Dependencies:** Direct pip install (no venv needed)
- **Test Execution:** Automated on every push

### Staging Environment
- **Deployment:** Containerized with production-like config
- **Purpose:** Validate before production deployment
- **Access:** Protected, requires authentication

### Production Environment
- **Deployment:** Docker containers (no venv)
- **Architecture:** Highly available, load balanced
- **Monitoring:** Health checks, metrics, logging

## Environment Promotion Flow

```text
Local Development (venv) -> CI/CD (containers) -> Staging -> Production

1. Local development with venv and/or docker-compose
2. Push to GitHub, triggering CI pipeline
3. CI runs tests in isolated container (no venv)
4. Build Docker image and push to registry
5. Deploy to staging environment
6. Run integration tests against staging
7. Manual approval gate
8. Deploy to production
9. Smoke tests and monitoring
```

## CI/CD Pipeline Details

### GitHub Actions Workflow
```yaml
name: Test and Deploy
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      - name: Run tests
        run: |
          pytest
          ruff check .
          mypy .
```

## Rollback Strategy

- **Primary Method:** Container image rollback via orchestrator
- **Trigger Conditions:** Failed health checks, error rate > 10%, manual trigger
- **Recovery Time Objective:** < 5 minutes

## Package Distribution

```toml