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