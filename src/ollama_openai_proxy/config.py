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