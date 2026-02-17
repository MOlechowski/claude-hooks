#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# ///
"""PreCompact hook: structure accumulated session log via claude -p, inject into compaction"""

import os
import shutil
import subprocess
import sys

from hook_utils import parse_hook_input

MEMORY_DIR = os.path.join(os.path.expanduser("~"), ".claude", "session-memory")
MAX_LOG_CHARS = 30000
MIN_LOG_LINES = 5
RAW_FALLBACK_CHARS = 5000

STRUCTURING_PROMPT = """Structure this raw session activity log into organized technical notes \
for preserving context across a conversation compaction. Use this exact template — fill in \
each section with relevant details from the log. Be specific: include file paths, function \
names, commands, error messages. Skip sections with no relevant data. Keep total output under \
4000 tokens.

# Task specification
_What is the user working on? Design decisions and context._

# Files and Functions
_Important files referenced or modified. What do they contain?_

# Workflow
_Commands run and their purpose. How to interpret output._

# Errors & Corrections
_Errors encountered and how they were fixed. Failed approaches._

# Codebase and System Documentation
_Important system components discovered. How they work._

# Learnings
_What worked well, what did not, what to avoid._

# Key results
_Specific outputs the user requested: answers, tables, data._

# Current State
_What was being worked on most recently. Next steps._

Here is the raw session log:

"""


def find_claude_binary():
    """Find the claude CLI binary"""
    path = shutil.which("claude")
    if path:
        return path
    fallback = os.path.expanduser("~/.npm-global/bin/claude")
    if os.path.isfile(fallback) and os.access(fallback, os.X_OK):
        return fallback
    return None


def try_claude_cli(prompt):
    """Try structuring via claude -p (uses existing subscription)"""
    claude_bin = find_claude_binary()
    if not claude_bin:
        return None

    env = os.environ.copy()
    env["CLAUDECODE"] = ""  # bypass nesting guard

    try:
        result = subprocess.run(
            [
                claude_bin, "-p",
                "--model", "opus",
                "--no-session-persistence",
                "--dangerously-skip-permissions",
                "--tools", "",
            ],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=50,
            env=env,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        pass

    return None


def try_api_call(prompt):
    """Try structuring via direct API call (requires ANTHROPIC_API_KEY)"""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None

    import json

    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    })

    try:
        result = subprocess.run(
            [
                "curl", "-s", "--max-time", "45",
                "-H", f"x-api-key: {api_key}",
                "-H", "anthropic-version: 2023-06-01",
                "-H", "content-type: application/json",
                "https://api.anthropic.com/v1/messages",
                "-d", payload,
            ],
            capture_output=True,
            text=True,
            timeout=50,
        )
        if result.returncode == 0:
            resp = json.loads(result.stdout)
            text = resp.get("content", [{}])[0].get("text", "")
            if text:
                return text
    except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError, (KeyError, IndexError)):
        pass

    return None


def main():
    hook_input = parse_hook_input()
    session_id = hook_input.get("session_id", "")

    if not session_id:
        sys.exit(0)

    log_file = os.path.join(MEMORY_DIR, f"{session_id}.md")
    if not os.path.isfile(log_file):
        sys.exit(0)

    with open(log_file) as f:
        log_content = f.read()

    # Skip if log is effectively empty
    if len(log_content.splitlines()) < MIN_LOG_LINES:
        sys.exit(0)

    # Truncate from beginning if too large (keep recent context)
    if len(log_content) > MAX_LOG_CHARS:
        log_content = "[... earlier entries truncated ...]\n\n" + log_content[-MAX_LOG_CHARS:]

    prompt = STRUCTURING_PROMPT + log_content

    # Try methods in order: claude -p → API key → raw fallback
    structured = try_claude_cli(prompt)
    if not structured:
        structured = try_api_call(prompt)

    if structured:
        print(
            "IMPORTANT: Use the following structured session notes to preserve context "
            "during compaction. These notes capture the key details from the session "
            "that should be retained in the summary:\n"
        )
        print(structured)
    else:
        # Fallback: inject raw log
        print(
            "Use the following session activity log to preserve important context "
            "during compaction:\n"
        )
        print(log_content[-RAW_FALLBACK_CHARS:])

    sys.exit(0)


if __name__ == "__main__":
    main()
