# Multi-stage Dockerfile for Ollama-OpenAI Proxy
# Optimized for development, CI/CD, and production environments

# Stage 1: Base - Common foundation for all stages
FROM python:3.12-slim as base

# Security updates and essential tools
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Create non-root user early for security
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

WORKDIR /app

# Switch to non-root user for pip installations
USER appuser

# Copy and install base requirements
# This layer is cached and reused across all stages
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Add user's pip bin to PATH
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Stage 2: Development - Hot reload and debugging tools
FROM base as dev

# Switch to root for development tool installation
USER root

# Install development dependencies
COPY --chown=appuser:appuser requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Install additional development tools
RUN pip install --no-cache-dir \
    debugpy \
    ipython \
    watchdog

# Development-specific configurations
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Switch back to non-root user
USER appuser

# Copy source code (will be overridden by volume mount in dev)
COPY --chown=appuser:appuser src/ ./src/

# Development command with hot reload support
CMD ["python", "-m", "uvicorn", "ollama_openai_proxy.main:app", "--host", "0.0.0.0", "--port", "11434", "--reload"]

# Stage 3: CI - Testing and quality assurance
FROM base as ci

# Install testing dependencies as appuser
COPY --chown=appuser:appuser requirements-dev.txt .
RUN pip install --no-cache-dir --user -r requirements-dev.txt

# Copy source code and test files
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser tests/ ./tests/
COPY --chown=appuser:appuser pyproject.toml pytest.ini ./

# Set environment for CI
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Default command runs tests with coverage
CMD ["pytest", "--cov=src", "--cov-report=xml", "--cov-report=term", "-v"]

# Stage 4: Production - Minimal runtime
FROM base as prod

# Copy only application source code
COPY --chown=appuser:appuser src/ ./src/

# Security hardening for production
USER root
# Remove unnecessary packages and files
RUN apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache && \
    rm -rf /tmp/* && \
    find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Set proper file permissions
RUN chmod -R 755 /app && \
    chown -R appuser:appuser /app

# Switch to non-root user for runtime
USER appuser

# Production environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONOPTIMIZE=1
ENV PYTHONPATH=/app/src

# Health check configuration
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:11434/health').read()"

# Expose application port
EXPOSE 11434

# Production command
CMD ["python", "-m", "ollama_openai_proxy.main"]