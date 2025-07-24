# Technology Stack

## Core Technologies
- **Language:** Python 3.12
- **Framework:** FastAPI 0.109.0
- **HTTP Server:** Uvicorn 0.27.0
- **SDK:** OpenAI Python 1.10.0
- **Validation:** Pydantic 2.5.3

## Development & Build Tools
- **Container:** Docker 24.0
- **Orchestration:** Docker Compose 2.23
- **Packaging:** setuptools 69.0
- **Testing:** pytest 7.4.4, pytest-asyncio 0.23.3
- **Linting:** ruff 0.1.14
- **Type Checking:** mypy 1.8.0

## CI/CD & Deployment
- **CI/CD:** GitHub Actions
- **Pre-commit:** pre-commit 3.6.0
- **Development:** Python venv (required for local dev)
- **Production:** Docker containers (no venv)

## Environment Philosophy
- **Local Development:** Python virtual environments (venv) for isolation
- **CI/CD:** Containerized environments with direct dependency installation
- **Production:** Docker containers without virtual environments