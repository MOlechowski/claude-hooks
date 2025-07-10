#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# ///
"""Common utilities for Claude Code hooks"""

import json
import os
import sys
from datetime import datetime

LOGS_DIR = os.path.expanduser('~/.claude/logs')

def parse_hook_input():
    """Parse JSON input from stdin"""
    try:
        return json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        print("Error: Invalid JSON input", file=sys.stderr)
        sys.exit(1)

def log(event_type, message=None, data=None, base_filename="hook"):
    """
    Simple unified logging function that logs to both text and JSON
    
    Args:
        event_type: Type of event (e.g., "tool_blocked", "session_end", "notification")
        message: Human-readable message for text log (optional)
        data: Dictionary of structured data for JSON log (optional)
        base_filename: Base name for log files (will create .log and .json versions)
    """
    os.makedirs(LOGS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Log to text file if message provided
    if message:
        log_entry = f"[{timestamp}] {event_type}: {message}\n"
        with open(os.path.join(LOGS_DIR, f"{base_filename}.log"), 'a') as f:
            f.write(log_entry)
    
    # Log to JSON file
    json_entry = {
        "timestamp": timestamp,
        "event_type": event_type,
    }
    
    # Add any additional data
    if data:
        json_entry.update(data)
    
    # Add message to JSON if no other data provided
    if message and not data:
        json_entry["message"] = message
    
    # Read existing JSON log
    json_path = os.path.join(LOGS_DIR, f"{base_filename}.json")
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            try:
                log_data = json.load(f)
            except (json.JSONDecodeError, ValueError):
                log_data = []
    else:
        log_data = []
    
    log_data.append(json_entry)
    
    # Write updated JSON log
    with open(json_path, 'w') as f:
        json.dump(log_data, f, indent=2)