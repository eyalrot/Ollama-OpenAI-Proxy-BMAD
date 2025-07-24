# Code Style and Conventions

## Python Standards
- **Version:** Python 3.12
- **Line Length:** 120 characters (configured in pyproject.toml)
- **Type Hints:** Required - `disallow_untyped_defs = true` in mypy config
- **Linting:** ruff with rules: E, F, I, N, W, B, RUF

## Code Quality Tools
- **Linter:** ruff 0.1.14 (fast, comprehensive Python linter)
- **Type Checker:** mypy 1.8.0 with strict settings
- **Pre-commit Hooks:** Automated code quality checks

## Project Structure
- **Source Code:** `src/ollama_openai_proxy/` (namespace package)
- **Tests:** `tests/` directory with unit and integration tests
- **Configuration:** `pyproject.toml` for project metadata and tool configs

## Import Organization
- Standard library imports first
- Third-party imports second  
- Local application imports last
- Enforced by ruff import sorting (I rule)