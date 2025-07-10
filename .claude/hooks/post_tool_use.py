#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# ///
"""Post-tool use hook to log tool execution results"""

import sys
from hook_utils import parse_hook_input, log

# === MAIN ===
def main():
    hook_input = parse_hook_input()
    
    tool_name = hook_input.get('tool_name', 'unknown')
    success = hook_input.get('success', True)
    session_id = hook_input.get('session_id', '')
    
    status = "succeeded" if success else "failed"
    log("tool_result", f"Tool {tool_name} {status}", {
        "session_id": session_id,
        "tool_name": tool_name,
        "success": success,
    }, "post_tool_use")
    
    sys.exit(0)

if __name__ == "__main__":
    main()