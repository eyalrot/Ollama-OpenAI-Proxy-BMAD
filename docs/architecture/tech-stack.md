# Tech Stack

## Cloud Infrastructure

- **Provider:** Any cloud provider or on-premises
- **Key Services:** Container runtime (Docker), Orchestration (Kubernetes optional)
- **Deployment Regions:** Configurable based on requirements

## Technology Stack Table

| Category | Technology | Version | Purpose | Rationale |
|----------|------------|---------|---------|-----------|
| **Language** | Python | 3.12 | Primary development language | Latest stable version, improved performance, better error messages |
| **Runtime** | Python | 3.12 | Application runtime | Enhanced async performance, per-interpreter GIL |
| **Framework** | FastAPI | 0.109.0 | Web framework | Native async, automatic OpenAPI docs, Pydantic integration |
| **HTTP Server** | Uvicorn | 0.27.0 | ASGI server | High performance, production-ready |
| **SDK** | OpenAI Python | 1.10.0 | OpenAI API client | Official SDK with built-in retry, streaming, error handling |
| **Validation** | Pydantic | 2.5.3 | Data validation | Type safety, automatic validation |
| **Container** | Docker | 24.0 | Containerization | Standard deployment format |
| **Orchestration** | Docker Compose | 2.23 | Multi-container apps | Local development and testing |
| **Packaging** | setuptools | 69.0 | Python packaging | Build wheels for distribution |
| **Package Dist** | twine | 4.0.2 | PyPI upload | Secure package uploads to PyPI |
| **Build Tool** | build | 1.0.3 | PEP 517 builder | Modern Python package building |
| **Testing** | pytest | 7.4.4 | Test framework | Powerful, extensive plugin ecosystem |
| **Testing** | pytest-asyncio | 0.23.3 | Async test support | Required for async endpoint testing |
| **Linting** | ruff | 0.1.14 | Code linting | Fast, comprehensive Python linter |
| **Type Checking** | mypy | 1.8.0 | Static type checking | Catches type errors early |
