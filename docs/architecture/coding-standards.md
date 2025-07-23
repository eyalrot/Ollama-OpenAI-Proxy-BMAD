# Coding Standards

## Core Standards

- **Languages & Runtimes:** Python 3.12
- **Style & Linting:** ruff with default configuration
- **Test Organization:** tests/{unit,integration}/test_*.py

## Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Functions | snake_case | translate_request |
| Classes | PascalCase | OllamaGenerateRequest |
| Constants | UPPER_SNAKE_CASE | DEFAULT_TIMEOUT |
| Modules | snake_case | openai_client.py |

## Critical Rules

- **Async All The Way:** All route handlers and service methods must be async
- **Type Everything:** All functions must have type hints for parameters and returns
- **No Direct OpenAI Calls:** Always use the OpenAI SDK wrapper service
- **Error Context:** All errors must include request context for debugging
- **No Hardcoded URLs:** All external URLs must come from configuration
- **Python 3.12 Features:** Use new features like improved error messages and f-string debugging
