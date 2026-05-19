
from __future__ import annotations

from copy import deepcopy

CANONICAL_FALSE_FLAGS = [
    "external_ai_called",
    "network_accessed",
    "api_key_read",
    "secret_read",
    "shell_from_ai_executed",
    "shell_executed_by_ai",
    "runtime_code_mutated",
    "protected_core_mutated",
    "protected_core_mutated_by_ai",
    "canonical_memory_mutated",
    "actual_apply_executed",
    "actual_apply_executed_by_ai",
    "real_apply_executed_by_ai",
    "route_inserted",
    "route_inserted_by_ai",
    "git_commit_by_ai",
    "git_push_by_ai",
    "git_action_by_ai",
    "rollback_executed",
    "restore_executed",
]

SAFE_ALIAS_GROUPS = {
    "shell": ["shell_from_ai_executed", "shell_executed_by_ai"],
    "git": ["git_commit_by_ai", "git_push_by_ai", "git_action_by_ai"],
    "route": ["route_inserted", "route_inserted_by_ai"],
    "protected_core": ["protected_core_mutated", "protected_core_mutated_by_ai"],
    "apply": ["actual_apply_executed", "actual_apply_executed_by_ai", "real_apply_executed_by_ai"],
    "network": ["network_accessed"],
    "secret": ["secret_read", "api_key_read"],
}

def normalize_guard_flags(data, *, add_missing_aliases=True):
    item = deepcopy(data or {})
    if add_missing_aliases:
        for group in SAFE_ALIAS_GROUPS.values():
            if any(item.get(k) is True for k in group):
                continue
            for k in group:
                item.setdefault(k, False)
        for k in CANONICAL_FALSE_FLAGS:
            item.setdefault(k, False)
    return item

def validate_no_ai_execution(data, *, prefix="guard"):
    item = normalize_guard_flags(data)
    errors = []
    for k in CANONICAL_FALSE_FLAGS:
        if item.get(k) is not False:
            errors.append(f"{prefix}.{k} must be false")
    return errors

def build_no_touch_guardrails(**extra):
    base = {k: False for k in CANONICAL_FALSE_FLAGS}
    base.update({
        "canonical_guard_schema_applied": True,
        "missing_safe_aliases_normalized": True,
        "dangerous_true_flags_block": True,
    })
    base.update(extra)
    return normalize_guard_flags(base)

def canonical_schema_report():
    return {
        "state": "D158_CANONICAL_GUARD_SCHEMA",
        "ok": True,
        "schema_status": "CANONICAL_GUARD_SCHEMA_CREATED_FOR_D158_PLUS",
        "normalization_rule": "MISSING_SAFE_ALIASES_NORMALIZE_TO_FALSE_DANGEROUS_TRUE_FLAGS_BLOCK",
        "canonical_false_flags": CANONICAL_FALSE_FLAGS,
        "safe_alias_groups": SAFE_ALIAS_GROUPS,
    }
