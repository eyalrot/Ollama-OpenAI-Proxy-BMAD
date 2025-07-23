# Story 1.1: Project Foundation and Structure

**Story Points**: 3  
**Priority**: P0 (Must be first)  
**Type**: Infrastructure  

## Story Summary
**As a** developer,  
**I want to** set up the initial project structure with all necessary configurations,  
**So that** I have a solid foundation for building the proxy service.

## Technical Implementation Guide

### Pre-Implementation Checklist
- [ ] Python 3.12+ installed locally
- [ ] Git installed and configured
- [ ] Docker Desktop installed
- [ ] GitHub account with repository access

### Implementation Steps

#### Step 1: Create Project Structure
```bash
# Create project directory
mkdir ollama-openai-proxy && cd ollama-openai-proxy

# Initialize git repository
git init

# Create directory structure
mkdir -p src/ollama_openai_proxy
mkdir -p tests/{unit,integration}
mkdir -p docker

# Create initial Python files
touch src/ollama_openai_proxy/{__init__.py,main.py}
touch tests/__init__.py
```

#### Step 2: Set Up Virtual Environment (Local Dev)
```bash
# Create virtual environment
python -m venv venv

# Activate venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Verify venv is active
which python  # Should show path in venv directory
```

#### Step 3: Create pyproject.toml
```toml
[build-system]
requires = ["setuptools>=69.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ollama-openai-proxy"
version = "0.1.0"
description = "OpenAI-compatible proxy for Ollama API"
readme = "README.md"
requires-python = ">=3.12"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.12",
]

[project.scripts]
ollama-openai-proxy = "ollama_openai_proxy.main:main"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]

[tool.ruff]
target-version = "py312"
line-length = 100
select = ["E", "F", "I", "N", "W", "B", "RUF"]

[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

#### Step 4: Create Requirements Files
**requirements.txt**:
```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
openai==1.10.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0
```

**requirements-dev.txt**:
```txt
-r requirements.txt
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
pytest-mock==3.12.0
ruff==0.1.14
mypy==1.8.0
pre-commit==3.6.0
httpx==0.26.0
```

#### Step 5: Create Initial FastAPI Application
**src/ollama_openai_proxy/main.py**:
```python
"""Main entry point for Ollama-OpenAI Proxy Service."""
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Configure JSON logging
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

__version__ = "0.1.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    logger.info("Starting Ollama-OpenAI Proxy Service")
    yield
    logger.info("Shutting down Ollama-OpenAI Proxy Service")


app = FastAPI(
    title="Ollama-OpenAI Proxy",
    description="OpenAI-compatible proxy for Ollama API",
    version=__version__,
    lifespan=lifespan
)


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse(
        content={
            "status": "healthy",
            "version": __version__
        }
    )


def main() -> None:
    """Run the application."""
    import uvicorn
    uvicorn.run(
        "ollama_openai_proxy.main:app",
        host="0.0.0.0",
        port=11434,
        reload=True
    )


if __name__ == "__main__":
    main()
```

#### Step 6: Create .gitignore
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.coverage
.pytest_cache/
htmlcov/
.tox/
.mypy_cache/
.ruff_cache/

# Environment
.env
.env.*

# OS
.DS_Store
Thumbs.db

# Build
build/
dist/
*.egg-info/
.eggs/
```

#### Step 7: Create Docker Configuration
**docker/Dockerfile**:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies (no venv in container)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Run as non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:11434/health')"

# Run application
CMD ["python", "-m", "ollama_openai_proxy.main"]
```

**docker/docker-compose.yml**:
```yaml
version: '3.8'

services:
  proxy:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    ports:
      - "11434:11434"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ../src:/app/src  # Hot reload for development
    restart: unless-stopped
```

#### Step 8: Create Pre-commit Configuration
**.pre-commit-config.yaml**:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.14
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--strict]

  - repo: local
    hooks:
      - id: check-venv
        name: Check virtual environment (local only)
        entry: sh -c 'if [ -n "$CI" ]; then exit 0; else python -c "import sys; exit(0 if \"venv\" in sys.executable else 1)"; fi'
        language: system
        pass_filenames: false
        description: Ensure running in virtual environment for local development
```

#### Step 9: Create GitHub Actions Workflow
**.github/workflows/test.yml**:
```yaml
name: Test

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
    
    # No venv in CI - install directly
    - name: Install dependencies
      run: |
        pip install -r requirements-dev.txt
    
    - name: Run linting
      run: |
        ruff check .
        mypy src/
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=src --cov-report=xml
    
    - name: Check coverage
      run: |
        coverage report --fail-under=80
```

#### Step 10: Create Initial README
**README.md**:
```markdown
# Ollama-OpenAI Proxy

OpenAI-compatible proxy service for Ollama API, enabling Ollama applications to use OpenAI backends.

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

## License

MIT
```

#### Step 11: Create .env.example
**.env.example**:
```bash
# OpenAI Configuration (Required)
OPENAI_API_KEY=your-api-key-here

# Optional Configuration
OPENAI_API_BASE_URL=https://api.openai.com/v1
PROXY_PORT=11434
LOG_LEVEL=INFO
REQUEST_TIMEOUT=300
```

### Verification Steps

1. **Verify project structure:**
   ```bash
   tree -I 'venv|__pycache__'
   ```

2. **Test virtual environment:**
   ```bash
   which python  # Should be in venv
   pip list      # Should show installed packages
   ```

3. **Test FastAPI application:**
   ```bash
   python -m ollama_openai_proxy
   # In another terminal:
   curl http://localhost:11434/health
   ```

4. **Test Docker build:**
   ```bash
   cd docker
   docker-compose build
   docker-compose up
   ```

5. **Test pre-commit hooks:**
   ```bash
   # Make a test commit
   git add .
   git commit -m "test: Initial commit"
   ```

### Definition of Done Checklist

- [ ] All directories and files created as specified
- [ ] Virtual environment working for local development
- [ ] FastAPI app runs and health check returns correct response
- [ ] Docker build succeeds and container runs
- [ ] Pre-commit hooks installed and working
- [ ] GitHub Actions workflow file created
- [ ] README includes venv setup instructions
- [ ] .gitignore excludes venv and other artifacts
- [ ] All code passes linting (ruff)
- [ ] All code passes type checking (mypy)

### Common Issues & Solutions

1. **Python version mismatch:**
   - Ensure Python 3.12+ is installed
   - Use `python3.12 -m venv venv` if needed

2. **Port already in use:**
   - Check if port 11434 is free: `lsof -i :11434`
   - Change port in main.py if needed

3. **Docker build fails:**
   - Ensure Docker daemon is running
   - Check Docker has enough disk space

### Next Steps

After completing this story:
1. Commit all changes (except venv directory)
2. Push to feature branch
3. Create PR for review
4. Move to Story 1.2: Configuration Management