"""Agent 2 (Architect) — Core decision engine.

Consumes project analysis from Agent 1 and produces structured
architecture decisions via LLM reasoning. All outputs conform
to a strict JSON contract for downstream Agent 3 consumption.
"""

import json
import os
from typing import Any

from anthropic import Anthropic

from src.agent2.config import AgentConfig
from src.agent2.exceptions import Agent2Error, FileOperationError
from src.utils.json_utils import extract_json_from_markdown, validate_agent2_output


class ArchitectAgent:
    """AI-driven architecture decision engine for embedded DevOps."""

    SYSTEM_PROMPT: str = (
        "You are an expert embedded systems architect. "
        "Analyze embedded project metadata and decide the optimal build strategy, "
        "OTA policy, monitoring setup, and MQTT broker configuration. "
        "Respond ONLY in valid JSON."
    )

    OUTPUT_SCHEMA: dict[str, Any] = {
        "build_strategy": "docker_west_build | native_west_build | platformio_build",
        "ota_active": "boolean",
        "monitoring": "boolean",
        "mqtt_broker": "string",
        "justification": "string (max 200 chars)",
    }

    def __init__(self, config: AgentConfig, mock_mode: bool = False) -> None:
        self._config = config
        self._mock_mode = mock_mode
        if not mock_mode:
            self._client = Anthropic(api_key=config.api_key)

    def analyze(self, project_analysis: dict[str, Any]) -> dict[str, Any]:
        """Execute the architecture decision pipeline."""
        if self._mock_mode:
            return self._generate_mock_decision(project_analysis)

        prompt = self._build_prompt(project_analysis)

        try:
            response = self._client.messages.create(
                model=self._config.model,
                max_tokens=self._config.max_tokens,
                temperature=self._config.temperature,
                system=self.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:
            raise Agent2Error(f"LLM API call failed: {exc}") from exc

        raw_text = response.content[0].text
        decision = extract_json_from_markdown(raw_text)
        validate_agent2_output(decision)

        return decision

    def _generate_mock_decision(self, analysis: dict[str, Any]) -> dict[str, Any]:
        """Generate a deterministic mock decision based on project analysis."""
        framework = analysis.get("framework", "").lower()
        protocols = [p.lower() for p in analysis.get("protocols", [])]
        board = analysis.get("target_board", "").lower()

        decision = {
            "build_strategy": "docker_west_build",
            "ota_active": False,
            "monitoring": False,
            "mqtt_broker": "none",
            "justification": "Default mock decision for testing",
        }

        if "zephyr" in framework:
            decision["build_strategy"] = "docker_west_build"
            decision["justification"] = "Zephyr RTOS detected, Docker west build recommended"

        if any(p in protocols for p in ["mqtt", "wifi"]):
            decision["monitoring"] = True
            decision["mqtt_broker"] = "mosquitto"
            decision["justification"] += "; MQTT/WiFi detected, monitoring enabled"

        if "esp32" in board:
            decision["ota_active"] = True
            decision["justification"] += "; ESP32 has sufficient flash for OTA"

        return decision

    def _build_prompt(self, analysis: dict[str, Any]) -> str:
        return (
            f"Analyze this embedded project and decide the technical strategy:\n\n"
            f"{json.dumps(analysis, indent=2, ensure_ascii=False)}\n\n"
            f"Respond ONLY in JSON using this exact schema:\n"
            f"{json.dumps(self.OUTPUT_SCHEMA, indent=2)}\n\n"
            f"Rules:\n"
            f"- Zephyr RTOS + ESP32 -> docker_west_build\n"
            f"- MQTT + WiFi detected -> monitoring=true, mqtt_broker='mosquitto'\n"
            f"- OTA only if flash > 4MB\n"
            f"- Keep justification under 200 characters"
        )

    def load_analysis(self, file_path: str) -> dict[str, Any]:
        """Load and validate Agent 1 output from disk."""
        if not os.path.exists(file_path):
            raise FileOperationError(f"Input file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError as exc:
            raise FileOperationError(f"Invalid JSON in {file_path}: {exc}") from exc
        except OSError as exc:
            raise FileOperationError(f"Cannot read {file_path}: {exc}") from exc

    def save_decision(self, decision: dict[str, Any], file_path: str) -> None:
        """Persist architecture decision to disk for Agent 3."""
        try:
            with open(file_path, "w", encoding="utf-8") as handle:
                json.dump(decision, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
        except OSError as exc:
            raise FileOperationError(f"Cannot write {file_path}: {exc}") from exc