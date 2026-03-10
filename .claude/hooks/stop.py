#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# ///
"""Stop hook to log when Claude Code session ends"""

import sys
from hook_utils import parse_hook_input, log, LOGS_DIR

# === MAIN ===
def main():
    hook_input = parse_hook_input()
    
    session_id = hook_input.get('session_id', 'unknown')
    transcript_path = hook_input.get('transcript_path', '')
    
    log("session_end", {
        "session_id": session_id,
        "event": "session_ended",
        "transcript_path": transcript_path
    }, "sessions")
    
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\nSession completed at {timestamp}", file=sys.stderr)
    print(f"Logs available at: {LOGS_DIR}", file=sys.stderr)
    
    sys.exit(0)

if __name__ == "__main__":
    main()