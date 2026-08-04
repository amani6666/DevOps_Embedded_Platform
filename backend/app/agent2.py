#!/usr/bin/env python3
"""Agent 2 (Architect) — CLI Entrypoint."""

import os
import sys
import traceback

from src.agent2.architect import ArchitectAgent
from src.agent2.config import AgentConfig
from src.agent2.exceptions import Agent2Error


def main() -> int:
    """Execute the Agent 2 architecture decision pipeline."""
    try:
        config = AgentConfig()
        
        # Enable mock mode if ANTHROPIC_API_KEY is not set or AGENT2_MOCK=1
        mock_mode = (
            os.getenv("AGENT2_MOCK", "0") == "1"
            or not os.getenv("ANTHROPIC_API_KEY")
        )
        
        agent = ArchitectAgent(config, mock_mode=mock_mode)

        analysis = agent.load_analysis(config.input_file)
        decision = agent.analyze(analysis)
        agent.save_decision(decision, config.output_file)

        if mock_mode:
            print("[MOCK MODE] Decision generated without LLM call")
        
        return 0

    except Agent2Error as exc:
        print(f"[AGENT2 ERROR] {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"[FATAL] Unhandled exception: {exc}", file=sys.stderr)
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())