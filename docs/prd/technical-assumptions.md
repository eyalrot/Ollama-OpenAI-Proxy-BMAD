# Technical Assumptions

## Repository Structure: Monorepo

The entire proxy service will be contained in a single repository including all source code, tests, deployment configurations, and documentation.

## Service Architecture

**CRITICAL DECISION** - The service follows a stateless microservice architecture pattern acting as an API Gateway. It contains:
- Single FastAPI application exposing Ollama API endpoints
- Translation engine for format conversion
- OpenAI SDK client wrapper for backend communication
- No complex state management or business logic
- Horizontal scalability through stateless design

## Testing Requirements

**CRITICAL DECISION** - Testing strategy prioritizes Ollama SDK compatibility:
- Unit tests: Required for all translation logic with 80% coverage minimum
- Integration tests: CRITICAL - Must use official Ollama SDK for all endpoint testing
- SDK Compatibility Matrix: Test against multiple Ollama SDK versions
- Performance tests: Latency comparison between direct Ollama and proxy
- Continuous testing: Run on every PR, block merge on failure
- No manual testing required - all testing automated through SDK

## Additional Technical Assumptions and Requests

- Framework: FastAPI 0.109.0 for native async support and automatic OpenAPI documentation
- HTTP Server: Uvicorn 0.27.0 for high-performance ASGI serving
- SDK Client: OpenAI Python SDK 1.10.0 for reliable backend communication
- Validation: Pydantic 2.5.3 for type safety and automatic validation
- Testing: pytest 7.4.4 with pytest-asyncio for async testing support
- Linting: ruff for fast, comprehensive Python linting
- Type Checking: mypy for static type checking
- Deployment: Docker 24.0 with multi-stage builds for optimization
- Package Distribution: setuptools for building wheels, twine for PyPI uploads
- Error Handling: Exception-based with OpenAI SDK error mapping to HTTP status codes
- Logging: Python logging module with JSON structured output
- Configuration: Environment variables with .env file support for development
- Security: API key pass-through, no storage of credentials, HTTPS for external calls
