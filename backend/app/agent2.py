"""Agent 2 — Architecte infrastructure.

Consomme la sortie de Agent 1 (Sahar) et produit la décision
d'architecture attendue par Agent 3 (Nour).
"""

from __future__ import annotations

import json
import os
from typing import Any

from pydantic import BaseModel, Field, field_validator


class Agent1Input(BaseModel):
    """Contrat d'entrée figé (sortie Agent 1)."""
    framework: str
    fichiers_detectes: list[str] = Field(default_factory=list)
    carte_cible: str = "unknown"
    protocoles: list[str] = Field(default_factory=list)


class Agent2Output(BaseModel):
    """Contrat de sortie figé (entrée Agent 3 / Nour)."""
    strategie_build: str
    ota_active: bool
    monitoring: bool
    broker_mqtt: str
    justification: str

    @field_validator("strategie_build")
    @classmethod
    def validate_strategy(cls, v: str) -> str:
        allowed = {"docker_west_build", "native_west_build", "platformio_build"}
        if v not in allowed:
            raise ValueError(f"strategie_build must be one of {allowed}")
        return v


def decide_architecture(analysis: dict[str, Any]) -> dict[str, Any]:
    """Règles déterministes + mock-mode (pas de LLM obligatoire)."""
    data = Agent1Input(**analysis)

    framework = data.framework.lower()
    protocols = [p.lower() for p in data.protocoles]
    board = data.carte_cible.lower()

    decision = Agent2Output(
        strategie_build="docker_west_build",
        ota_active=False,
        monitoring=False,
        broker_mqtt="none",
        justification="Décision par défaut",
    )

    if "zephyr" in framework:
        decision.strategie_build = "docker_west_build"
        decision.justification = "Zephyr RTOS détecté → build isolé via Docker/west"

    if any(p in protocols for p in ("mqtt", "wifi")):
        decision.monitoring = True
        decision.broker_mqtt = "mosquitto"
        decision.justification += " ; MQTT/WiFi → monitoring + Mosquitto"

    if "esp32" in board:
        decision.ota_active = True
        decision.justification += " ; ESP32 → OTA possible (flash ≥ 4 Mo)"

    # Limite cahier des charges
    if len(decision.justification) > 200:
        decision.justification = decision.justification[:197] + "..."

    return decision.model_dump()


# Point d'entrée FastAPI (Sahar pourra l'ajouter facilement)
def run_agent2(agent1_payload: dict[str, Any]) -> dict[str, Any]:
    return decide_architecture(agent1_payload)