
from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

D97_REPORT = "reports/d97_protected_core_no_touch_reconfirmation.json"
D97_HASH = "reports/d97_protected_file_hash_snapshot.json"
D97_ROUTE = "reports/d97_no_route_insert_reconfirmation.json"
D97_SCOPE = "reports/d97_d98_rollback_restore_scope.json"

OUT = "reports/d98_rollback_restore_command_pack.json"
RESTORE = "reports/d98_restore_manifest_reference.json"
ABORT = "reports/d98_pre_execution_abort_plan.json"
D99_SCOPE = "reports/d98_d99_final_guarded_execution_capsule_scope.json"

REQ_D97_DECISION = "PROTECTED_CORE_NO_TOUCH_RECONFIRMED"
REQ_GATE = "D98_ROLLBACK_RESTORE_COMMAND_PACK"
REQ_PHRASE = "APPROVE_D98_ROLLBACK_RESTORE_COMMAND_PACK_ONLY"

FALSE_FLAGS = [
    "external_ai_called",
    "network_accessed",
    "runtime_code_mutated",
    "protected_core_mutated",
    "canonical_memory_mutated",
    "actual_apply_executed",
    "route_inserted",
    "git_commit_by_ai",
]

FORBIDDEN = [
    "actual_apply",
    "route_insert",
    "protected_core_mutation",
    "canonical_memory_overwrite",
    "external_ai_network_call",
    "git_commit_or_push_by_ai",
    "execute_rollback_now",
    "delete_runtime_candidate",
]


def now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path, default=None):
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path, data):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def digest(data):
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def require_false(label, data, errors):
    for key in FALSE_FLAGS:
        if data.get(key) is not False:
            errors.append(f"{label}.{key} must be false")


def validate_d97(d97, hs, route, scope):
    errors = []
    warnings = []

    if not d97:
        return ["missing D97 protected-core no-touch reconfirmation report"], warnings

    if d97.get("ok") is not True:
        errors.append("D97 ok must be true")
    if d97.get("decision") != REQ_D97_DECISION:
        errors.append(f"D97 decision invalid: {d97.get('decision')}")

    guard = d97.get("guardrails") if isinstance(d97.get("guardrails"), dict) else {}
    require_false("D97.guardrails", guard, errors)
    if guard.get("protected_core_no_touch_reconfirmation_only") is not True:
        errors.append("D97 protected_core_no_touch_reconfirmation_only must be true")
    if guard.get("hash_snapshot_only") is not True:
        errors.append("D97 hash_snapshot_only must be true")
    if guard.get("approval_for_real_apply") is not False:
        errors.append("D97 approval_for_real_apply must be false")

    if not hs:
        errors.append("missing D97 protected file hash snapshot")
    else:
        if hs.get("ok") is not True:
            errors.append("D97 hash snapshot ok must be true")
        if hs.get("mutation_performed") is not False:
            errors.append("D97 hash snapshot mutation_performed must be false")
        if not hs.get("snapshot_sha256"):
            errors.append("D97 snapshot_sha256 missing")

    if not route:
        errors.append("missing D97 no-route-insert reconfirmation")
    else:
        if route.get("ok") is not True:
            errors.append("D97 no-route ok must be true")
        if route.get("route_insert_allowed_now") is not False:
            errors.append("D97 route_insert_allowed_now must be false")
        if route.get("route_inserted") is not False:
            errors.append("D97 route_inserted must be false")
        if route.get("route_mutation_performed") is not False:
            errors.append("D97 route_mutation_performed must be false")
        if route.get("next_required_gate") != REQ_GATE:
            errors.append("D97 no-route next_required_gate must be D98")

    if not scope:
        errors.append("missing D97 D98 rollback scope")
    else:
        if scope.get("ok") is not True:
            errors.append("D97 D98 scope ok must be true")
        if scope.get("allowed_next_gate") != REQ_GATE:
            errors.append("D97 D98 scope allowed_next_gate must be D98")
        for item in [
            "rollback_restore_command_pack",
            "restore_manifest_reference",
            "pre_execution_abort_plan",
        ]:
            if item not in scope.get("d98_allowed_to_create", []):
                errors.append(f"D97 D98 scope missing allowed item: {item}")
        for item in FORBIDDEN:
            if item not in scope.get("d98_must_not_execute", []):
                errors.append(f"D97 D98 scope missing must-not-execute item: {item}")
        if scope.get("apply_allowed_after_d97") is not False:
            errors.append("D97 scope apply_allowed_after_d97 must be false")
        if scope.get("route_insert_allowed_after_d97") is not False:
            errors.append("D97 scope route_insert_allowed_after_d97 must be false")
        if scope.get("protected_core_mutation_allowed_after_d97") is not False:
            errors.append("D97 scope protected_core_mutation_allowed_after_d97 must be false")
        if scope.get("required_phrase_for_later_gate") != REQ_PHRASE:
            errors.append("D97 scope required phrase invalid")

    return errors, warnings


def build_pack(pack_id, reconfirmation_id, regression_id, hs):
    return {
        "state": "D98_ROLLBACK_RESTORE_COMMAND_PACK_ARTIFACT",
        "ok": True,
        "pack_id": pack_id,
        "reconfirmation_id": reconfirmation_id,
        "regression_id": regression_id,
        "created_at": now(),
        "mode": "ROLLBACK_RESTORE_DOCUMENTATION_ONLY",
        "commands_are_documentation_only": True,
        "commands_must_not_be_executed_by_ai": True,
        "human_may_review_manually": True,
        "restore_manifest_source": "reports/d97_protected_file_hash_snapshot.json",
        "restore_manifest_snapshot_sha256": hs.get("snapshot_sha256"),
        "review_commands": [
            "git status --short",
            "git diff --stat",
            "cat reports/d97_protected_core_no_touch_reconfirmation.json",
            "cat reports/d97_protected_file_hash_snapshot.json",
            "cat reports/d97_no_route_insert_reconfirmation.json",
        ],
        "blocked_execution_commands": [
            "git apply",
            "git restore",
            "git checkout -- <protected-core-path>",
            "git reset --hard",
            "git commit",
            "git push",
            "route insert",
            "python -c '<runtime mutation>'",
        ],
        "not_approved": FORBIDDEN,
        "next_required_gate": "D99_FINAL_GUARDED_EXECUTION_CAPSULE",
    }


def build_restore_ref(pack_id, hs):
    return {
        "state": "D98_RESTORE_MANIFEST_REFERENCE",
        "ok": True,
        "pack_id": pack_id,
        "created_at": now(),
        "source_hash_snapshot_state": hs.get("state"),
        "source_snapshot_sha256": hs.get("snapshot_sha256"),
        "protected_files_count": hs.get("hashed_files_count", 0),
        "restore_reference_mode": "DOCUMENTATION_ONLY",
        "restore_not_executed": True,
        "not_allowed_now": [
            "git restore",
            "git checkout --",
            "git reset --hard",
            "rm -rf runtime candidate",
        ],
    }


def build_abort(pack_id):
    return {
        "state": "D98_PRE_EXECUTION_ABORT_PLAN",
        "ok": True,
        "pack_id": pack_id,
        "created_at": now(),
        "abort_if": [
            "D97 protected-core hash snapshot is missing",
            "D97 no-route-insert reconfirmation is missing",
            "D96 final local regression is missing or failed",
            "any protected-core file differs from reviewed snapshot without explicit human explanation",
            "any route insertion is detected",
            "any runtime/core/canonical memory mutation is detected before final capsule",
            "any external AI/network call is required",
            "any AI git commit or push is attempted",
            "rollback command pack would require destructive execution",
        ],
        "must_remain_false": {
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "runtime_code_mutated": False,
            "external_ai_called": False,
            "network_accessed": False,
            "git_commit_by_ai": False,
            "rollback_executed": False,
        },
        "human_review_required": True,
    }


def build_d99_scope(pack_id, reconfirmation_id, regression_id):
    return {
        "state": "D98_D99_FINAL_GUARDED_EXECUTION_CAPSULE_SCOPE",
        "ok": True,
        "pack_id": pack_id,
        "reconfirmation_id": reconfirmation_id,
        "regression_id": regression_id,
        "created_at": now(),
        "allowed_next_gate": "D99_FINAL_GUARDED_EXECUTION_CAPSULE",
        "d99_allowed_to_create": [
            "final_guarded_execution_capsule",
            "final_no_apply_blocker_state",
            "post_capsule_manual_review_checklist",
        ],
        "d99_must_not_execute": FORBIDDEN,
        "apply_allowed_after_d98": False,
        "route_insert_allowed_after_d98": False,
        "protected_core_mutation_allowed_after_d98": False,
        "required_phrase_for_later_gate": "APPROVE_D99_FINAL_GUARDED_EXECUTION_CAPSULE_ONLY",
    }


def create_rollback_restore_command_pack(root="."):
    root = Path(root).resolve()

    d97 = read_json(root / D97_REPORT, {}) or {}
    hs = read_json(root / D97_HASH, {}) or {}
    route = read_json(root / D97_ROUTE, {}) or {}
    scope = read_json(root / D97_SCOPE, {}) or {}

    errors, warnings = validate_d97(d97, hs, route, scope)

    reconfirmation_id = str(d97.get("reconfirmation_id") or hs.get("reconfirmation_id") or route.get("reconfirmation_id") or "")
    regression_id = str(d97.get("regression_id") or hs.get("regression_id") or route.get("regression_id") or "")
    package_id = str(d97.get("package_id") or "")

    pack_id = "d98-" + digest({
        "reconfirmation_id": reconfirmation_id,
        "regression_id": regression_id,
        "package_id": package_id,
        "d97_decision": d97.get("decision"),
        "snapshot_sha256": hs.get("snapshot_sha256"),
    })

    ok = not errors
    decision = "ROLLBACK_RESTORE_COMMAND_PACK_READY" if ok else "ROLLBACK_RESTORE_COMMAND_PACK_BLOCKED"
    result = "D98_ROLLBACK_RESTORE_COMMAND_PACK_CREATED" if ok else "D98_ROLLBACK_RESTORE_COMMAND_PACK_BLOCKED"

    pack = build_pack(pack_id, reconfirmation_id, regression_id, hs)
    restore = build_restore_ref(pack_id, hs)
    abort = build_abort(pack_id)
    d99_scope = build_d99_scope(pack_id, reconfirmation_id, regression_id)

    if ok:
        write_json(root / RESTORE, restore)
        write_json(root / ABORT, abort)
        write_json(root / D99_SCOPE, d99_scope)

    report = {
        "state": "D98_ROLLBACK_RESTORE_COMMAND_PACK",
        "result": result,
        "route": "FIELD_INTENT_ROLLBACK_RESTORE_COMMAND_PACK",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "pack_id": pack_id,
        "reconfirmation_id": reconfirmation_id,
        "regression_id": regression_id,
        "package_id": package_id,
        "restore_manifest_reference_path": str(root / RESTORE) if ok else "",
        "pre_execution_abort_plan_path": str(root / ABORT) if ok else "",
        "d99_scope_path": str(root / D99_SCOPE) if ok else "",
        "input_reports": {
            "d97_report_path": str(root / D97_REPORT),
            "d97_hash_snapshot_path": str(root / D97_HASH),
            "d97_no_route_path": str(root / D97_ROUTE),
            "d97_d98_scope_path": str(root / D97_SCOPE),
        },
        "rollback_restore_command_pack": pack if ok else {},
        "restore_manifest_reference": restore if ok else {},
        "pre_execution_abort_plan": abort if ok else {},
        "d99_scope": d99_scope if ok else {},
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "rollback_executed": False,
            "restore_executed": False,
            "rollback_restore_documentation_only": True,
            "approval_for_real_apply": False,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "pack_id": pack_id,
            "reconfirmation_id": reconfirmation_id,
            "regression_id": regression_id,
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "rollback_restore_command_pack_created": ok,
            "restore_manifest_reference_created": ok,
            "pre_execution_abort_plan_created": ok,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_untouched": True,
            "next_step": "D99 may create final guarded execution capsule. Real apply remains blocked.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_rollback_restore_command_pack(), ensure_ascii=False, indent=2))
