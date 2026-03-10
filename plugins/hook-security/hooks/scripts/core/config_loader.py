"""Configuration loader for hook-security plugin.

Loads and validates rules from rules.json.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


VALID_OPERATORS = frozenset({
    "regex_match",
    "contains",
    "equals",
    "not_contains",
    "starts_with",
    "ends_with",
})

VALID_ACTIONS = frozenset({"block", "warn"})

REQUIRED_RULE_FIELDS = ("id", "action", "message", "conditions")


@dataclass
class Condition:
    """A single condition for matching."""

    field: str
    operator: str
    pattern: str

    @classmethod
    def from_dict(cls, data: dict) -> Condition:
        return cls(
            field=data.get("field", ""),
            operator=data.get("operator", "regex_match"),
            pattern=data.get("pattern", ""),
        )


@dataclass
class Rule:
    """A security rule loaded from rules.json."""

    id: str
    action: str
    message: str
    conditions: list[Condition] = field(default_factory=list)
    name: str = ""
    enabled: bool = True
    event: str = "all"

    @classmethod
    def from_dict(cls, data: dict) -> Rule:
        conditions = [Condition.from_dict(c) for c in data.get("conditions", [])]
        return cls(
            id=data["id"],
            action=data["action"],
            message=data["message"],
            conditions=conditions,
            name=data.get("name", ""),
            enabled=data.get("enabled", True),
            event=data.get("event", "all"),
        )


def validate_rule(rule_dict: dict, index: int) -> bool:
    """Validate a rule dict has required fields and valid values.

    Returns True if valid, False with stderr warning if not.
    """
    for f in REQUIRED_RULE_FIELDS:
        if f not in rule_dict:
            print(
                f"hook-security: rule[{index}] missing required field '{f}', skipping",
                file=sys.stderr,
            )
            return False

    if rule_dict["action"] not in VALID_ACTIONS:
        print(
            f"hook-security: rule '{rule_dict['id']}' has invalid action "
            f"'{rule_dict['action']}', skipping",
            file=sys.stderr,
        )
        return False

    conditions = rule_dict.get("conditions", [])
    if not isinstance(conditions, list) or len(conditions) == 0:
        print(
            f"hook-security: rule '{rule_dict['id']}' has no conditions, skipping",
            file=sys.stderr,
        )
        return False

    for i, cond in enumerate(conditions):
        if not isinstance(cond, dict):
            print(
                f"hook-security: rule '{rule_dict['id']}' condition[{i}] "
                f"is not an object, skipping rule",
                file=sys.stderr,
            )
            return False
        if "field" not in cond or "pattern" not in cond:
            print(
                f"hook-security: rule '{rule_dict['id']}' condition[{i}] "
                f"missing 'field' or 'pattern', skipping rule",
                file=sys.stderr,
            )
            return False
        operator = cond.get("operator", "regex_match")
        if operator not in VALID_OPERATORS:
            print(
                f"hook-security: rule '{rule_dict['id']}' condition[{i}] "
                f"has unknown operator '{operator}', skipping rule",
                file=sys.stderr,
            )
            return False

    return True


def load_rules(
    rules_path: Path, event: Optional[str] = None
) -> Optional[list[Rule]]:
    """Load rules from rules.json.

    Args:
        rules_path: Path to rules.json file.
        event: Optional event filter (e.g. "bash"). Only rules matching
               this event or "all" are returned.

    Returns:
        List of enabled Rule objects, or None if file is missing/malformed.
    """
    if not rules_path.is_file():
        print(
            f"hook-security: rules file not found at {rules_path}",
            file=sys.stderr,
        )
        return None

    try:
        with open(rules_path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"hook-security: failed to load rules: {exc}", file=sys.stderr)
        return None

    if not isinstance(data, dict) or "rules" not in data:
        print(
            "hook-security: rules.json missing 'rules' key",
            file=sys.stderr,
        )
        return None

    raw_rules = data["rules"]
    if not isinstance(raw_rules, list):
        print(
            "hook-security: 'rules' must be an array",
            file=sys.stderr,
        )
        return None

    rules: list[Rule] = []
    for i, rule_dict in enumerate(raw_rules):
        if not isinstance(rule_dict, dict):
            print(
                f"hook-security: rule[{i}] is not an object, skipping",
                file=sys.stderr,
            )
            continue

        if not validate_rule(rule_dict, i):
            continue

        rule = Rule.from_dict(rule_dict)

        if not rule.enabled:
            continue

        if event and rule.event != "all" and rule.event != event:
            continue

        rules.append(rule)

    return rules
