#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# ///
"""PostToolUse hook: log tool usage to session memory with smart truncation"""

import json
import os
import sys
from datetime import datetime

from hook_utils import parse_hook_input, MEMORY_DIR


def truncate(text, max_chars):
    """Truncate text to max_chars"""
    if not text:
        return ""
    text = str(text)
    if len(text) > max_chars:
        return text[:max_chars] + "..."
    return text


def first_lines(text, n=5):
    """Return first n lines of text"""
    if not text:
        return ""
    lines = str(text).splitlines()
    return "\n".join(lines[:n])


def safe_str(value):
    """Convert value to string safely"""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value)


def build_summary(tool_name, tool_input, tool_response):
    """Build concise summary based on tool type"""
    inp = tool_input or {}
    resp = safe_str(tool_response)

    if tool_name == "Read":
        return f"Read: {inp.get('file_path', '?')}"

    if tool_name == "Write":
        return f"Write: {inp.get('file_path', '?')}"

    if tool_name == "Edit":
        path = inp.get("file_path", "?")
        old = truncate(inp.get("old_string", ""), 100)
        new = truncate(inp.get("new_string", ""), 100)
        return f"Edit: {path}\n  old: {old}\n  new: {new}"

    if tool_name == "Bash":
        cmd = inp.get("command", "?")
        output = truncate(resp, 200)
        return f"Bash: {cmd}\n  output: {output}"

    if tool_name == "Grep":
        pattern = inp.get("pattern", "?")
        path = inp.get("path", ".")
        results = first_lines(resp, 5)
        return f"Grep: '{pattern}' in {path}\n  {results}"

    if tool_name == "Glob":
        pattern = inp.get("pattern", "?")
        results = first_lines(resp, 5)
        return f"Glob: {pattern}\n  {results}"

    if tool_name == "WebSearch":
        return f"WebSearch: {inp.get('query', '?')}"

    if tool_name == "WebFetch":
        return f"WebFetch: {inp.get('url', '?')}"

    if tool_name == "Task":
        return f"Task: {inp.get('description', '?')}"

    # Default: tool name + truncated input
    return f"{tool_name}: {truncate(safe_str(inp), 200)}"


def main():
    hook_input = parse_hook_input()
    session_id = hook_input.get("session_id", "")

    if not session_id:
        sys.exit(0)

    log_file = os.path.join(MEMORY_DIR, f"{session_id}.md")
    if not os.path.isfile(log_file):
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "unknown")
    tool_input = hook_input.get("tool_input", {})
    tool_response = hook_input.get("tool_response", "")

    summary = build_summary(tool_name, tool_input, tool_response)
    timestamp = datetime.now().strftime("%H:%M:%S")

    with open(log_file, "a") as f:
        f.write(f"## Tool: {tool_name} [{timestamp}]\n{summary}\n\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
