"""Custom exceptions for Ollama-OpenAI Proxy."""


class ProxyError(Exception):
    """Base exception for all proxy errors."""

    pass


class ConfigurationError(ProxyError):
    """Raised when configuration is invalid or missing."""

    pass


class OpenAIError(ProxyError):
    """Raised when OpenAI API returns an error."""

    pass
