# Environment Strategy Summary

## Architecture Decision Record: Virtual Environments

### Context

The Ollama-OpenAI Proxy project requires clear environment management strategies to balance developer productivity, CI/CD efficiency, and production simplicity.

### Decision

We adopt a **context-specific environment strategy**:

1. **Local Development**: Mandatory use of Python virtual environments (venv)
2. **CI/CD**: Direct dependency installation in isolated containers
3. **Production**: Docker containers without virtual environments

### Rationale

#### Local Development (venv Required)

**Benefits:**
- Isolation from system Python packages
- Reproducible development environments
- Protection against dependency conflicts
- Easy environment reset (`rm -rf venv && python -m venv venv`)

**Implementation:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements-dev.txt
```

#### CI/CD (No venv)

**Benefits:**
- Faster execution (no venv creation overhead)
- Simpler GitHub Actions configuration
- Each run gets a fresh container
- Natural isolation through containerization

**Implementation:**
```yaml
- name: Install dependencies
  run: pip install -r requirements-dev.txt
- name: Run tests
  run: pytest
```

#### Production (No venv)

**Benefits:**
- Smaller Docker images
- Reduced attack surface
- Container provides complete isolation
- Aligns with container best practices

**Implementation:**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "-m", "ollama_openai_proxy"]
```

### Consequences

**Positive:**
- Clear, documented strategy for each environment
- Optimized for each context's needs
- Reduced complexity in CI/CD and production
- Better developer experience locally

**Negative:**
- Developers must remember to activate venv
- Slight difference between local and CI environments

**Mitigation:**
- Pre-commit hooks check for venv activation
- Clear documentation and setup scripts
- IDE configurations to auto-activate venv

## Quick Reference

| Question | Answer |
|----------|--------|
| Setting up local dev? | Use venv |
| Running tests locally? | From activated venv |
| Configuring CI? | No venv needed |
| Building Docker image? | No venv in Dockerfile |
| Installing new package? | In activated venv, then update requirements.txt |

## Enforcement

### Pre-commit Hook (`.pre-commit-config.yaml`)

```yaml
repos:
  - repo: local
    hooks:
      - id: check-venv
        name: Check virtual environment
        entry: python -c "import sys; exit(0 if 'venv' in sys.executable else 1)"
        language: system
        pass_filenames: false
        description: Ensure running in virtual environment
```

### IDE Configuration

**VS Code (`settings.json`):**
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.terminal.activateEnvironment": true
}
```

**PyCharm:**
- Project Settings → Python Interpreter → Add Local Interpreter → Existing Environment
- Select: `<project>/venv/bin/python`

## Migration Guide

### For Existing Developers

1. Delete any global project packages:
   ```bash
   pip uninstall -r requirements.txt -y
   ```

2. Create fresh venv:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements-dev.txt
   ```

3. Update IDE settings to use venv interpreter

### For New Developers

Follow the setup instructions in [Development Environment](./development-environment.md).

## Validation

To verify correct setup:

```bash
# Check you're in venv (locally)
which python
# Should show: /path/to/project/venv/bin/python

# Check no venv in CI
# GitHub Actions will show: /opt/hostedtoolcache/Python/3.12.x/x64/bin/python

# Check Docker doesn't have venv
docker run --rm ollama-openai-proxy which python
# Should show: /usr/local/bin/python
```

## References

- [PEP 405 - Python Virtual Environments](https://www.python.org/dev/peps/pep-0405/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [GitHub Actions Container Jobs](https://docs.github.com/en/actions/using-jobs/running-jobs-in-a-container)