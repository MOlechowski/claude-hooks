#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# ///
"""Pre-tool use hook to validate and block dangerous operations"""

import sys
import shlex
from hook_utils import parse_hook_input, log

# === CONFIGURATION ===
BLOCKED_TOOLS = {
    "Bash": {
        "git": {
            "commit": {
                "flags": ["--no-verify", "-n"],
                "message": (
                    "Cannot execute: git commit with --no-verify flag bypasses "
                    "pre-commit hooks and may introduce issues. Consider running "
                    "without --no-verify to ensure code quality checks pass."
                )
            }
        }
    }
}

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
    
    tool_name = hook_input.get("tool_name", "unknown")
    tool_input = hook_input.get("tool_input", {})
    session_id = hook_input.get("session_id", "")
    
    log("tool_use", {
        "session_id": session_id,
        "tool_name": tool_name,
        "tool_input": tool_input
    }, "tool-usage")
    
    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        
        log("command", {
            "session_id": session_id,
            "command": cmd
        }, "command-history")
        
        try:
            tokens = shlex.split(cmd) if cmd else []
        except ValueError:
            # Malformed command, let Claude handle it
            tokens = cmd.split() if cmd else []
        
        should_block, message = check_bash_command(tokens)
        
        if should_block:
            log("security_block", {
                "session_id": session_id,
                "command": cmd,
                "action": "blocked",
                "message": message
            }, "security")
            
            print(f"Command blocked: {message}", file=sys.stderr)
            sys.exit(2)
    
    sys.exit(0)

if __name__ == "__main__":
    main()