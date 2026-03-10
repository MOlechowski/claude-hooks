#!/usr/bin/env python3
"""PreToolUse hook: block dangerous CLI commands via configurable rules.json."""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Allow imports from the scripts directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.config_loader import load_rules  # noqa: E402
from core.rule_engine import RuleEngine  # noqa: E402

LOGS_DIR = os.path.join(os.path.expanduser("~"), ".claude", "logs", "security")
RULES_PATH = Path(__file__).resolve().parent.parent.parent / "rules.json"


def parse_hook_input():
    """Parse JSON input from stdin."""
    try:
        return json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        print("hook-security: invalid JSON input", file=sys.stderr)
        sys.exit(1)


def log(event_type, data=None):
    """Append a JSONL entry to security.jsonl."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    entry = {"timestamp": datetime.now().isoformat(), "event_type": event_type}
    if data:
        entry.update(data)
    with open(os.path.join(LOGS_DIR, "security.jsonl"), "a") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    hook_input = parse_hook_input()

    rules = load_rules(RULES_PATH, event="bash")

    if rules is None:
        # Missing file → allow (no rules = nothing to block)
        # Malformed file → error already printed to stderr
        sys.exit(0) if not RULES_PATH.is_file() else sys.exit(1)

    if not rules:
        sys.exit(0)

    engine = RuleEngine()
    result = engine.evaluate_rules(rules, hook_input)

    if not result:
        sys.exit(0)

    session_id = hook_input.get("session_id", "")
    command = hook_input.get("tool_input", {}).get("command", "")

    # Determine if this is a block or warn
    is_block = "hookSpecificOutput" in result

    try:
        log(
            "security_block" if is_block else "security_warn",
            {
                "session_id": session_id,
                "command": command,
                "action": "blocked" if is_block else "warned",
                "message": result.get("systemMessage", ""),
            },
        )
    except OSError:
        pass

    # Output structured response for Claude Code hooks protocol
    print(json.dumps(result))

    if is_block:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
