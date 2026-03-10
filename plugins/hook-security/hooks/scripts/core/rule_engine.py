"""Rule evaluation engine for hook-security plugin."""

from __future__ import annotations

import re
import sys
from functools import lru_cache
from typing import Any, Optional

from .config_loader import Rule


@lru_cache(maxsize=128)
def _compile_regex(pattern: str) -> re.Pattern[str]:
    """Compile regex pattern with caching."""
    return re.compile(pattern, re.IGNORECASE)


class RuleEngine:
    """Evaluates security rules against hook input data."""

    def evaluate_rules(
        self, rules: list[Rule], input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Evaluate all rules against input data.

        Returns a response dict for Claude Code hooks protocol.
        Empty dict means no rules matched (allow).
        """
        blocking: list[Rule] = []
        warning: list[Rule] = []

        for rule in rules:
            if not self._rule_matches(rule, input_data):
                continue
            if rule.action == "block":
                blocking.append(rule)
            else:
                warning.append(rule)

        if blocking:
            messages = [
                f"**[{r.id}]** {r.message}" for r in blocking
            ]
            combined = "\n\n".join(messages)
            return {
                "hookSpecificOutput": {"permissionDecision": "deny"},
                "systemMessage": combined,
            }

        if warning:
            messages = [
                f"**[{r.id}]** {r.message}" for r in warning
            ]
            return {"systemMessage": "\n\n".join(messages)}

        return {}

    def _rule_matches(
        self, rule: Rule, input_data: dict[str, Any]
    ) -> bool:
        """Check if a rule matches the input data.

        All conditions must match (AND logic).
        """
        if not rule.conditions:
            return False

        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        for condition in rule.conditions:
            value = self._extract_field(
                condition.field, tool_name, tool_input
            )
            if value is None:
                return False
            if not self._check_operator(
                condition.operator, condition.pattern, value
            ):
                return False

        return True

    def _extract_field(
        self,
        field_name: str,
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> Optional[str]:
        """Extract a field value from the hook input.

        Supports:
            command     — Bash command string
            file_path   — target file path
            content     — Write content or Edit new_string
            new_string  — Edit new_string
            old_string  — Edit old_string
            tool_name   — name of the tool being invoked
        """
        if field_name == "tool_name":
            return tool_name

        if field_name == "command":
            return tool_input.get("command", "")

        if field_name == "file_path":
            return tool_input.get("file_path", "")

        if field_name == "content":
            return (
                tool_input.get("content")
                or tool_input.get("new_string", "")
            )

        if field_name == "new_string":
            return tool_input.get("new_string", "")

        if field_name == "old_string":
            return tool_input.get("old_string", "")

        # Generic fallback: try direct lookup in tool_input
        value = tool_input.get(field_name)
        if value is not None:
            return str(value)

        return None

    def _check_operator(
        self, operator: str, pattern: str, value: str
    ) -> bool:
        """Apply an operator to check pattern against value."""
        if operator == "regex_match":
            return self._regex_match(pattern, value)
        if operator == "contains":
            return pattern in value
        if operator == "equals":
            return pattern == value
        if operator == "not_contains":
            return pattern not in value
        if operator == "starts_with":
            return value.startswith(pattern)
        if operator == "ends_with":
            return value.endswith(pattern)
        return False

    def _regex_match(self, pattern: str, text: str) -> bool:
        """Check if pattern matches text using cached compiled regex."""
        try:
            regex = _compile_regex(pattern)
            return bool(regex.search(text))
        except re.error as exc:
            print(
                f"hook-security: invalid regex '{pattern}': {exc}",
                file=sys.stderr,
            )
            return False
