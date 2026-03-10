#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# ///
"""SessionStart hook: initialize session memory log file"""

import os
import sys
from datetime import datetime

from hook_utils import parse_hook_input, MEMORY_DIR


def main():
    hook_input = parse_hook_input()
    session_id = hook_input.get("session_id", "")

    if not session_id:
        sys.exit(0)

    os.makedirs(MEMORY_DIR, exist_ok=True)

    log_file = os.path.join(MEMORY_DIR, f"{session_id}.md")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cwd = os.getcwd()

    with open(log_file, "w") as f:
        f.write(f"# Session Log\nStarted: {now}\nWorking directory: {cwd}\n\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
