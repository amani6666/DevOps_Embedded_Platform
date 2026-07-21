"""Configuration management for Agent 2 (Architect)."""

import os

from src.agent2.exceptions import ConfigurationError, ApiKeyError


class AgentConfig:
    """Immutable configuration container for Agent 2."""

    DEFAULT_MODEL: str = "claude-3-5-sonnet-20241022"
    DEFAULT_MAX_TOKENS: int = 500
    DEFAULT_TEMPERATURE: float = 0.0

    def __init__(self) -> None:
        self._api_key: str = self._resolve_api_key()
        self._model: str = os.getenv("ANTHROPIC_MODEL", self.DEFAULT_MODEL)
        self._max_tokens: int = self._parse_int(
            os.getenv("ANTHROPIC_MAX_TOKENS", str(self.DEFAULT_MAX_TOKENS)),
            "ANTHROPIC_MAX_TOKENS"
        )
        self._temperature: float = self._parse_float(
            os.getenv("ANTHROPIC_TEMPERATURE", str(self.DEFAULT_TEMPERATURE)),
            "ANTHROPIC_TEMPERATURE"
        )
        self._input_file: str = os.getenv("AGENT1_INPUT", "mock_agent1_output.json")
        self._output_file: str = os.getenv("AGENT2_OUTPUT", "mock_agent2_output.json")

    @property
    def api_key(self) -> str:
        return self._api_key

    @property
    def model(self) -> str:
        return self._model

    @property
    def max_tokens(self) -> int:
        return self._max_tokens

    @property
    def temperature(self) -> float:
        return self._temperature

    @property
    def input_file(self) -> str:
        return self._input_file

    @property
    def output_file(self) -> str:
        return self._output_file

    def _resolve_api_key(self) -> str:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ApiKeyError(
                "ANTHROPIC_API_KEY environment variable is required. "
                "Set it before running: $env:ANTHROPIC_API_KEY = 'your-key-here'"
            )
        return api_key

    def _parse_int(self, value: str, name: str) -> int:
        try:
            parsed = int(value)
            if parsed <= 0:
                raise ConfigurationError(f"{name} must be positive, got {parsed}")
            return parsed
        except ValueError as exc:
            raise ConfigurationError(f"{name} must be an integer, got '{value}'") from exc

    def _parse_float(self, value: str, name: str) -> float:
        try:
            parsed = float(value)
            if not 0.0 <= parsed <= 2.0:
                raise ConfigurationError(f"{name} must be between 0.0 and 2.0, got {parsed}")
            return parsed
        except ValueError as exc:
            raise ConfigurationError(f"{name} must be a float, got '{value}'") from exc
