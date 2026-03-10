#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# ///
"""Common utilities for Claude Code hooks"""

import json
import os
import sys
from datetime import datetime

# Centralized log directory
LOGS_DIR = os.path.join(os.path.expanduser("~"), ".claude", "logs")

# Session memory directory (absolute path, shared by all session memory hooks)
MEMORY_DIR = os.path.join(os.path.expanduser("~"), ".claude", "session-memory")

def parse_hook_input():
    """Parse JSON input from stdin"""
    try:
        return json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        print("Error: Invalid JSON input", file=sys.stderr)
        sys.exit(1)

def log(event_type, data=None, base_filename="hook"):
    """
    Simple JSON logging function with pretty formatting
    
    Args:
        event_type: Type of event (e.g., "tool_blocked", "session_end", "notification")
        data: Dictionary of structured data for JSON log (optional)
        base_filename: Base name for log files (will create .json file)
    """
    os.makedirs(LOGS_DIR, exist_ok=True)
    timestamp = datetime.now().isoformat()
    
    # Create JSON entry
    json_entry = {
        "timestamp": timestamp,
        "event_type": event_type,
    }
    
    # Add any additional data
    if data:
        json_entry.update(data)
    
    # Append as JSONL (one JSON object per line)
    jsonl_path = os.path.join(LOGS_DIR, f"{base_filename}.jsonl")
    with open(jsonl_path, 'a') as f:
        f.write(json.dumps(json_entry) + '\n')