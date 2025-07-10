#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# ///
"""Subagent stop hook to log when subagents finish"""

import sys
from hook_utils import parse_hook_input, log

# === MAIN ===
def main():
    hook_input = parse_hook_input()
    
    session_id = hook_input.get('session_id', 'unknown')
    subagent_id = hook_input.get('subagent_id', 'unknown')
    transcript_path = hook_input.get('transcript_path', '')
    
    log("subagent_end", f"Subagent ended: {subagent_id} (session: {session_id})", {
        "session_id": session_id,
        "subagent_id": subagent_id,
        "event": "subagent_ended",
        "transcript_path": transcript_path,
    }, "subagents")
    
    sys.exit(0)

if __name__ == "__main__":
    main()