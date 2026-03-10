#!/usr/bin/env python3
"""UserPromptSubmit hook: reinforce CLAUDE.md/AGENTS.md rules per prompt via claude -p"""

import hashlib
import json
import os
import shutil
import subprocess
import sys

LOG_DIR = os.path.join(os.path.expanduser("~"), ".claude", "logs", "rule-reinforcement")
MAX_INPUT_CHARS = 6000
STATIC_FALLBACK_LINES = 10

DISTILLATION_PROMPT = """\
You are a rule selector. Given a user's prompt and project instruction files,
select the 3-5 rules most relevant to what the user is about to do.

Rules about testing matter when the user asks to fix, add, or change code.
Rules about git/commits matter when the user asks to commit or push.
Rules about documentation matter when the user modifies public APIs.
Rules about code style always matter when writing code.

Output ONLY a compact numbered list of the selected rules. No explanations.
Keep under 200 tokens.

USER PROMPT:
{user_prompt}

PROJECT INSTRUCTIONS:
{combined_instructions}"""


def parse_hook_input():
    """Parse JSON input from stdin"""
    try:
        return json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        print("Error: Invalid JSON input", file=sys.stderr)
        sys.exit(1)


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
    """Invoke claude -p with haiku for fast rule distillation"""
    claude_bin = find_claude_binary()
    if not claude_bin:
        return None

    env = os.environ.copy()
    env.pop("CLAUDECODE", None)

    try:
        result = subprocess.run(
            [
                claude_bin, "-p",
                "--model", "haiku",
                "--no-session-persistence",
                "--dangerously-skip-permissions",
                "--tools", "",
            ],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=13,
            env=env,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        pass

    return None


def find_project_root():
    """Find git project root"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        pass
    return None


def discover_instruction_files():
    """Discover CLAUDE.md and AGENTS.md from project root and global config"""
    paths = []

    project_root = find_project_root()
    if project_root:
        for name in ("CLAUDE.md", "AGENTS.md"):
            path = os.path.join(project_root, name)
            if os.path.isfile(path):
                paths.append(path)

    global_claude = os.path.join(os.path.expanduser("~"), ".claude", "CLAUDE.md")
    if os.path.isfile(global_claude):
        paths.append(global_claude)

    return paths


def read_and_concatenate(paths):
    """Read instruction files, concatenate, and truncate to MAX_INPUT_CHARS"""
    parts = []
    for path in paths:
        try:
            with open(path) as f:
                content = f.read().strip()
            if content:
                parts.append(f"# Source: {os.path.basename(path)}\n{content}")
        except OSError:
            continue

    combined = "\n\n---\n\n".join(parts)
    if len(combined) > MAX_INPUT_CHARS:
        combined = combined[:MAX_INPUT_CHARS] + "\n[... truncated ...]"
    return combined


def get_content_hash(content):
    """Hash content for cache key"""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def get_cached_content(paths):
    """Check if source files have changed since last read; return cached content or None"""
    cache_file = os.path.join(LOG_DIR, "content_cache.json")
    if not os.path.isfile(cache_file):
        return None

    try:
        with open(cache_file) as f:
            cache = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    cached_mtimes = cache.get("mtimes", {})
    for path in paths:
        try:
            current_mtime = os.path.getmtime(path)
        except OSError:
            return None
        if cached_mtimes.get(path) != current_mtime:
            return None

    return cache.get("content")


def save_content_cache(paths, content):
    """Save concatenated content and mtimes to cache"""
    os.makedirs(LOG_DIR, exist_ok=True)
    mtimes = {}
    for path in paths:
        try:
            mtimes[path] = os.path.getmtime(path)
        except OSError:
            pass

    cache = {"mtimes": mtimes, "content": content}
    cache_file = os.path.join(LOG_DIR, "content_cache.json")
    try:
        with open(cache_file, "w") as f:
            json.dump(cache, f)
    except OSError:
        pass


def static_fallback(content):
    """Return first N lines as static fallback when claude CLI is unavailable"""
    lines = content.splitlines()
    return "\n".join(lines[:STATIC_FALLBACK_LINES])


def main():
    hook_input = parse_hook_input()
    user_prompt = hook_input.get("user_prompt", "")

    if not user_prompt:
        sys.exit(0)

    paths = discover_instruction_files()
    if not paths:
        sys.exit(0)

    combined = get_cached_content(paths)
    if combined is None:
        combined = read_and_concatenate(paths)
        save_content_cache(paths, combined)

    if not combined.strip():
        sys.exit(0)

    prompt = DISTILLATION_PROMPT.format(
        user_prompt=user_prompt,
        combined_instructions=combined,
    )

    distilled = try_claude_cli(prompt)

    if distilled:
        print(
            "IMPORTANT: The following project rules are relevant to your current task:\n"
        )
        print(distilled)
    else:
        fallback = static_fallback(combined)
        if fallback:
            print(
                "IMPORTANT: The following project rules are relevant to your current task:\n"
            )
            print(fallback)

    sys.exit(0)


if __name__ == "__main__":
    main()
