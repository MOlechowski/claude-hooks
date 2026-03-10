#!/usr/bin/env python3
"""PreToolUse hook: block dangerous CLI commands and log security events"""

import json
import os
import shlex
import sys
from datetime import datetime

# === LOG DIRECTORY ===
LOGS_DIR = os.path.join(os.path.expanduser("~"), ".claude", "logs", "security")

# === CONFIGURATION ===
# Add rules to block specific commands. Example:
#
# BLOCKED_TOOLS = {
#     "Bash": {
#         "git": {
#             "commit": {
#                 "flags": ["--no-verify", "-n"],
#                 "message": "Cannot execute: git commit with --no-verify bypasses pre-commit hooks."
#             }
#         }
#     }
# }
BLOCKED_TOOLS = {
    "Bash": {}
}


# === UTILITIES ===
def parse_hook_input():
    """Parse JSON input from stdin"""
    try:
        return json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        print("Error: Invalid JSON input", file=sys.stderr)
        sys.exit(1)


def log(event_type, data=None):
    """Append a JSONL entry to security.jsonl"""
    os.makedirs(LOGS_DIR, exist_ok=True)
    entry = {"timestamp": datetime.now().isoformat(), "event_type": event_type}
    if data:
        entry.update(data)
    with open(os.path.join(LOGS_DIR, "security.jsonl"), "a") as f:
        f.write(json.dumps(entry) + "\n")


# === CHECKING LOGIC ===
def check_bash_command(tokens):
    """Check Bash commands against rules. Returns (should_block, message)"""
    if not tokens:
        return False, ""

    program = tokens[0]
    program_rules = BLOCKED_TOOLS["Bash"].get(program, {})

    if len(tokens) > 1 and tokens[1] in program_rules:
        sub_rules = program_rules[tokens[1]]
        if any(flag in tokens for flag in sub_rules.get("flags", [])):
            return True, sub_rules.get("message", "")

    return False, ""


# === MAIN ===
def main():
    hook_input = parse_hook_input()

    tool_input = hook_input.get("tool_input", {})
    session_id = hook_input.get("session_id", "")
    cmd = tool_input.get("command", "")

    try:
        tokens = shlex.split(cmd) if cmd else []
    except ValueError:
        tokens = cmd.split() if cmd else []

    should_block, message = check_bash_command(tokens)

    if should_block:
        try:
            log("security_block", {
                "session_id": session_id,
                "command": cmd,
                "action": "blocked",
                "message": message,
            })
        except OSError:
            pass

        print(f"Command blocked: {message}", file=sys.stderr)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
