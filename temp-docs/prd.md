# Ollama-OpenAI Proxy Service Product Requirements Document (PRD)

## Goals and Background Context

### Goals

- Enable zero-code migration for existing Ollama applications to work with OpenAI-compatible backends
- Maintain 100% compatibility with the official Ollama SDK
- Provide a simple, stateless proxy service that translates between Ollama and OpenAI API formats
- Support all core Ollama functionality including model listing, text generation, chat, and embeddings
- Allow deployment via multiple methods: Docker, Docker Compose, Python wheel, and PyPI
- Ensure reliable streaming support for real-time responses
- Minimize dependencies and complexity following KISS principles

### Background Context

The Ollama-OpenAI Proxy Service addresses a critical migration challenge faced by organizations using Ollama-based applications. Many teams have built integrations using the Ollama API and SDK but need to leverage OpenAI or OpenAI-compatible services for enhanced capabilities, cost optimization, or organizational requirements. Currently, this migration requires significant code rewrites and testing efforts. This proxy service eliminates that barrier by acting as a transparent translation layer, allowing existing Ollama applications to communicate with OpenAI backends without any code modifications.

The service implements the Ollama API specification while using the OpenAI Python SDK as a client library to communicate with backends. This architectural approach ensures reliability through the use of official SDKs while maintaining the simplicity needed for a translation-only service.

### Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-01-23 | 1.0 | Initial PRD creation from existing documentation | Eyal Rot |

## Requirements

### Functional

- FR1: The proxy service MUST implement the Ollama API specification endpoints to maintain compatibility with the official Ollama SDK
- FR2: The service MUST translate Ollama API requests to OpenAI API format using the official OpenAI Python SDK as a client library
- FR3: The service MUST support the `/api/tags` endpoint to list available models, translating OpenAI's `/v1/models` response to Ollama format
- FR4: The service MUST support the `/api/generate` endpoint for text generation, converting between Ollama and OpenAI completion formats
- FR5: The service MUST support the `/api/chat` endpoint for conversational interactions with message history
- FR6: The service MUST support the `/api/embeddings` and `/api/embed` endpoints for generating text embeddings
- FR7: The service MUST handle both streaming and non-streaming responses using Server-Sent Events (SSE) for Ollama format
- FR8: The service MUST properly map OpenAI errors to Ollama-compatible error responses
- FR9: The service MUST support configuration via environment variables for API endpoints and authentication
- FR10: The service MUST work with any OpenAI-compatible backend by configuring the base URL
- FR11: Optional endpoints (`/api/pull`, `/api/push`, `/api/delete`) MUST return static success responses to maintain compatibility

### Non Functional

- NFR1: The service MUST be stateless with no session storage or request history
- NFR2: All endpoints MUST be tested using the official Ollama SDK to ensure compatibility
- NFR3: The service MUST achieve 100% Ollama SDK method coverage in integration tests
- NFR4: Unit test coverage MUST be at least 80% for translation logic
- NFR5: The service MUST use Python 3.12 or higher for enhanced async performance
- NFR6: The service MUST support deployment via Docker, Docker Compose, Python wheel, and PyPI
- NFR7: Response latency MUST not exceed 100ms overhead compared to direct API calls (excluding model processing time)
- NFR8: The service MUST handle streaming responses without buffering entire content
- NFR9: Error responses MUST maintain Ollama's expected error structure and status codes
- NFR10: The service MUST NOT log sensitive information including API keys or request/response bodies
- NFR11: All external inputs MUST be validated using Pydantic before processing

## Technical Assumptions

### Repository Structure: Monorepo

The entire proxy service will be contained in a single repository including all source code, tests, deployment configurations, and documentation.

### Service Architecture

**CRITICAL DECISION** - The service follows a stateless microservice architecture pattern acting as an API Gateway. It contains:
- Single FastAPI application exposing Ollama API endpoints
- Translation engine for format conversion
- OpenAI SDK client wrapper for backend communication
- No complex state management or business logic
- Horizontal scalability through stateless design

### Testing Requirements

**CRITICAL DECISION** - Testing strategy prioritizes Ollama SDK compatibility:
- Unit tests: Required for all translation logic with 80% coverage minimum
- Integration tests: CRITICAL - Must use official Ollama SDK for all endpoint testing
- SDK Compatibility Matrix: Test against multiple Ollama SDK versions
- Performance tests: Latency comparison between direct Ollama and proxy
- Continuous testing: Run on every PR, block merge on failure
- No manual testing required - all testing automated through SDK

### Additional Technical Assumptions and Requests

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

## Epic List

- Epic 1: Foundation & Core Translation: Establish project infrastructure and implement the `/api/tags` endpoint with full Ollama SDK compatibility testing
- Epic 2: Text Generation & Streaming: Implement `/api/generate` endpoint with both streaming and non-streaming support, ensuring complete SDK compatibility
- Epic 3: Advanced Features & Distribution: Add chat and embeddings endpoints, complete SDK coverage, and create distribution packages

## Epic 1: Foundation & Core Translation

Establish the foundational project structure, development environment, and core translation capabilities. This epic delivers a working proxy service that can list models through the Ollama SDK, proving the translation architecture works end-to-end. By the end of this epic, users can point their Ollama SDK at the proxy and successfully list available models from an OpenAI backend.

### Story 1.1: Project Foundation and Structure

As a developer,
I want to set up the initial project structure with all necessary configurations,
so that I have a solid foundation for building the proxy service.

#### Acceptance Criteria

1: The project has a complete Python package structure with src/, tests/, and docker/ directories
2: FastAPI application runs locally with a health check endpoint returning service status
3: Development environment is configured with all required dependencies in requirements.txt and requirements-dev.txt
4: Docker development environment works with hot-reload enabled
5: Basic logging is configured with JSON structured output
6: Git repository is initialized with appropriate .gitignore for Python projects
7: pyproject.toml is configured for modern Python packaging
8: Pre-commit hooks are set up for ruff linting and formatting

### Story 1.2: Configuration Management

As a developer,
I want to implement environment-based configuration management,
so that the service can be easily configured for different deployments.

#### Acceptance Criteria

1: Configuration system loads from environment variables with sensible defaults
2: OPENAI_API_BASE_URL and OPENAI_API_KEY are configurable via environment
3: PROXY_PORT (default 11434) and LOG_LEVEL are configurable
4: .env.example file documents all configuration options
5: Configuration validation ensures required settings are present at startup
6: Configuration values are accessible throughout the application via a config module

### Story 1.3: OpenAI SDK Client Wrapper

As a developer,
I want to create a wrapper around the OpenAI SDK client,
so that I can manage API communication consistently.

#### Acceptance Criteria

1: AsyncOpenAI client is initialized with configuration from environment
2: Client wrapper handles authentication using provided API key
3: Client wrapper provides methods for all required OpenAI operations (list models, chat completions, embeddings)
4: Error handling captures OpenAI SDK exceptions and re-raises as appropriate
5: Unit tests verify client initialization and error handling
6: Client uses connection pooling for efficient resource usage

### Story 1.4: Implement /api/tags Endpoint

As an Ollama SDK user,
I want to list available models using the standard client.list() method,
so that I can discover what models are available through the proxy.

#### Acceptance Criteria

1: GET /api/tags endpoint is implemented in FastAPI
2: Endpoint calls OpenAI SDK's models.list() to fetch available models
3: Response is transformed from OpenAI format to Ollama's expected format
4: Response includes model name, modified_at timestamp, and size fields
5: Error responses maintain Ollama's error format
6: Endpoint handles OpenAI API errors gracefully with proper status codes

### Story 1.5: Translation Engine for Model Listing

As a developer,
I want to implement the translation logic for model listing,
so that OpenAI model data is correctly converted to Ollama format.

#### Acceptance Criteria

1: Translation function converts OpenAI model objects to Ollama format
2: Model IDs are preserved as Ollama model names
3: Timestamps are converted to ISO format as expected by Ollama
4: Model size is calculated or provided as a reasonable default
5: Translation is covered by comprehensive unit tests
6: Edge cases like empty model lists are handled correctly

### Story 1.6: Ollama SDK Integration Testing Setup

As a developer,
I want to set up integration testing using the official Ollama SDK,
so that I can verify true compatibility with Ollama clients.

#### Acceptance Criteria

1: Test fixtures create an Ollama client pointing to the test server
2: Test server runs with mocked OpenAI responses for consistent testing
3: pytest-asyncio is configured for async test support
4: Integration test directory structure separates SDK tests from unit tests
5: Conftest.py provides reusable fixtures for Ollama client and test server
6: Test documentation explains how to run integration tests

### Story 1.7: Ollama SDK Compatibility Test for Model Listing

As an Ollama SDK user,
I want to verify that client.list() works exactly as expected,
so that I know the proxy maintains full compatibility.

#### Acceptance Criteria

1: Integration test uses official Ollama SDK to call client.list()
2: Test verifies that models are returned in the expected format
3: Test confirms model names, timestamps, and sizes are present
4: Test handles empty model list scenario
5: Test verifies error handling when backend is unavailable
6: Test passes with real Ollama SDK (not mocked HTTP calls)

## Epic 2: Text Generation & Streaming

Implement the core text generation functionality with full streaming support. This epic delivers the ability to generate text using Ollama's generate() method, supporting both streaming and non-streaming modes. This is the most critical functionality for most Ollama applications, enabling them to perform AI text generation through OpenAI backends.

### Story 2.1: Implement /api/generate Endpoint

As an Ollama SDK user,
I want to generate text using client.generate() method,
so that I can create AI-generated content through the proxy.

#### Acceptance Criteria

1: POST /api/generate endpoint is implemented in FastAPI
2: Endpoint accepts Ollama generate request format with model, prompt, and options
3: Request is validated using Pydantic models
4: Endpoint supports both streaming and non-streaming modes based on request
5: Non-streaming responses return complete JSON response
6: Streaming responses use Server-Sent Events format

### Story 2.2: Translation Engine for Generate Requests

As a developer,
I want to translate Ollama generate requests to OpenAI chat completion format,
so that the requests can be processed by OpenAI backends.

#### Acceptance Criteria

1: Translation function converts Ollama prompt to OpenAI messages format
2: Ollama options (temperature, top_p, etc.) are mapped to OpenAI parameters
3: Model name is preserved in the OpenAI request
4: Stream parameter is correctly passed through
5: Translation handles missing optional parameters with defaults
6: Unit tests cover all parameter mappings and edge cases

### Story 2.3: Translation Engine for Generate Responses

As a developer,
I want to translate OpenAI completion responses back to Ollama format,
so that Ollama clients receive expected response structure.

#### Acceptance Criteria

1: Translation converts OpenAI chat completion to Ollama generate response
2: Response includes model, created_at, response text, and done flag
3: Timestamps are converted to ISO format
4: Token usage information is included if available
5: Translation handles both complete and streamed responses
6: Error responses maintain Ollama's expected structure

### Story 2.4: Streaming Response Implementation

As an Ollama SDK user,
I want to receive streaming responses for real-time text generation,
so that I can see output as it's being generated.

#### Acceptance Criteria

1: Streaming endpoint returns Server-Sent Events (SSE) format
2: Each chunk is a complete JSON object with Ollama format
3: Stream includes incremental response text in each chunk
4: Final chunk has done=true flag
5: Stream handles client disconnections gracefully
6: Errors during streaming are properly formatted and sent

### Story 2.5: Ollama SDK Integration Test for Generate

As an Ollama SDK user,
I want to verify client.generate() works for non-streaming requests,
so that I can generate complete responses.

#### Acceptance Criteria

1: Integration test uses Ollama SDK to call generate() without streaming
2: Test verifies complete response is returned with expected fields
3: Test confirms response text is present and non-empty
4: Test verifies model name matches request
5: Test checks done=true flag is set
6: Multiple prompts are tested to ensure consistency

### Story 2.6: Ollama SDK Integration Test for Streaming

As an Ollama SDK user,
I want to verify streaming generation works with the SDK,
so that I can build real-time applications.

#### Acceptance Criteria

1: Integration test uses Ollama SDK with stream=True parameter
2: Test collects all chunks from the stream
3: Test verifies each chunk has correct format
4: Test confirms final chunk has done=true
5: Test reconstructs full response from chunks
6: Test verifies streaming provides same result as non-streaming

### Story 2.7: Error Handling for Generation

As a developer,
I want comprehensive error handling for generation requests,
so that clients receive appropriate error messages.

#### Acceptance Criteria

1: Rate limit errors (429) are properly translated to Ollama format
2: Authentication errors (401) return appropriate Ollama error structure
3: Model not found errors are handled with clear messages
4: Network timeouts are caught and reported
5: Invalid request parameters return 400 with details
6: All errors include correlation IDs for debugging

## Epic 3: Advanced Features & Distribution

Complete the proxy implementation with chat and embeddings support, then package for distribution. This epic delivers the remaining Ollama SDK functionality and makes the service easily deployable through multiple channels. By the end, users have a production-ready proxy service available via Docker, PyPI, or direct installation.

### Story 3.1: Implement /api/chat Endpoint

As an Ollama SDK user,
I want to have chat conversations using client.chat() method,
so that I can build conversational AI applications.

#### Acceptance Criteria

1: POST /api/chat endpoint is implemented with message history support
2: Endpoint accepts messages array with role and content
3: Request validation ensures message format is correct
4: Both streaming and non-streaming modes are supported
5: Response includes assistant message with proper format
6: System messages are properly handled if present

### Story 3.2: Chat Translation Engine

As a developer,
I want to translate between Ollama and OpenAI chat formats,
so that conversations work seamlessly.

#### Acceptance Criteria

1: Ollama messages format maps directly to OpenAI format
2: Role mappings are preserved (user, assistant, system)
3: Message content is passed through without modification
4: Chat options are translated to OpenAI parameters
5: Response includes message object with role and content
6: Translation handles multi-turn conversations correctly

### Story 3.3: Implement /api/embeddings Endpoints

As an Ollama SDK user,
I want to generate embeddings using client.embeddings() method,
so that I can create vector representations of text.

#### Acceptance Criteria

1: POST /api/embeddings endpoint is implemented
2: POST /api/embed endpoint aliases to same functionality
3: Endpoint accepts model and prompt parameters
4: Request is translated to OpenAI embeddings format
5: Response returns embedding array in Ollama format
6: Both endpoints return identical responses

### Story 3.4: Embeddings Translation Engine

As a developer,
I want to translate embedding requests and responses,
so that vector operations work correctly.

#### Acceptance Criteria

1: Ollama prompt is converted to OpenAI input format
2: Model name is correctly mapped
3: OpenAI embedding response is extracted to array format
4: Response contains only the embedding array as expected by Ollama
5: High-dimensional embeddings are handled without truncation
6: Unit tests verify dimension preservation

### Story 3.5: Comprehensive SDK Integration Test Suite

As a developer,
I want a complete test suite validating all Ollama SDK methods,
so that I can ensure full compatibility.

#### Acceptance Criteria

1: Test suite covers client.list(), generate(), chat(), and embeddings()
2: Each method is tested with multiple parameter combinations
3: Edge cases like empty prompts and long texts are tested
4: Error scenarios are validated for each endpoint
5: Performance benchmarks compare proxy overhead to direct calls
6: Test report shows 100% SDK method coverage

### Story 3.6: Docker Production Build

As a DevOps engineer,
I want production-ready Docker images,
so that I can deploy the service easily.

#### Acceptance Criteria

1: Dockerfile uses multi-stage build for size optimization
2: Final image is based on python:3.12-slim
3: Health check endpoint is configured in Docker
4: Image runs as non-root user for security
5: Build process is documented in README
6: Docker Compose file provided for local deployment

### Story 3.7: Python Package Distribution

As a Python developer,
I want to install the proxy via pip,
so that I can integrate it into my Python environment.

#### Acceptance Criteria

1: Package builds as universal wheel with proper metadata
2: Setup.py and pyproject.toml are properly configured
3: Package includes all necessary files via MANIFEST.in
4: CLI entry point allows running via 'ollama-openai-proxy' command
5: Package can be installed with 'pip install ollama-openai-proxy'
6: Documentation includes PyPI installation instructions

### Story 3.8: Documentation and Examples

As a user,
I want comprehensive documentation and examples,
so that I can quickly start using the proxy service.

#### Acceptance Criteria

1: README includes quick start guide with Docker and pip options
2: Configuration options are fully documented with examples
3: Example code shows Ollama SDK usage with proxy
4: Troubleshooting section covers common issues
5: API compatibility matrix documents supported features
6: Migration guide helps users switch from Ollama to proxy

## Checklist Results Report

*To be populated after pm-checklist execution*

## Next Steps

### UX Expert Prompt

Not applicable - this is a backend-only API service with no user interface requirements.

### Architect Prompt

Create a comprehensive architecture document for the Ollama-OpenAI Proxy Service using this PRD as the foundation. Focus on designing a simple, stateless translation layer that maintains 100% compatibility with the Ollama SDK while using the OpenAI Python SDK for backend communication. Ensure the architecture supports multiple deployment methods and emphasizes testability with the official Ollama SDK.