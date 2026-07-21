#!/usr/bin/env python3
"""Agent 2 (Architect) — CLI Entrypoint."""

import sys
import traceback

from src.agent2.architect import ArchitectAgent
from src.agent2.config import AgentConfig
from src.agent2.exceptions import Agent2Error


def main() -> int:
    """Execute the Agent 2 architecture decision pipeline."""
    try:
        config = AgentConfig()
        agent = ArchitectAgent(config)

        analysis = agent.load_analysis(config.input_file)
        decision = agent.analyze(analysis)
        agent.save_decision(decision, config.output_file)

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
