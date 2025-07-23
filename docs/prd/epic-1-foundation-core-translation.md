# Epic 1: Foundation & Core Translation

Establish the foundational project structure, development environment, and core translation capabilities. This epic delivers a working proxy service that can list models through the Ollama SDK, proving the translation architecture works end-to-end. By the end of this epic, users can point their Ollama SDK at the proxy and successfully list available models from an OpenAI backend.

## Story 1.1: Project Foundation and Structure

As a developer,
I want to set up the initial project structure with all necessary configurations,
so that I have a solid foundation for building the proxy service.

### Acceptance Criteria

1: The project has a complete Python package structure with src/, tests/, and docker/ directories
2: FastAPI application runs locally with a health check endpoint returning service status
3: Development environment is configured with all required dependencies in requirements.txt and requirements-dev.txt
4: Docker development environment works with hot-reload enabled
5: Basic logging is configured with JSON structured output
6: Git repository is initialized with appropriate .gitignore for Python projects
7: pyproject.toml is configured for modern Python packaging
8: Pre-commit hooks are set up for ruff linting and formatting

## Story 1.2: Configuration Management

As a developer,
I want to implement environment-based configuration management,
so that the service can be easily configured for different deployments.

### Acceptance Criteria

1: Configuration system loads from environment variables with sensible defaults
2: OPENAI_API_BASE_URL and OPENAI_API_KEY are configurable via environment
3: PROXY_PORT (default 11434) and LOG_LEVEL are configurable
4: .env.example file documents all configuration options
5: Configuration validation ensures required settings are present at startup
6: Configuration values are accessible throughout the application via a config module

## Story 1.3: OpenAI SDK Client Wrapper

As a developer,
I want to create a wrapper around the OpenAI SDK client,
so that I can manage API communication consistently.

### Acceptance Criteria

1: AsyncOpenAI client is initialized with configuration from environment
2: Client wrapper handles authentication using provided API key
3: Client wrapper provides methods for all required OpenAI operations (list models, chat completions, embeddings)
4: Error handling captures OpenAI SDK exceptions and re-raises as appropriate
5: Unit tests verify client initialization and error handling
6: Client uses connection pooling for efficient resource usage

## Story 1.4: Implement /api/tags Endpoint

As an Ollama SDK user,
I want to list available models using the standard client.list() method,
so that I can discover what models are available through the proxy.

### Acceptance Criteria

1: GET /api/tags endpoint is implemented in FastAPI
2: Endpoint calls OpenAI SDK's models.list() to fetch available models
3: Response is transformed from OpenAI format to Ollama's expected format
4: Response includes model name, modified_at timestamp, and size fields
5: Error responses maintain Ollama's error format
6: Endpoint handles OpenAI API errors gracefully with proper status codes

## Story 1.5: Translation Engine for Model Listing

As a developer,
I want to implement the translation logic for model listing,
so that OpenAI model data is correctly converted to Ollama format.

### Acceptance Criteria

1: Translation function converts OpenAI model objects to Ollama format
2: Model IDs are preserved as Ollama model names
3: Timestamps are converted to ISO format as expected by Ollama
4: Model size is calculated or provided as a reasonable default
5: Translation is covered by comprehensive unit tests
6: Edge cases like empty model lists are handled correctly

## Story 1.6: Ollama SDK Integration Testing Setup

As a developer,
I want to set up integration testing using the official Ollama SDK,
so that I can verify true compatibility with Ollama clients.

### Acceptance Criteria

1: Test fixtures create an Ollama client pointing to the test server
2: Test server runs with mocked OpenAI responses for consistent testing
3: pytest-asyncio is configured for async test support
4: Integration test directory structure separates SDK tests from unit tests
5: Conftest.py provides reusable fixtures for Ollama client and test server
6: Test documentation explains how to run integration tests

## Story 1.7: Ollama SDK Compatibility Test for Model Listing

As an Ollama SDK user,
I want to verify that client.list() works exactly as expected,
so that I know the proxy maintains full compatibility.

### Acceptance Criteria

1: Integration test uses official Ollama SDK to call client.list()
2: Test verifies that models are returned in the expected format
3: Test confirms model names, timestamps, and sizes are present
4: Test handles empty model list scenario
5: Test verifies error handling when backend is unavailable
6: Test passes with real Ollama SDK (not mocked HTTP calls)
