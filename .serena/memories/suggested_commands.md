# Suggested Commands

## Development Setup
```bash
# Create and activate virtual environment (REQUIRED for local dev)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

## Running the Application
```bash
# Run the proxy service
python -m ollama_openai_proxy

# Verify health
curl http://localhost:11434/health
```

## Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test types
pytest tests/unit -v
pytest tests/integration -v
```

## Code Quality
```bash
# Run linting
ruff check src/ tests/

# Run type checking  
mypy src/

# Check coverage threshold
coverage report --fail-under=60
```

## Docker Development
```bash
# Docker development
cd docker
docker-compose up --build

# Verify Docker health
curl http://localhost:11434/health
```

## Important Notes
- **Virtual environment is REQUIRED for local development**
- Always activate venv before working: `source venv/bin/activate`
- Deactivate when done: `deactivate`