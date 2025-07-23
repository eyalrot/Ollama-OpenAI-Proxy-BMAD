# Epic 1: Foundation & Core Translation (Enhanced Draft)

## Epic Status: In Progress (57% Complete)

### Story Progress:
- ✅ **Story 1.1: Project Foundation and Structure** - Complete
- ✅ **Story 1.2: Configuration Management** - Complete
- ✅ **Story 1.3: OpenAI SDK Client Wrapper** - Complete
- ✅ **Story 1.4: Implement /api/tags Endpoint** - Complete
- 🔄 **Story 1.5: Translation Engine for Model Listing** - Next
- ⏳ **Story 1.6: Testing Infrastructure Setup** - Pending
- ⏳ **Story 1.7: Ollama SDK Compatibility Test Suite** - Pending

### Key Achievements:
- Project structure established with Docker and CI/CD
- Configuration management with Pydantic validation
- OpenAI service wrapper with retry logic and connection pooling
- Working /api/tags endpoint that returns OpenAI models in Ollama format
- Successfully tested with 35+ OpenAI models being translated

## Epic Overview
Establish the foundational project structure, development environment, and core translation capabilities. This epic delivers a working proxy service that can list models through the Ollama SDK, proving the translation architecture works end-to-end. By the end of this epic, users can point their Ollama SDK at the proxy and successfully list available models from an OpenAI backend.

**Epic Value**: Proves the core concept works with minimal implementation, reducing project risk early.

## Development Environment Setup

**IMPORTANT**: Local development must use virtual environments (venv) to ensure consistency and isolation.

### Local Development Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd ollama-openai-proxy

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Verify setup
which python  # Should show path within venv directory
python --version  # Should show Python 3.12+
```

### Environment Strategy Summary

| Environment | Venv Required | Why |
|-------------|---------------|-----|
| Local Development | ✅ Yes | Isolation from system Python |
| GitHub Actions CI | ❌ No | Fresh container each run |
| Docker Containers | ❌ No | Container provides isolation |
| Production | ❌ No | Runs in Docker |

## Pre-Epic Checklist
- [ ] User has OpenAI API key ready
- [ ] Development environment has Python 3.12+ installed
- [ ] Docker Desktop installed for containerized development
- [ ] Git configured for version control
- [ ] Familiarity with Python virtual environments (venv)

## Story 1.1: Project Foundation and Structure

**As a** developer,  
**I want to** set up the initial project structure with all necessary configurations,  
**So that** I have a solid foundation for building the proxy service.

### Technical Notes
- Use modern Python packaging with pyproject.toml
- Configure ruff for fast linting/formatting
- Set up proper Python package structure following best practices
- Local development must use virtual environments (venv)
- CI/CD runs in isolated environments (containers/VMs) and doesn't require venv

### Acceptance Criteria
1. The project has a complete Python package structure:
   ```
   ollama-openai-proxy/
   ├── src/
   │   └── ollama_openai_proxy/
   │       ├── __init__.py
   │       └── main.py
   ├── tests/
   │   ├── unit/
   │   └── integration/
   ├── docker/
   │   ├── Dockerfile
   │   └── docker-compose.yml
   ├── .gitignore
   ├── .python-version
   ├── pyproject.toml
   ├── requirements.txt
   ├── requirements-dev.txt
   ├── README.md
   └── venv/  # Created by developer, not committed
   ```
2. FastAPI application runs locally with a health check endpoint returning service status:
   - GET `/health` returns `{"status": "healthy", "version": "0.1.0"}`
3. Local development environment is configured with all required dependencies:
   - Virtual environment created: `python -m venv venv`
   - Virtual environment activated: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
   - Dependencies installed in venv: `pip install -r requirements-dev.txt`
   - Note: Production Docker images install dependencies directly without venv
4. Docker development environment works with hot-reload enabled
   - Docker containers install dependencies directly (no venv)
   - Dockerfile uses pip install without virtual environment
5. Basic logging is configured with JSON structured output to stdout
6. Git repository is initialized with appropriate .gitignore for Python projects including:
   - `venv/` directory excluded
   - `__pycache__/` directories excluded
   - `.env` files excluded
7. pyproject.toml is configured for modern Python packaging
8. Pre-commit hooks are set up for ruff linting and formatting:
   - `.pre-commit-config.yaml` configured for local development
   - Instructions for setup: `pre-commit install` (run from within local venv)
   - Hooks use the developer's active venv locally
9. **NEW**: Basic GitHub Actions workflow file created (`.github/workflows/test.yml`) for CI readiness:
   ```yaml
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
   ```
   Note: CI runs in isolated environment, no venv needed

### Definition of Done
- [ ] Virtual environment created and activated for local development
- [ ] Can run `python -m ollama_openai_proxy` locally (from venv) and access health endpoint
- [ ] Can run `docker-compose up` and see hot-reload working
- [ ] Pre-commit hooks configured to run in local venv
- [ ] Dockerfile installs dependencies without venv
- [ ] README includes venv setup instructions for developers

## Story 1.2: Configuration Management

**As a** developer,  
**I want to** implement environment-based configuration management,  
**So that** the service can be easily configured for different deployments.

### Technical Notes
- Use pydantic-settings for type-safe configuration
- Support both environment variables and .env files
- Validate configuration at startup

### Acceptance Criteria
1. Configuration system loads from environment variables with sensible defaults
2. Configuration model includes:
   ```python
   class Settings(BaseSettings):
       openai_api_base_url: str = "https://api.openai.com/v1"
       openai_api_key: SecretStr  # Required, no default
       proxy_port: int = 11434
       log_level: str = "INFO"
       request_timeout: int = 300  # 5 minutes
   ```
3. OPENAI_API_BASE_URL and OPENAI_API_KEY are configurable via environment
4. PROXY_PORT (default 11434) and LOG_LEVEL are configurable
5. .env.example file documents all configuration options:
   ```bash
   # For local development, ensure you're in your virtual environment
   
   # Required configuration
   OPENAI_API_KEY=your-api-key-here
   
   # Optional configuration with defaults
   OPENAI_API_BASE_URL=https://api.openai.com/v1
   PROXY_PORT=11434
   LOG_LEVEL=INFO
   ```
6. Configuration validation ensures required settings are present at startup
7. Configuration values are accessible throughout the application via a config module
8. **NEW**: Application fails fast with clear error message if required config is missing

### Definition of Done
- [ ] Service starts with valid configuration
- [ ] Service fails with helpful error when OPENAI_API_KEY is missing
- [ ] Can override settings via environment variables

## Story 1.3: OpenAI SDK Client Wrapper

**As a** developer,  
**I want to** create a wrapper around the OpenAI SDK client,  
**So that** I can manage API communication consistently.

### Technical Notes
- Use dependency injection pattern for testability
- Implement proper connection pooling
- Add request ID tracking for debugging

### Acceptance Criteria
1. AsyncOpenAI client is initialized with configuration from environment
2. Client wrapper handles authentication using provided API key
3. Client wrapper provides typed methods for required OpenAI operations:
   - `list_models() -> List[Model]`
   - `create_chat_completion(...) -> ChatCompletion`
   - `create_embedding(...) -> Embedding`
4. Error handling captures OpenAI SDK exceptions and re-raises as appropriate
5. Unit tests verify client initialization and error handling
6. Client uses connection pooling for efficient resource usage
7. **NEW**: Request/response logging (without sensitive data) for debugging
8. **NEW**: Retry logic with exponential backoff for transient failures

### Definition of Done
- [ ] Client wrapper can be mocked in tests
- [ ] All OpenAI errors are properly typed and handled
- [ ] Connection pooling is verified working

## Story 1.4: Implement /api/tags Endpoint

**As an** Ollama SDK user,  
**I want to** list available models using the standard client.list() method,  
**So that** I can discover what models are available through the proxy.

### Technical Notes
- Follow Ollama API specification exactly
- Ensure response format matches Ollama's expectations
- Add request ID to logs for tracing

### Acceptance Criteria
1. GET /api/tags endpoint is implemented in FastAPI
2. Endpoint calls OpenAI SDK's models.list() to fetch available models
3. Response is transformed from OpenAI format to Ollama's expected format:
   ```json
   {
     "models": [
       {
         "name": "gpt-3.5-turbo",
         "modified_at": "2024-01-20T10:30:00Z",
         "size": 1000000000
       }
     ]
   }
   ```
4. Response includes model name, modified_at timestamp, and size fields
5. Error responses maintain Ollama's error format
6. Endpoint handles OpenAI API errors gracefully with proper status codes
7. **NEW**: Endpoint includes cache headers to reduce API calls
8. **NEW**: Response time logged for performance monitoring

### Definition of Done
- [ ] Endpoint returns valid Ollama format response
- [ ] Error cases return appropriate HTTP status codes
- [ ] Manual test with curl confirms format

## Story 1.5: Translation Engine for Model Listing

**As a** developer,  
**I want to** implement the translation logic for model listing,  
**So that** OpenAI model data is correctly converted to Ollama format.

### Technical Notes
- Create separate translation module for reusability
- Use Pydantic models for type safety
- Consider model name mappings for compatibility

### Acceptance Criteria
1. Translation function converts OpenAI model objects to Ollama format
2. Model IDs are preserved as Ollama model names
3. Timestamps are converted to ISO format as expected by Ollama
4. Model size is calculated or provided as reasonable default (1GB)
5. Translation is covered by comprehensive unit tests
6. Edge cases like empty model lists are handled correctly
7. **NEW**: Unknown models are filtered out or mapped appropriately
8. **NEW**: Model metadata is preserved for future use

### Definition of Done
- [ ] Unit tests cover all translation scenarios
- [ ] Type hints used throughout
- [ ] Translation is a pure function (no side effects)

## Story 1.6: Testing Infrastructure Setup

**As a** developer,  
**I want to** set up comprehensive testing infrastructure,  
**So that** I can verify true compatibility with Ollama clients.

### Technical Notes
- Use pytest-asyncio for async testing
- Create reusable fixtures for test client and mocked OpenAI
- Set up coverage reporting

### Acceptance Criteria
1. Test fixtures create an Ollama client pointing to the test server
2. Test server runs with mocked OpenAI responses for consistent testing
3. pytest-asyncio is configured for async test support
4. Integration test directory structure separates SDK tests from unit tests
5. Conftest.py provides reusable fixtures for Ollama client and test server
6. Test documentation explains how to run integration tests
7. **NEW**: GitHub Actions workflow:
   - Runs in isolated container environment
   - Installs dependencies directly (no venv needed)
   - Executes all tests and linting
8. **NEW**: Code coverage reporting configured with 80% threshold

### Definition of Done
- [ ] Can run `pytest` locally from within venv and all tests pass
- [ ] Test fixtures are reusable across test files
- [ ] CI pipeline runs tests successfully in isolated environment
- [ ] Local development test instructions specify venv usage

## Story 1.7: Ollama SDK Compatibility Test Suite

**As an** Ollama SDK user,  
**I want to** verify that client.list() works exactly as expected,  
**So that** I know the proxy maintains full compatibility.

### Technical Notes
- Test against official Ollama Python SDK
- Verify exact response format matching
- Test error scenarios comprehensively

### Acceptance Criteria
1. Integration test uses official Ollama SDK to call client.list()
2. Test verifies that models are returned in the expected format
3. Test confirms model names, timestamps, and sizes are present
4. Test handles empty model list scenario
5. Test verifies error handling when backend is unavailable
6. Test passes with real Ollama SDK (not mocked HTTP calls)
7. **NEW**: Performance test confirms <100ms overhead vs direct call
8. **NEW**: Compatibility test runs against multiple Ollama SDK versions

### Definition of Done
- [ ] Official Ollama SDK successfully lists models through proxy
- [ ] All response fields match Ollama's expectations
- [ ] Error scenarios handled gracefully

## Epic Completion Criteria

### Technical Deliverables
- [ ] Working proxy service with /api/tags endpoint
- [ ] Docker-based development environment
- [ ] Comprehensive test suite with SDK compatibility tests
- [ ] Configuration management system
- [ ] Basic CI/CD pipeline ready

### Business Value Delivered
- [ ] Users can list OpenAI models using Ollama SDK
- [ ] Core translation architecture is proven
- [ ] Project risk is minimized by proving concept early

### Performance Metrics
- [ ] Response time overhead: <100ms
- [ ] Test coverage: >80%
- [ ] All tests passing in CI

## Dependencies and Risks

### Dependencies
- OpenAI API key (provided by user)
- Python 3.12+ environment
- Docker for containerization

### Identified Risks
1. **OpenAI API changes**: Mitigated by using official SDK
2. **Ollama format changes**: Mitigated by comprehensive SDK testing
3. **Performance overhead**: Mitigated by early performance testing

## Technical Decisions Log
1. **FastAPI over Flask**: Chosen for native async support and automatic OpenAPI docs
2. **Pydantic for validation**: Type safety and automatic validation
3. **Official SDKs**: Using both Ollama and OpenAI official SDKs for reliability

## Notes for Development Team
- Start with Story 1.1 and complete sequentially
- For local development, always work within activated virtual environment:
  ```bash
  python -m venv venv
  source venv/bin/activate  # Linux/Mac
  # or
  venv\Scripts\activate  # Windows
  pip install -r requirements-dev.txt
  ```
- Each story should have a PR with tests
- Run all tests and linting locally from within venv before committing
- CI/CD will run tests in isolated environments without venv
- Update README with venv setup instructions for local development
- Never install packages globally on your development machine

---

*Epic 1 ensures we have a solid foundation and proves the core concept before building additional features.*