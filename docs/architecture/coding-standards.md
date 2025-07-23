# Coding Standards

## Core Standards

- **Languages & Runtimes:** Python 3.12
- **Style & Linting:** ruff with default configuration
- **Test Organization:** tests/{unit,integration}/test_*.py
- **Development Environment:** Virtual environments (venv) required for local development
- **CI/CD Environment:** Containerized execution without venv

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
- **Virtual Environment Usage:** All local development MUST use venv for dependency isolation
- **No Global Package Installation:** Never install packages globally on development machines

## Development Environment Setup

### Local Development Requirements

1. **Create Virtual Environment:**
   ```bash
   python -m venv venv
   ```

2. **Activate Virtual Environment:**
   - Linux/Mac: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate`

3. **Install Dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Verify Setup:**
   ```bash
   which python  # Should show path within venv
   python --version  # Should show Python 3.12+
   ```

### Pre-commit Hooks

- Install pre-commit hooks from within venv: `pre-commit install`
- Hooks will run automatically on git commit
- Manual run: `pre-commit run --all-files`

### CI/CD Environment

- GitHub Actions runs in isolated containers
- Dependencies installed directly without venv
- Each run gets a fresh environment
- No persistent state between runs
