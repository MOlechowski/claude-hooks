#!/usr/bin/env python3
"""Stop hook: log session end events"""

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

    session_id = hook_input.get("session_id", "unknown")
    transcript_path = hook_input.get("transcript_path", "")

    try:
        log("session_end", {
            "session_id": session_id,
            "event": "session_ended",
            "transcript_path": transcript_path,
        }, "sessions")
    except OSError:
        pass

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\nSession completed at {timestamp}", file=sys.stderr)
    print(f"Logs available at: {LOGS_DIR}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
