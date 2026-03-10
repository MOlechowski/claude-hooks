#!/usr/bin/env python3
"""Notification hook: log Claude Code notifications"""

import json
import os
import sys
from datetime import datetime

# === LOG DIRECTORY ===
LOGS_DIR = os.path.join(os.path.expanduser("~"), ".claude", "logs", "observability")


def parse_hook_input():
    """Parse JSON input from stdin"""
    try:
        return json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        print("Error: Invalid JSON input", file=sys.stderr)
        sys.exit(1)


def log(event_type, data, filename):
    """Append a JSONL entry to the specified log file"""
    os.makedirs(LOGS_DIR, exist_ok=True)
    entry = {"timestamp": datetime.now().isoformat(), "event_type": event_type}
    if data:
        entry.update(data)
    with open(os.path.join(LOGS_DIR, f"{filename}.jsonl"), "a") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    hook_input = parse_hook_input()

    notification_type = hook_input.get("notification_type", "unknown")
    message = hook_input.get("message", "")
    session_id = hook_input.get("session_id", "")

    try:
        log("notification", {
            "notification_type": notification_type,
            "message": message,
            "session_id": session_id,
        }, "notifications")
    except OSError:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
