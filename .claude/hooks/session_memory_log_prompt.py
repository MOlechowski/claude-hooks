#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# ///
"""UserPromptSubmit hook: log user messages to session memory"""

import os
import sys
from datetime import datetime

from hook_utils import parse_hook_input, MEMORY_DIR
MAX_PROMPT_LENGTH = 2000


def main():
    hook_input = parse_hook_input()
    session_id = hook_input.get("session_id", "")

    if not session_id:
        sys.exit(0)

    log_file = os.path.join(MEMORY_DIR, f"{session_id}.md")
    if not os.path.isfile(log_file):
        sys.exit(0)

    user_prompt = hook_input.get("user_prompt", "")
    if not user_prompt:
        sys.exit(0)

    if len(user_prompt) > MAX_PROMPT_LENGTH:
        user_prompt = user_prompt[:MAX_PROMPT_LENGTH] + "... [truncated]"

    timestamp = datetime.now().strftime("%H:%M:%S")

    with open(log_file, "a") as f:
        f.write(f"## User [{timestamp}]\n{user_prompt}\n\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
