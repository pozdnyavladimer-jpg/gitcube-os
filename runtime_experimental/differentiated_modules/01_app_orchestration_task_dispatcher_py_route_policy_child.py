from __future__ import annotations

from typing import Any, Dict


MODULE_STATE = "D75_DIFFERENTIATED_CHILD_MODULE"
SOURCE_NODE = 'app/orchestration/task_dispatcher.py'
GRADIENT_ROLE = 'route_policy_child'
GRADIENT_INTENT = 'separate routing pressure from core dispatcher'
PAIN_SCORE_AT_BIRTH = 0.8125

# This scaffold is intentionally sandbox-only.
PROTECTED_CORE_TOUCH_ALLOWED = False
CANONICAL_MEMORY_WRITE_ALLOWED = False
EXTERNAL_AI_CALL_ALLOWED = False
RUNTIME_APPLY_ALLOWED = False


def describe_module() -> Dict[str, Any]:
    return {
        "state": MODULE_STATE,
        "source_node": SOURCE_NODE,
        "gradient_role": GRADIENT_ROLE,
        "gradient_intent": GRADIENT_INTENT,
        "pain_score_at_birth": PAIN_SCORE_AT_BIRTH,
        "sandbox_only": True,
    }


def run_sandbox_probe(event: Dict[str, Any] | None = None) -> Dict[str, Any]:
    payload = dict(event or {})
    return {
        "ok": True,
        "state": MODULE_STATE,
        "source_node": SOURCE_NODE,
        "gradient_role": GRADIENT_ROLE,
        "payload_preserved": payload,
        "guardrails": {
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "actual_apply_executed": False,
            "sandbox_only": True,
        },
    }


def propose_route_contract(event: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return {
        "ok": True,
        "contract": "D75_CHILD_MODULE_ROUTE_CONTRACT",
        "source_node": SOURCE_NODE,
        "handler_role": GRADIENT_ROLE,
        "allowed_mode": "SANDBOX_PROBE_ONLY",
        "forbidden_actions": [
            "direct_core_edit",
            "overwrite_canonical_memory",
            "external_ai_call",
            "auto_apply_runtime_mutation",
        ],
        "required_before_integration": [
            "D66_RECHECK",
            "UNIT_TESTS",
            "REGRESSION_TESTS",
            "ROLLBACK_MANIFEST",
            "HUMAN_OR_HIGHER_POLICY_APPROVAL",
        ],
    }
