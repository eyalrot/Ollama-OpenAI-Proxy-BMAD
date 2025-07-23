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