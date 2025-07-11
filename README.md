# Claude Code Hooks Collection

A collection of hooks for [Claude Code](https://github.com/anthropics/claude-code) to enhance security, logging, and control.

## Features

- **Security**: Block dangerous commands (e.g., `git --no-verify`)
- **Logging**: Track all tool usage and bash commands

## Requirements

- [UV](https://github.com/astral-sh/uv) - Fast Python package manager
  ```bash
  # Install with Homebrew (macOS/Linux)
  brew install uv
  
  # Or install with curl
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

## Installation

1. Clone this repository
2. Copy the entire `.claude` directory to your home directory:
   ```bash
   cp -r .claude ~/.claude
   ```
   Or if you already have hooks, just copy the hooks directory:
   ```bash
   cp -r .claude/hooks/* ~/.claude/hooks/
   ```
3. The `settings.json` file includes all hook registrations. If you already have a `~/.claude/settings.json`, merge the hooks configuration.

## Available Hooks

### pre_tool_use.py
- Logs all tool usage to `tool-usage.json` with structured data
- Logs bash commands to `command-history.json` with session tracking
- Blocks `git commit --no-verify` and `git commit -n` commands with LLM-friendly explanations
- Logs security blocks to `security.json` with detailed context

### post_tool_use.py
- Logs tool execution results to `post_tool_use.json`
- Tracks tool success/failure status with session context

### notification.py
- Logs all Claude Code notifications to `notifications.json`
- Captures permission requests and other notifications with structured data

### stop.py
- Logs session end events to `sessions.json`
- Prints session summary to console
- **Note**: Only triggers when Claude Code session ends

### subagent_stop.py
- Logs subagent completion events to `subagents.json`
- Tracks subagent lifecycle with session context
- **Note**: Only triggers when subagents (Task tool) complete

## Usage

Once installed, hooks run automatically. Check logs in your project's `.claude/logs/` directory:
- `tool-usage.json` - All tools used by Claude with structured data
- `command-history.json` - All bash commands executed with session tracking
- `security.json` - Blocked dangerous commands with detailed context
- `post_tool_use.json` - Tool execution results and success/failure status
- `notifications.json` - Claude notifications and permission requests
- `sessions.json` - Session lifecycle events
- `subagents.json` - Subagent (Task tool) events

## Configuration Examples

The `pre_tool_use.py` hook uses a `BLOCKED_TOOLS` configuration to block dangerous commands. You can extend it by adding more rules:

```python
BLOCKED_TOOLS = {
    "Bash": {
        # Block all git commit --no-verify commands
        "git": {
            "commit": {
                "flags": ["--no-verify", "-n"],
                "message": (
                    "Cannot execute: git commit with --no-verify flag bypasses "
                    "pre-commit hooks and may introduce issues. Consider running "
                    "without --no-verify to ensure code quality checks pass."
                )
            }
        },
        
        # Example: Block dangerous rm commands
        "rm": {
            "patterns": [
                ["-rf", "/"],
                ["-fr", "/"],
                ["/*"]
            ],
            "message": (
                "Cannot execute: recursive force removal of root directory would "
                "delete entire filesystem. This operation is irreversible and would "
                "destroy the system."
            )
        },
        
        # Example: Block all sudo commands
        "sudo": {
            "*": {
                "message": (
                    "Cannot execute: elevated privileges not permitted in this "
                    "environment. Operations requiring sudo access must be performed "
                    "through authorized channels."
                )
            }
        },
        
        # Example: Block specific docker commands
        "docker": {
            "rm": {
                "flags": ["-f", "--force"],
                "message": (
                    "Cannot execute: force removal of docker containers may cause "
                    "data loss. Please stop containers gracefully before removal."
                )
            }
        }
    }
}
```

### Configuration Structure

- **Program level**: First key is the command (e.g., "git", "rm", "sudo")
- **Subcommand level**: Second key is the subcommand (e.g., "commit" for git)
- **Wildcard**: Use "*" to block all usage of a command
- **Flags**: List of flags that trigger blocking
- **Patterns**: List of token combinations that must all be present
- **Message**: LLM-friendly explanation of why the command is blocked

### Writing LLM-Friendly Messages

Good blocking messages should:
1. Start with "Cannot execute:" to clearly indicate the action is blocked
2. Explain WHY the command is dangerous
3. Suggest safer alternatives when possible
4. Be specific about potential consequences

Examples:
- ✅ "Cannot execute: git commit with --no-verify flag bypasses pre-commit hooks and may introduce issues. Consider running without --no-verify to ensure code quality checks pass."
- ❌ "Git --no-verify blocked"

## Contributing

Feel free to submit PRs with new hooks or improvements!

## License

MIT
