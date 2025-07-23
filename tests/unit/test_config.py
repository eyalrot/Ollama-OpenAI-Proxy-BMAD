"""Tests for configuration management."""
from typing import Any

import pytest
from ollama_openai_proxy.config import Settings, get_settings
from pydantic import ValidationError


class TestSettings:
    """Test Settings configuration."""

    def test_valid_configuration(self, monkeypatch: Any) -> None:
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

    def test_missing_api_key(self, monkeypatch: Any) -> None:
        """Test that missing API key raises error."""
        # Remove API key if set
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        # Clear LRU cache
        get_settings.cache_clear()

        # Create Settings without loading from .env file
        with pytest.raises(ValidationError) as exc_info:
            Settings(_env_file=None)

        assert "openai_api_key" in str(exc_info.value)

    def test_invalid_port(self, monkeypatch: Any) -> None:
        """Test invalid port number."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("PROXY_PORT", "99999")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "proxy_port" in str(exc_info.value)

    def test_invalid_log_level(self, monkeypatch: Any) -> None:
        """Test invalid log level."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("LOG_LEVEL", "INVALID")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "log_level" in str(exc_info.value)

    def test_base_url_formatting(self, monkeypatch: Any) -> None:
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

    def test_env_file_loading(self, tmp_path: Any, monkeypatch: Any) -> None:
        """Test loading from .env file."""
        # Create temporary .env file
        env_file = tmp_path / ".env"
        env_file.write_text(
            """
OPENAI_API_KEY=env-file-key
PROXY_PORT=9999
LOG_LEVEL=WARNING
"""
        )

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

    def test_get_settings_caching(self, monkeypatch: Any) -> None:
        """Test that get_settings returns cached instance."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        # Clear cache
        get_settings.cache_clear()

        # Get settings twice
        settings1 = get_settings()
        settings2 = get_settings()

        # Should be the same instance
        assert settings1 is settings2

    def test_helpful_error_message(self, monkeypatch: Any, tmp_path: Any) -> None:
        """Test helpful error message for missing API key."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        # Change to a directory without .env file
        monkeypatch.chdir(tmp_path)

        # Clear cache
        get_settings.cache_clear()

        with pytest.raises(ValueError) as exc_info:
            get_settings()

        assert "OPENAI_API_KEY environment variable is required" in str(exc_info.value)


class TestConfigurationIntegration:
    """Test configuration integration with FastAPI app."""

    def test_app_startup_with_valid_config(self, monkeypatch: Any) -> None:
        """Test app starts with valid configuration."""
        # Import at module level
        from ollama_openai_proxy.config import get_settings

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        # Clear cache
        get_settings.cache_clear()

        # Test that settings can be loaded
        settings = get_settings()
        assert settings.openai_api_key.get_secret_value() == "test-key"
        assert settings.proxy_port == 11434

    def test_config_validate_endpoint(self, monkeypatch: Any) -> None:
        """Test configuration validation endpoint."""
        # Import at module level
        from ollama_openai_proxy.config import get_settings

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")

        # Clear cache
        get_settings.cache_clear()

        # Test settings with custom values
        settings = get_settings()
        assert settings.log_level == "DEBUG"
        assert settings.openai_api_key.get_secret_value() == "test-key"
