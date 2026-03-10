# Claude Code Hooks

A plugin marketplace for [Claude Code](https://github.com/anthropics/claude-code) hooks — security, observability, and session memory.

## Installation

```bash
/plugin install MOlechowski/claude-hooks
```

Then enable individual plugins:

```bash
/plugin enable hook-security
/plugin enable hook-observability
/plugin enable hook-session-memory
```

## Plugins

### hook-security

Blocks dangerous CLI commands before execution.

| Hook Event | Matcher | Action                                        |
|------------|---------|-----------------------------------------------|
| PreToolUse | `Bash`  | Block commands matching `BLOCKED_TOOLS` rules |

Ships with no default rules. Edit `BLOCKED_TOOLS` in `plugins/hook-security/hooks/scripts/pre_tool_use.py` to add your own blocking patterns (`git`, `rm`, `sudo`, `docker`, etc.).

### hook-observability

Logs all tool usage, results, notifications, and session events.

| Hook Event   | Script                | Log File                                    |
|--------------|-----------------------|---------------------------------------------|
| PreToolUse   | `log_tool_use.py`     | `tool-usage.jsonl`, `command-history.jsonl` |
| PostToolUse  | `log_tool_result.py`  | `post_tool_use.jsonl`                       |
| Notification | `log_notification.py` | `notifications.jsonl`                       |
| Stop         | `log_session_end.py`  | `sessions.jsonl`                            |
| SubagentStop | `log_subagent_end.py` | `subagents.jsonl`                           |

### hook-session-memory

Preserves session context across `/compact` by logging activity and structuring notes at compaction time.

| Hook Event       | Script            | Action                                                             |
|------------------|-------------------|--------------------------------------------------------------------|
| SessionStart     | `init.py`         | Create per-session log file                                        |
| UserPromptSubmit | `log_prompt.py`   | Append user messages (max 2000 chars)                              |
| PostToolUse      | `log_tool.py`     | Append tool summaries with smart truncation                        |
| PreCompact       | `pre_compact.py`  | Structure notes via `claude -p` / API / raw fallback (60s timeout) |

**Structured note sections:** Task specification, Files and Functions, Workflow, Errors & Corrections, Codebase and System Documentation, Learnings, Key results, Current State.

## Log Locations

| Plugin              | Directory                        |
|---------------------|----------------------------------|
| hook-security       | `~/.claude/logs/security/`       |
| hook-observability  | `~/.claude/logs/observability/`  |
| hook-session-memory | `~/.claude/logs/session-memory/` |

## Local Testing

```bash
# Test individual plugins
claude --plugin-dir ./plugins/hook-security
claude --plugin-dir ./plugins/hook-observability
claude --plugin-dir ./plugins/hook-session-memory

# Test all plugins together
claude --plugin-dir ./plugins/hook-security --plugin-dir ./plugins/hook-observability --plugin-dir ./plugins/hook-session-memory
```

## Requirements

- Python 3.10+
- Claude Code CLI

## Known Limitations

- `pre_compact.py` requires `claude` CLI on PATH for structured notes; silently skips if unavailable

## License

MIT
