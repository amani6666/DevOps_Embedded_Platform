"""Custom exceptions for Agent 2 (Architect) module."""


class Agent2Error(Exception):
    """Base exception for all Agent 2 errors."""
    pass


class ConfigurationError(Agent2Error):
    """Raised when required configuration is missing or invalid."""
    pass


class ApiKeyError(Agent2Error):
    """Raised when the Anthropic API key is missing or invalid."""
    pass


class JsonParseError(Agent2Error):
    """Raised when AI response cannot be parsed as valid JSON."""
    pass


class FileOperationError(Agent2Error):
    """Raised when file read/write operations fail."""
    pass
