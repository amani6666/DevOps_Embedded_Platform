"""JSON parsing utilities with robust markdown code-block extraction."""

import json
import re
from typing import Any

from src.agent2.exceptions import JsonParseError


def extract_json_from_markdown(raw_text: str) -> dict[str, Any]:
    """Extract and parse JSON from an LLM response."""
    if not raw_text or not raw_text.strip():
        raise JsonParseError("Received empty response from LLM")

    cleaned = raw_text.strip()

    json_match = re.search(r"`(?:json)?\s*([\s\S]*?)\s*`", cleaned)
    if json_match:
        cleaned = json_match.group(1).strip()
    else:
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start:end + 1]

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise JsonParseError(
            f"Failed to parse JSON. Raw text (first 500 chars): {raw_text[:500]}"
        ) from exc


def validate_agent2_output(data: dict[str, Any]) -> None:
    """Validate Agent 2 output conforms to the Agent 3 interface contract."""
    required_fields = {
        "build_strategy": str,
        "ota_active": bool,
        "monitoring": bool,
        "mqtt_broker": str,
        "justification": str,
    }

    missing = [field for field in required_fields if field not in data]
    if missing:
        raise JsonParseError(f"Missing required fields: {missing}")

    for field, expected_type in required_fields.items():
        if not isinstance(data[field], expected_type):
            raise JsonParseError(
                f"Field '{field}' must be {expected_type.__name__}, "
                f"got {type(data[field]).__name__}"
            )

    valid_strategies = {"docker_west_build", "native_west_build", "platformio_build"}
    if data["build_strategy"] not in valid_strategies:
        raise JsonParseError(
            f"Invalid build_strategy '{data['build_strategy']}'. "
            f"Must be one of: {valid_strategies}"
        )
