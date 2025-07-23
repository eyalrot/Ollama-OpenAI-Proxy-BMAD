# Story 1.2: Configuration Management

**Story Points**: 2  
**Priority**: P0 (Required before client setup)  
**Type**: Feature  
**Dependencies**: Story 1.1 must be complete

## Story Summary
**As a** developer,  
**I want to** implement environment-based configuration management,  
**So that** the service can be easily configured for different deployments.

## Technical Implementation Guide

### Pre-Implementation Checklist
- [ ] Story 1.1 complete (project structure in place)
- [ ] Virtual environment activated
- [ ] Pydantic-settings installed via requirements.txt

### Implementation Steps

#### Step 1: Create Configuration Module
**src/ollama_openai_proxy/config.py**:
```python
"""Configuration management for Ollama-OpenAI Proxy."""
import os
from functools import lru_cache
from typing import Optional

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # OpenAI Configuration
    openai_api_key: SecretStr = Field(
        ...,
        description="OpenAI API key for authentication"
    )
    openai_api_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="Base URL for OpenAI API"
    )
    
    # Proxy Configuration
    proxy_port: int = Field(
        default=11434,
        description="Port for the proxy service",
        ge=1,
        le=65535
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    # Request Configuration
    request_timeout: int = Field(
        default=300,
        description="Request timeout in seconds",
        ge=1
    )
    
    # Application Info
    app_name: str = Field(
        default="Ollama-OpenAI Proxy",
        description="Application name"
    )
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper
    
    @field_validator("openai_api_base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Ensure base URL is properly formatted."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("Base URL must start with http:// or https://")
        # Remove trailing slash for consistency
        return v.rstrip("/")
    
    def get_openai_api_key(self) -> str:
        """Get the OpenAI API key value."""
        return self.openai_api_key.get_secret_value()


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    This function is cached to ensure we only create one Settings
    instance for the entire application lifecycle.
    
    Returns:
        Settings: The application settings
    
    Raises:
        ValidationError: If required settings are missing or invalid
    """
    try:
        settings = Settings()
        return settings
    except Exception as e:
        # Provide helpful error message for missing API key
        if "openai_api_key" in str(e):
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Please set it in your .env file or environment:\n"
                "export OPENAI_API_KEY=your-api-key-here"
            ) from e
        raise


# Create a settings instance that can be imported
# This will fail fast if configuration is invalid
try:
    settings = get_settings()
except Exception:
    # During imports (like tests), we might not have env vars set
    # The actual app will call get_settings() explicitly
    settings = None  # type: ignore
```

#### Step 2: Create Custom Exceptions
**src/ollama_openai_proxy/exceptions.py**:
```python
"""Custom exceptions for Ollama-OpenAI Proxy."""


class ProxyException(Exception):
    """Base exception for all proxy errors."""
    pass


class ConfigurationError(ProxyException):
    """Raised when configuration is invalid or missing."""
    pass


class OpenAIError(ProxyException):
    """Raised when OpenAI API returns an error."""
    pass
```

#### Step 3: Update Main Application
Update **src/ollama_openai_proxy/main.py**:
```python
"""Main entry point for Ollama-OpenAI Proxy Service."""
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from .config import get_settings
from .exceptions import ConfigurationError

# Will be configured after settings are loaded
logger = logging.getLogger(__name__)

__version__ = "0.1.0"


def configure_logging(log_level: str) -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    try:
        # Load and validate settings
        settings = get_settings()
        
        # Configure logging with the specified level
        configure_logging(settings.log_level)
        
        # Log startup information
        logger.info(
            "Starting Ollama-OpenAI Proxy Service",
            extra={
                "version": __version__,
                "port": settings.proxy_port,
                "log_level": settings.log_level,
                "openai_base_url": settings.openai_api_base_url
            }
        )
        
        # Store settings in app state for access in routes
        app.state.settings = settings
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise ConfigurationError(f"Application startup failed: {e}") from e
    finally:
        logger.info("Shutting down Ollama-OpenAI Proxy Service")


# Create FastAPI app
app = FastAPI(
    title="Ollama-OpenAI Proxy",
    description="OpenAI-compatible proxy for Ollama API",
    version=__version__,
    lifespan=lifespan
)


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    try:
        # Verify we can access settings
        settings = app.state.settings
        
        return JSONResponse(
            content={
                "status": "healthy",
                "version": __version__,
                "configured": True,
                "port": settings.proxy_port
            }
        )
    except Exception:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "version": __version__,
                "configured": False,
                "error": "Configuration not loaded"
            }
        )


@app.get("/config/validate")
async def validate_config() -> JSONResponse:
    """Validate configuration (excludes sensitive data)."""
    try:
        settings = app.state.settings
        
        return JSONResponse(
            content={
                "status": "valid",
                "config": {
                    "openai_api_base_url": settings.openai_api_base_url,
                    "proxy_port": settings.proxy_port,
                    "log_level": settings.log_level,
                    "request_timeout": settings.request_timeout,
                    "api_key_configured": bool(settings.openai_api_key)
                }
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Configuration validation failed: {str(e)}"
        )


def main() -> None:
    """Run the application."""
    import uvicorn
    
    try:
        # Load settings to fail fast if configuration is invalid
        settings = get_settings()
        
        # Configure logging before starting the server
        configure_logging(settings.log_level)
        
        logger.info(f"Starting server on port {settings.proxy_port}")
        
        uvicorn.run(
            "ollama_openai_proxy.main:app",
            host="0.0.0.0",
            port=settings.proxy_port,
            reload=True,
            log_config=None  # Use our custom logging
        )
    except ConfigurationError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Failed to start application: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

#### Step 4: Create Tests for Configuration
**tests/unit/test_config.py**:
```python
"""Tests for configuration management."""
import os
import pytest
from pydantic import ValidationError

from ollama_openai_proxy.config import Settings, get_settings


class TestSettings:
    """Test Settings configuration."""
    
    def test_valid_configuration(self, monkeypatch):
        """Test configuration with all valid values."""
        # Set environment variables
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
        monkeypatch.setenv("OPENAI_API_BASE_URL", "https://api.test.com/v1")
        monkeypatch.setenv("PROXY_PORT", "8080")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("REQUEST_TIMEOUT", "600")
        
        # Clear LRU cache
        get_settings.cache_clear()
        
        settings = Settings()
        
        assert settings.get_openai_api_key() == "test-key-123"
        assert settings.openai_api_base_url == "https://api.test.com/v1"
        assert settings.proxy_port == 8080
        assert settings.log_level == "DEBUG"
        assert settings.request_timeout == 600
    
    def test_missing_api_key(self, monkeypatch):
        """Test that missing API key raises error."""
        # Remove API key if set
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        
        # Clear LRU cache
        get_settings.cache_clear()
        
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        assert "openai_api_key" in str(exc_info.value)
    
    def test_invalid_port(self, monkeypatch):
        """Test invalid port number."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("PROXY_PORT", "99999")
        
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        assert "proxy_port" in str(exc_info.value)
    
    def test_invalid_log_level(self, monkeypatch):
        """Test invalid log level."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("LOG_LEVEL", "INVALID")
        
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        assert "log_level" in str(exc_info.value)
    
    def test_base_url_formatting(self, monkeypatch):
        """Test base URL formatting."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        
        # Test trailing slash removal
        monkeypatch.setenv("OPENAI_API_BASE_URL", "https://api.test.com/v1/")
        settings = Settings()
        assert settings.openai_api_base_url == "https://api.test.com/v1"
        
        # Test invalid URL
        monkeypatch.setenv("OPENAI_API_BASE_URL", "not-a-url")
        with pytest.raises(ValidationError):
            Settings()
    
    def test_env_file_loading(self, tmp_path, monkeypatch):
        """Test loading from .env file."""
        # Create temporary .env file
        env_file = tmp_path / ".env"
        env_file.write_text("""
OPENAI_API_KEY=env-file-key
PROXY_PORT=9999
LOG_LEVEL=WARNING
""")
        
        # Change to temp directory
        monkeypatch.chdir(tmp_path)
        
        # Clear any existing env vars
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("PROXY_PORT", raising=False)
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        
        settings = Settings()
        
        assert settings.get_openai_api_key() == "env-file-key"
        assert settings.proxy_port == 9999
        assert settings.log_level == "WARNING"
    
    def test_get_settings_caching(self, monkeypatch):
        """Test that get_settings returns cached instance."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        
        # Clear cache
        get_settings.cache_clear()
        
        # Get settings twice
        settings1 = get_settings()
        settings2 = get_settings()
        
        # Should be the same instance
        assert settings1 is settings2
    
    def test_helpful_error_message(self, monkeypatch):
        """Test helpful error message for missing API key."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        
        # Clear cache
        get_settings.cache_clear()
        
        with pytest.raises(ValueError) as exc_info:
            get_settings()
        
        assert "OPENAI_API_KEY environment variable is required" in str(exc_info.value)


class TestConfigurationIntegration:
    """Test configuration integration with FastAPI app."""
    
    @pytest.mark.asyncio
    async def test_app_startup_with_valid_config(self, monkeypatch):
        """Test app starts with valid configuration."""
        from fastapi.testclient import TestClient
        
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        
        # Clear cache
        get_settings.cache_clear()
        
        # Import app after setting env vars
        from ollama_openai_proxy.main import app
        
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["configured"] is True
    
    @pytest.mark.asyncio
    async def test_config_validate_endpoint(self, monkeypatch):
        """Test configuration validation endpoint."""
        from fastapi.testclient import TestClient
        
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        
        # Clear cache
        get_settings.cache_clear()
        
        from ollama_openai_proxy.main import app
        
        with TestClient(app) as client:
            response = client.get("/config/validate")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "valid"
            assert data["config"]["log_level"] == "DEBUG"
            assert data["config"]["api_key_configured"] is True
            # Should not expose actual API key
            assert "openai_api_key" not in data["config"]
```

#### Step 5: Create .env for Local Development
Create a `.env` file (not committed) for local testing:
```bash
# Development environment configuration
OPENAI_API_KEY=your-actual-api-key-here
LOG_LEVEL=DEBUG
```

#### Step 6: Update Docker Files for Configuration
Update **docker/docker-compose.yml**:
```yaml
version: '3.8'

services:
  proxy:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    ports:
      - "${PROXY_PORT:-11434}:${PROXY_PORT:-11434}"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_API_BASE_URL=${OPENAI_API_BASE_URL:-https://api.openai.com/v1}
      - PROXY_PORT=${PROXY_PORT:-11434}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - REQUEST_TIMEOUT=${REQUEST_TIMEOUT:-300}
    volumes:
      - ../src:/app/src  # Hot reload for development
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:${PROXY_PORT:-11434}/health"]
      interval: 30s
      timeout: 3s
      retries: 3
```

### Verification Steps

1. **Test configuration loading:**
   ```bash
   # From activated venv
   python -c "from ollama_openai_proxy.config import get_settings; print(get_settings())"
   ```

2. **Test missing API key error:**
   ```bash
   # Temporarily remove API key
   unset OPENAI_API_KEY
   python -m ollama_openai_proxy
   # Should show helpful error message
   ```

3. **Test with valid configuration:**
   ```bash
   # Set API key
   export OPENAI_API_KEY=test-key
   python -m ollama_openai_proxy
   
   # In another terminal:
   curl http://localhost:11434/health
   curl http://localhost:11434/config/validate
   ```

4. **Run configuration tests:**
   ```bash
   pytest tests/unit/test_config.py -v
   ```

5. **Test Docker with configuration:**
   ```bash
   cd docker
   docker-compose up --build
   ```

### Definition of Done Checklist

- [ ] Configuration module created with Pydantic settings
- [ ] All required settings have validation
- [ ] Settings load from environment variables
- [ ] Settings load from .env file
- [ ] Missing API key shows helpful error message
- [ ] Application fails fast with invalid configuration
- [ ] Health check endpoint shows configuration status
- [ ] Config validation endpoint works (no sensitive data exposed)
- [ ] Unit tests pass with 100% coverage of config module
- [ ] Docker-compose properly passes environment variables
- [ ] Logging configured based on LOG_LEVEL setting

### Common Issues & Solutions

1. **Import errors:**
   - Ensure you're in the activated venv
   - Run `pip install -e .` to install package in development mode

2. **Settings not loading:**
   - Check .env file is in the project root
   - Verify environment variable names match exactly

3. **Validation errors:**
   - Check error messages for specific fields
   - Ensure all required fields are provided

### Integration Notes

- The `app.state.settings` makes configuration available to all routes
- Use dependency injection in future stories for cleaner access
- Settings are cached for performance
- Configuration validation happens at startup

### Next Steps

After completing this story:
1. Ensure all tests pass
2. Commit changes
3. Create PR for review
4. Move to Story 1.3: OpenAI SDK Client Wrapper