#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# ///
"""Notification hook to log Claude Code notifications"""

import sys
from hook_utils import parse_hook_input, log

# === MAIN ===
def main():
    hook_input = parse_hook_input()
    
    notification_type = hook_input.get('notification_type', 'unknown')
    message = hook_input.get('message', '')
    session_id = hook_input.get('session_id', '')
    
    log("notification", {
        "notification_type": notification_type,
        "message": message,
        "session_id": session_id
    }, "notifications")
    
    sys.exit(0)

if __name__ == "__main__":
    main()