
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D102_REPORT = "reports/d102_post_execution_verifier.json"
D102_EVIDENCE = "reports/d102_post_execution_evidence_report.json"
D102_CHANGED = "reports/d102_changed_files_manifest.json"
D102_INTEGRITY = "reports/d102_execution_integrity_summary.json"
D102_SCOPE = "reports/d102_d103_rollback_evidence_builder_scope.json"

OUT = "reports/d103_rollback_evidence_builder.json"
BUNDLE = "reports/d103_rollback_evidence_bundle.json"
RESTORE = "reports/d103_restore_point_reference.json"
READY = "reports/d103_rollback_readiness_summary.json"
D104_SCOPE = "reports/d103_d104_final_audit_ledger_scope.json"

REQ_D102_DECISION = "POST_EXECUTION_VERIFIER_READY"
REQ_GATE = "D103_ROLLBACK_EVIDENCE_BUILDER"
REQ_PHRASE = "APPROVE_D103_ROLLBACK_EVIDENCE_BUILDER_ONLY"

FALSE_FLAGS = [
    "external_ai_called", "network_accessed", "runtime_code_mutated",
    "protected_core_mutated", "canonical_memory_mutated",
    "actual_apply_executed", "route_inserted", "git_commit_by_ai",
]

FORBIDDEN = [
    "actual_apply_by_ai", "route_insert_by_ai", "protected_core_mutation_by_ai",
    "canonical_memory_overwrite_by_ai", "external_ai_network_execution",
    "git_commit_or_push_by_ai", "execute_rollback_by_ai",
    "delete_runtime_candidate_by_ai", "run_manual_apply_now",
    "execute_post_fix_mutation", "execute_rollback_now", "restore_files_now",
    "delete_generated_candidate",
]

ALLOWED = [
    "rollback_evidence_builder",
    "rollback_evidence_bundle",
    "restore_point_reference",
    "rollback_readiness_summary",
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
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def check_false(label, data, errors):
    for key in FALSE_FLAGS:
        if data.get(key) is not False:
            errors.append(f"{label}.{key} must be false")


def validate_d102(d102, evidence, changed, integrity, scope):
    errors = []
    warnings = []

    if not d102:
        return ["missing D102 post-execution verifier report"], warnings

    if d102.get("ok") is not True:
        errors.append("D102 ok must be true")
    if d102.get("decision") != REQ_D102_DECISION:
        errors.append(f"D102 decision invalid: {d102.get('decision')}")

    guard = d102.get("guardrails") if isinstance(d102.get("guardrails"), dict) else {}
    check_false("D102.guardrails", guard, errors)

    for key in ["rollback_executed", "restore_executed", "manual_execution_performed", "approval_for_real_apply"]:
        if guard.get(key) is not False:
            errors.append(f"D102 guardrails.{key} must be false")
    if guard.get("post_execution_verifier_only") is not True:
        errors.append("D102 post_execution_verifier_only must be true")

    verifier = d102.get("post_execution_verifier") if isinstance(d102.get("post_execution_verifier"), dict) else {}
    if not verifier:
        errors.append("D102 embedded verifier missing")
    else:
        if verifier.get("ok") is not True:
            errors.append("D102 verifier ok must be true")
        if verifier.get("next_required_gate") != REQ_GATE:
            errors.append("D102 verifier next_required_gate must be D103")

    if not evidence:
        errors.append("missing D102 evidence report")
    else:
        for key in ["real_apply_observed", "route_insert_observed", "protected_core_mutation_observed", "external_ai_execution_observed", "rollback_execution_observed"]:
            if evidence.get(key) is not False:
                errors.append(f"D102 evidence {key} must be false")

    if not changed:
        errors.append("missing D102 changed files manifest")
    else:
        if changed.get("manual_execution_performed") is not False:
            errors.append("D102 changed files manual_execution_performed must be false")
        if changed.get("manifest_mode") != "DECLARATIVE_NO_EXECUTION_MANIFEST":
            errors.append("D102 changed files manifest mode invalid")

    if not integrity:
        errors.append("missing D102 execution integrity summary")
    else:
        for key in ["manual_execution_performed", "ai_execution_performed", "actual_apply_executed", "route_inserted", "protected_core_mutated", "canonical_memory_mutated", "network_accessed", "external_ai_called", "git_commit_by_ai", "rollback_executed"]:
            if integrity.get(key) is not False:
                errors.append(f"D102 integrity {key} must be false")
        if integrity.get("ready_for_d103") is not True:
            errors.append("D102 integrity ready_for_d103 must be true")

    if not scope:
        errors.append("missing D102 D103 scope")
    else:
        if scope.get("allowed_next_gate") != REQ_GATE:
            errors.append("D102 scope allowed_next_gate must be D103")
        for item in ALLOWED:
            if item not in scope.get("d103_allowed_to_create", []):
                errors.append(f"D102 scope missing allowed item: {item}")
        for item in FORBIDDEN:
            if item not in scope.get("d103_must_not_execute", []):
                errors.append(f"D102 scope missing must-not-execute item: {item}")
        if scope.get("apply_allowed_after_d102") is not False:
            errors.append("D102 scope apply_allowed_after_d102 must be false")
        if scope.get("route_insert_allowed_after_d102") is not False:
            errors.append("D102 scope route_insert_allowed_after_d102 must be false")
        if scope.get("protected_core_mutation_allowed_after_d102") is not False:
            errors.append("D102 scope protected_core_mutation_allowed_after_d102 must be false")
        if scope.get("required_phrase_for_later_gate") != REQ_PHRASE:
            errors.append("D102 scope required phrase invalid")

    return errors, warnings


def report_list(root):
    d = root / "reports"
    if not d.exists():
        return []
    prefixes = ("d99_", "d100_", "d101_", "d102_")
    return sorted(p.relative_to(root).as_posix() for p in d.iterdir() if p.is_file() and p.name.startswith(prefixes))


def create_rollback_evidence_builder(root="."):
    root = Path(root).resolve()

    d102 = read_json(root / D102_REPORT, {}) or {}
    evidence = read_json(root / D102_EVIDENCE, {}) or {}
    changed = read_json(root / D102_CHANGED, {}) or {}
    integrity = read_json(root / D102_INTEGRITY, {}) or {}
    scope = read_json(root / D102_SCOPE, {}) or {}

    errors, warnings = validate_d102(d102, evidence, changed, integrity, scope)

    verifier_id = str(d102.get("verifier_id") or evidence.get("verifier_id") or integrity.get("verifier_id") or scope.get("verifier_id") or "")
    capsule_id = str(d102.get("capsule_id") or evidence.get("capsule_id") or integrity.get("capsule_id") or scope.get("capsule_id") or "")
    decision_id = str(d102.get("decision_id") or evidence.get("decision_id") or "")
    builder_id = "d103-" + digest({"verifier_id": verifier_id, "capsule_id": capsule_id, "decision_id": decision_id, "d102": d102.get("decision")})

    ok = not errors
    decision = "ROLLBACK_EVIDENCE_BUILDER_READY" if ok else "ROLLBACK_EVIDENCE_BUILDER_BLOCKED"
    result = "D103_ROLLBACK_EVIDENCE_BUILDER_CREATED" if ok else "D103_ROLLBACK_EVIDENCE_BUILDER_BLOCKED"

    builder = {
        "state": "D103_ROLLBACK_EVIDENCE_BUILDER_ARTIFACT",
        "ok": True,
        "builder_id": builder_id,
        "verifier_id": verifier_id,
        "capsule_id": capsule_id,
        "decision_id": decision_id,
        "created_at": now(),
        "mode": "ROLLBACK_EVIDENCE_BUILDER_DOCUMENTATION_ONLY",
        "rollback_allowed_now": False,
        "restore_allowed_now": False,
        "apply_allowed_now": False,
        "route_insert_allowed_now": False,
        "protected_core_mutation_allowed_now": False,
        "not_approved": FORBIDDEN,
        "next_required_gate": "D104_FINAL_AUDIT_LEDGER",
    }

    bundle = {
        "state": "D103_ROLLBACK_EVIDENCE_BUNDLE",
        "ok": True,
        "builder_id": builder_id,
        "verifier_id": verifier_id,
        "capsule_id": capsule_id,
        "created_at": now(),
        "bundle_mode": "ROLLBACK_EVIDENCE_DOCUMENTATION_ONLY",
        "rollback_executed": False,
        "restore_executed": False,
        "source_reports": report_list(root),
        "not_approved": FORBIDDEN,
    }

    restore = {
        "state": "D103_RESTORE_POINT_REFERENCE",
        "ok": True,
        "builder_id": builder_id,
        "verifier_id": verifier_id,
        "capsule_id": capsule_id,
        "created_at": now(),
        "restore_reference_mode": "REFERENCE_ONLY_NO_RESTORE",
        "restore_point_created_by_script": False,
        "restore_executed": False,
        "human_review_required": True,
        "blocked_now": ["git restore", "git checkout --", "git reset --hard", "execute rollback"],
    }

    readiness = {
        "state": "D103_ROLLBACK_READINESS_SUMMARY",
        "ok": True,
        "builder_id": builder_id,
        "verifier_id": verifier_id,
        "capsule_id": capsule_id,
        "created_at": now(),
        "readiness_decision": "ROLLBACK_EVIDENCE_READY_NO_ROLLBACK_EXECUTED",
        "rollback_evidence_ready": True,
        "ready_for_d104": True,
        "rollback_executed": False,
        "restore_executed": False,
        "actual_apply_executed": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "canonical_memory_mutated": False,
        "external_ai_called": False,
        "network_accessed": False,
        "git_commit_by_ai": False,
    }

    d104_scope = {
        "state": "D103_D104_FINAL_AUDIT_LEDGER_SCOPE",
        "ok": True,
        "builder_id": builder_id,
        "verifier_id": verifier_id,
        "capsule_id": capsule_id,
        "created_at": now(),
        "allowed_next_gate": "D104_FINAL_AUDIT_LEDGER",
        "d104_allowed_to_create": [
            "final_audit_ledger",
            "replay_log_index",
            "guarded_autonomy_chain_summary",
            "terminal_safety_state",
        ],
        "d104_must_not_execute": FORBIDDEN + ["execute_final_apply", "execute_rollback_now", "mutate_chain_history"],
        "apply_allowed_after_d103": False,
        "route_insert_allowed_after_d103": False,
        "protected_core_mutation_allowed_after_d103": False,
        "required_phrase_for_later_gate": "APPROVE_D104_FINAL_AUDIT_LEDGER_ONLY",
    }

    if ok:
        write_json(root / BUNDLE, bundle)
        write_json(root / RESTORE, restore)
        write_json(root / READY, readiness)
        write_json(root / D104_SCOPE, d104_scope)

    report = {
        "state": "D103_ROLLBACK_EVIDENCE_BUILDER",
        "result": result,
        "route": "FIELD_INTENT_ROLLBACK_EVIDENCE_BUILDER",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "builder_id": builder_id,
        "verifier_id": verifier_id,
        "capsule_id": capsule_id,
        "decision_id": decision_id,
        "rollback_evidence_builder": builder if ok else {},
        "rollback_evidence_bundle": bundle if ok else {},
        "restore_point_reference": restore if ok else {},
        "rollback_readiness_summary": readiness if ok else {},
        "d104_scope": d104_scope if ok else {},
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
            "rollback_evidence_only": True,
            "approval_for_real_apply": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": warnings},
        "summary": {
            "decision": decision,
            "builder_id": builder_id,
            "verifier_id": verifier_id,
            "capsule_id": capsule_id,
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "rollback_evidence_builder_created": ok,
            "rollback_evidence_bundle_created": ok,
            "restore_point_reference_created": ok,
            "rollback_readiness_summary_created": ok,
            "actual_apply_executed": False,
            "rollback_executed": False,
            "restore_executed": False,
            "protected_core_untouched": True,
            "next_step": "D104 may create final audit ledger and replay log. Real apply remains blocked.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_rollback_evidence_builder(), ensure_ascii=False, indent=2))
