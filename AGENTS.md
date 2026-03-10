---
last_validated: 2026-03-10T21:47:23Z
---

# Claude Code Hooks

A plugin marketplace for Claude Code hooks providing security, observability, session memory, and rule reinforcement.

## Repository Overview

This repository contains 4 self-contained Claude Code hook plugins distributed via the plugin marketplace. Each plugin lives under `plugins/` with its own `hooks.json` and Python scripts.

**Language:** Python 3.10+
**Tooling:** mise (tool versions), Taskfile (task runner), lefthook (git hooks)
**CI:** GitHub Actions — lint on push/PR to master

## Repository Structure

```text
.
├── .claude-plugin/
│   └── marketplace.json          # Marketplace manifest — lists all 4 plugins
├── .github/workflows/
│   └── lint.yml                  # CI: lint + commit-lint jobs
├── lefthook/                     # Git hook configs (split by concern)
│   ├── commits.yml               # Conventional commit enforcement
│   ├── files.yml                 # File size/type checks
│   ├── lint.yml                  # Pre-commit lint runner
│   ├── python.yml                # Python-specific checks
│   └── secrets.yml               # Gitleaks secret scanning
├── plugins/
│   ├── hook-observability/       # Logs all tool usage, results, notifications, sessions
│   │   ├── .claude-plugin/plugin.json
│   │   └── hooks/
│   │       ├── hooks.json
│   │       └── scripts/
│   │           ├── log_notification.py
│   │           ├── log_session_end.py
│   │           ├── log_subagent_end.py
│   │           ├── log_tool_result.py
│   │           └── log_tool_use.py
│   ├── hook-security/            # Blocks dangerous CLI commands
│   │   ├── .claude-plugin/plugin.json
│   │   └── hooks/
│   │       ├── hooks.json
│   │       └── scripts/
│   │           └── pre_tool_use.py
│   ├── hook-rule-reinforcement/  # Reinforces CLAUDE.md/AGENTS.md rules per prompt
│   │   ├── .claude-plugin/plugin.json
│   │   └── hooks/
│   │       ├── hooks.json
│   │       └── scripts/
│   │           └── reinforce_rules.py  # UserPromptSubmit: distill & inject relevant rules
│   └── hook-session-memory/      # Preserves context across /compact
│       ├── .claude-plugin/plugin.json
│       └── hooks/
│           ├── hooks.json
│           └── scripts/
│               ├── init.py           # SessionStart: create per-session log
│               ├── log_prompt.py     # UserPromptSubmit: log user messages
│               ├── log_tool.py       # PostToolUse: log tool summaries
│               └── pre_compact.py    # PreCompact: structure notes via claude -p
├── taskfiles/                    # Taskfile includes
│   ├── ci.yml                    # CI-specific tasks
│   ├── lint.yml                  # Linter tasks (ruff, json, actionlint, yamllint, markdownlint)
│   └── setup.yml                 # Setup tasks (mise install, lefthook install)
├── .mise.toml                    # Tool versions: ruff, task, actionlint, cocogitto, gitleaks, etc.
├── lefthook.yml                  # Lefthook entry point — extends lefthook/*.yml
├── Taskfile.yml                  # Taskfile entry point — includes taskfiles/*.yml
└── README.md
```

## Development Guidelines

### Plugin Structure

Each plugin follows the same layout:

```text
plugins/<name>/
├── .claude-plugin/
│   └── plugin.json       # Plugin metadata (name, description, category, version)
└── hooks/
    ├── hooks.json        # Hook event bindings (matcher → command)
    └── scripts/
        └── *.py          # Hook implementation scripts
```

- `hooks.json` maps hook events (PreToolUse, PostToolUse, etc.) to Python scripts
- Scripts receive JSON on stdin (`tool_input`, `session_id`, etc.) and exit with code 0 (allow), 1 (error), or 2 (block)
- All log output goes to `~/.claude/logs/<plugin-name>/` as JSONL files

### Naming Conventions

- Plugin directories: `hook-<domain>` (e.g., `hook-security`, `hook-observability`)
- Script files: `<action>_<subject>.py` (e.g., `log_tool_use.py`, `pre_tool_use.py`)
- Log files: `<subject>.jsonl` (e.g., `security.jsonl`, `tool-usage.jsonl`)

### Linting

```bash
task lint          # Run all linters
task lint:python   # Ruff only
task lint:json     # JSON validation
task lint:yamllint # YAML lint
```

### Setup

```bash
task setup         # Install tools (mise) and git hooks (lefthook)
```

### Testing Plugins Locally

```bash
claude --plugin-dir ./plugins/hook-security
claude --plugin-dir ./plugins/hook-observability
claude --plugin-dir ./plugins/hook-session-memory
claude --plugin-dir ./plugins/hook-rule-reinforcement
```

## Git Workflow

- **Branch:** feature branches off master
- **Commits:** conventional commits enforced by cocogitto (via lefthook pre-commit and CI)
- **CI:** `lint.yml` runs `task lint` on push/PR; commit-lint on PRs only
- **Merge:** PRs to master
