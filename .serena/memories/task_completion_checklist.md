# Task Completion Checklist

## Before Submitting Changes
1. **Code Quality Checks**
   - Run `ruff check src/ tests/` (linting)
   - Run `mypy src/` (type checking)
   - Ensure all pre-commit hooks pass

2. **Testing Requirements**
   - Run `pytest` (all tests must pass)
   - Run `pytest --cov=src` (check coverage)
   - Verify coverage threshold: `coverage report --fail-under=60`
   - Test both unit tests (`tests/unit`) and integration tests (`tests/integration`)

3. **Application Testing**
   - Start the service: `python -m ollama_openai_proxy`
   - Verify health endpoint: `curl http://localhost:11434/health`
   - Test key functionality manually if applicable

4. **Docker Testing** (when relevant)
   - Build and test Docker setup: `cd docker && docker-compose up --build`
   - Verify Docker health check works

5. **Documentation Updates**
   - Update README.md if new features or commands added
   - Update relevant architecture docs if architectural changes made

## CI/CD Considerations
- All tests must pass in GitHub Actions
- Code coverage maintained above 60%
- Docker builds must succeed (when Docker changes made)
- Pre-commit hooks must pass