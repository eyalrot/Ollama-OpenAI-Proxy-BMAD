# Codebase Structure

## Main Directories
- `src/ollama_openai_proxy/` - Main application source code
- `tests/` - Unit and integration tests
- `docs/` - Documentation including architecture docs
- `docker/` - Docker configuration files
- `.github/workflows/` - CI/CD workflows

## Source Code Organization
```
src/ollama_openai_proxy/
├── __init__.py
├── __main__.py          # Entry point for python -m
├── main.py              # FastAPI application setup
├── config.py            # Configuration management
├── exceptions.py        # Custom exceptions
├── models/              # Data models
├── services/            # Business logic services
├── routes/              # API route implementations
├── routers/             # Route organization (legacy)
└── utils/               # Utility functions
```

## Key Files
- `main.py` - FastAPI app with JSON logging setup
- `config.py` - Environment-based configuration
- `services/openai_service.py` - OpenAI API integration
- `services/translation_service.py` - API translation logic
- `routes/` - Individual API endpoint implementations

## Testing Structure
- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Integration tests requiring API calls
- Markers: `@pytest.mark.requires_api_key` for tests needing OpenAI API

## Documentation
- `docs/architecture/` - Comprehensive architecture documentation
- `docs/stories/` - User story specifications
- `docs/prd/` - Product requirements