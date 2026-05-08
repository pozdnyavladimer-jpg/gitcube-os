
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D96_REPORT = "reports/d96_final_local_full_regression.json"
D96_RESULTS = "reports/d96_full_regression_results.json"
D96_BLOCKED = "reports/d96_apply_still_blocked.json"
D96_D97_SCOPE = "reports/d96_d97_no_touch_reconfirmation_scope.json"

OUT = "reports/d97_protected_core_no_touch_reconfirmation.json"
HASH_SNAPSHOT_OUT = "reports/d97_protected_file_hash_snapshot.json"
NO_ROUTE_OUT = "reports/d97_no_route_insert_reconfirmation.json"
D98_SCOPE_OUT = "reports/d97_d98_rollback_restore_scope.json"

REQ_D96_DECISION = "FINAL_LOCAL_FULL_REGRESSION_PASSED"
REQ_D97_GATE = "D97_PROTECTED_CORE_NO_TOUCH_RECONFIRMATION"
REQ_D97_PHRASE = "APPROVE_D97_PROTECTED_CORE_NO_TOUCH_RECONFIRMATION_ONLY"

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

FORBIDDEN_REAL_ACTIONS = [
    "actual_apply",
    "route_insert",
    "protected_core_mutation",
    "canonical_memory_overwrite",
    "external_ai_network_call",
    "git_commit_or_push_by_ai",
]

PROTECTED_PREFIXES = [
    "app/orchestration",
    "core",
    "runtime",
    "bridges",
    "memory",
]

ALLOWED_D97_CREATE = [
    "protected_core_no_touch_reconfirmation",
    "protected_file_hash_snapshot",
    "no_route_insert_reconfirmation",
]


def now() -> str:
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


def digest(data) -> str:
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_ignored_file(path: Path) -> bool:
    parts = set(path.parts)
    if "__pycache__" in parts or ".git" in parts:
        return True
    if path.suffix in {".pyc", ".pyo"}:
        return True
    return False


def snapshot_protected_files(root: Path):
    files = []
    missing_prefixes = []
    for prefix in PROTECTED_PREFIXES:
        base = root / prefix
        if not base.exists():
            missing_prefixes.append(prefix)
            continue
        if base.is_file():
            candidates = [base]
        else:
            candidates = [p for p in base.rglob("*") if p.is_file()]
        for p in candidates:
            if is_ignored_file(p):
                continue
            rel = p.relative_to(root).as_posix()
            files.append({
                "path": rel,
                "sha256": file_sha256(p),
                "size_bytes": p.stat().st_size,
            })
    files.sort(key=lambda x: x["path"])
    return files, missing_prefixes


def check_false_flags(label, data, errors):
    for key in FALSE_FLAGS:
        if data.get(key) is not False:
            errors.append(f"{label}.{key} must be false")


def validate_d96(d96, results, blocked, scope):
    errors = []
    warnings = []

    if not d96:
        errors.append("missing D96 final local full regression report")
        return errors, warnings

    if d96.get("ok") is not True:
        errors.append("D96 ok must be true")
    if d96.get("decision") != REQ_D96_DECISION:
        errors.append(f"D96 decision invalid: {d96.get('decision')}")

    guard = d96.get("guardrails") if isinstance(d96.get("guardrails"), dict) else {}
    check_false_flags("D96.guardrails", guard, errors)
    if guard.get("local_regression_only") is not True:
        errors.append("D96 local_regression_only must be true")
    if guard.get("approval_for_real_apply") is not False:
        errors.append("D96 approval_for_real_apply must be false")

    if not results:
        errors.append("missing D96 full regression results")
    else:
        if results.get("ok") is not True:
            errors.append("D96 results ok must be true")
        summary = results.get("summary") if isinstance(results.get("summary"), dict) else {}
        if summary.get("failed_count") not in (0, None):
            errors.append("D96 regression failed_count must be 0")
        if results.get("network_accessed") is not False:
            errors.append("D96 results network_accessed must be false")
        if results.get("external_ai_called") is not False:
            errors.append("D96 results external_ai_called must be false")

    if not blocked:
        errors.append("missing D96 apply-still-blocked report")
    else:
        for key in [
            "apply_allowed_now",
            "route_insert_allowed_now",
            "protected_core_mutation_allowed_now",
            "canonical_memory_mutation_allowed_now",
            "external_ai_call_allowed_now",
            "git_action_by_ai_allowed_now",
        ]:
            if blocked.get(key) is not False:
                errors.append(f"D96 blocked {key} must be false")
        if blocked.get("next_required_gate") != REQ_D97_GATE:
            errors.append("D96 blocked next_required_gate must be D97")

    if not scope:
        errors.append("missing D96 D97 no-touch reconfirmation scope")
    else:
        if scope.get("ok") is not True:
            errors.append("D96 D97 scope ok must be true")
        if scope.get("allowed_next_gate") != REQ_D97_GATE:
            errors.append("D96 D97 scope allowed_next_gate must be D97")
        for item in ALLOWED_D97_CREATE:
            if item not in scope.get("d97_allowed_to_create", []):
                errors.append(f"D96 D97 scope missing allowed item: {item}")
        for item in FORBIDDEN_REAL_ACTIONS:
            if item not in scope.get("d97_must_not_execute", []):
                errors.append(f"D96 D97 scope missing must-not-execute item: {item}")
        if scope.get("apply_allowed_after_d96") is not False:
            errors.append("D96 scope apply_allowed_after_d96 must be false")
        if scope.get("route_insert_allowed_after_d96") is not False:
            errors.append("D96 scope route_insert_allowed_after_d96 must be false")
        if scope.get("protected_core_mutation_allowed_after_d96") is not False:
            errors.append("D96 scope protected_core_mutation_allowed_after_d96 must be false")
        if scope.get("required_phrase_for_later_gate") != REQ_D97_PHRASE:
            errors.append("D96 scope required phrase invalid")

    return errors, warnings


def build_hash_snapshot(reconfirmation_id, regression_id, protected_files, missing_prefixes):
    return {
        "state": "D97_PROTECTED_FILE_HASH_SNAPSHOT",
        "ok": True,
        "reconfirmation_id": reconfirmation_id,
        "regression_id": regression_id,
        "created_at": now(),
        "protected_prefixes": PROTECTED_PREFIXES,
        "missing_prefixes": missing_prefixes,
        "hashed_files_count": len(protected_files),
        "protected_files": protected_files,
        "snapshot_sha256": hashlib.sha256(
            json.dumps(protected_files, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest(),
        "mutation_performed": False,
    }


def build_no_route_reconfirmation(reconfirmation_id, regression_id):
    return {
        "state": "D97_NO_ROUTE_INSERT_RECONFIRMATION",
        "ok": True,
        "reconfirmation_id": reconfirmation_id,
        "regression_id": regression_id,
        "created_at": now(),
        "route_insert_allowed_now": False,
        "route_inserted": False,
        "route_mutation_performed": False,
        "reason": "D97 only reconfirms no-route-insert state. It does not modify routing tables.",
        "next_required_gate": "D98_ROLLBACK_RESTORE_COMMAND_PACK",
    }


def build_d98_scope(reconfirmation_id, regression_id):
    return {
        "state": "D97_D98_ROLLBACK_RESTORE_SCOPE",
        "ok": True,
        "reconfirmation_id": reconfirmation_id,
        "regression_id": regression_id,
        "created_at": now(),
        "allowed_next_gate": "D98_ROLLBACK_RESTORE_COMMAND_PACK",
        "d98_allowed_to_create": [
            "rollback_restore_command_pack",
            "restore_manifest_reference",
            "pre_execution_abort_plan",
        ],
        "d98_must_not_execute": FORBIDDEN_REAL_ACTIONS + [
            "execute_rollback_now",
            "delete_runtime_candidate",
        ],
        "apply_allowed_after_d97": False,
        "route_insert_allowed_after_d97": False,
        "protected_core_mutation_allowed_after_d97": False,
        "required_phrase_for_later_gate": "APPROVE_D98_ROLLBACK_RESTORE_COMMAND_PACK_ONLY",
    }


def create_protected_core_no_touch_reconfirmation(root="."):
    root = Path(root).resolve()

    d96 = read_json(root / D96_REPORT, {}) or {}
    results = read_json(root / D96_RESULTS, {}) or {}
    blocked = read_json(root / D96_BLOCKED, {}) or {}
    scope = read_json(root / D96_D97_SCOPE, {}) or {}

    errors, warnings = validate_d96(d96, results, blocked, scope)

    regression_id = str(d96.get("regression_id") or results.get("regression_id") or blocked.get("regression_id") or scope.get("regression_id") or "")
    intent_id = str(d96.get("intent_id") or scope.get("intent_id") or "")
    package_id = str(d96.get("package_id") or "")

    reconfirmation_id = "d97-" + digest({
        "regression_id": regression_id,
        "intent_id": intent_id,
        "package_id": package_id,
        "d96_decision": d96.get("decision"),
    })

    protected_files, missing_prefixes = snapshot_protected_files(root)

    ok = not errors
    decision = "PROTECTED_CORE_NO_TOUCH_RECONFIRMED" if ok else "PROTECTED_CORE_NO_TOUCH_RECONFIRMATION_BLOCKED"
    result = "D97_PROTECTED_CORE_NO_TOUCH_RECONFIRMATION_CREATED" if ok else "D97_PROTECTED_CORE_NO_TOUCH_RECONFIRMATION_BLOCKED"

    hash_snapshot = build_hash_snapshot(reconfirmation_id, regression_id, protected_files, missing_prefixes)
    no_route = build_no_route_reconfirmation(reconfirmation_id, regression_id)
    d98_scope = build_d98_scope(reconfirmation_id, regression_id)

    if ok:
        write_json(root / HASH_SNAPSHOT_OUT, hash_snapshot)
        write_json(root / NO_ROUTE_OUT, no_route)
        write_json(root / D98_SCOPE_OUT, d98_scope)

    report = {
        "state": "D97_PROTECTED_CORE_NO_TOUCH_RECONFIRMATION",
        "result": result,
        "route": "FIELD_INTENT_PROTECTED_CORE_NO_TOUCH_RECONFIRMATION",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "reconfirmation_id": reconfirmation_id,
        "regression_id": regression_id,
        "intent_id": intent_id,
        "package_id": package_id,
        "hash_snapshot_path": str(root / HASH_SNAPSHOT_OUT) if ok else "",
        "no_route_reconfirmation_path": str(root / NO_ROUTE_OUT) if ok else "",
        "d98_scope_path": str(root / D98_SCOPE_OUT) if ok else "",
        "input_reports": {
            "d96_report_path": str(root / D96_REPORT),
            "d96_results_path": str(root / D96_RESULTS),
            "d96_blocked_path": str(root / D96_BLOCKED),
            "d96_d97_scope_path": str(root / D96_D97_SCOPE),
        },
        "protected_file_hash_snapshot": hash_snapshot if ok else {},
        "no_route_insert_reconfirmation": no_route if ok else {},
        "d98_scope": d98_scope if ok else {},
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "protected_core_no_touch_reconfirmation_only": True,
            "hash_snapshot_only": True,
            "approval_for_real_apply": False,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "reconfirmation_id": reconfirmation_id,
            "regression_id": regression_id,
            "hashed_files_count": len(protected_files),
            "missing_prefixes_count": len(missing_prefixes),
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "protected_core_no_touch_reconfirmed": ok,
            "protected_file_hash_snapshot_created": ok,
            "no_route_insert_reconfirmed": ok,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_untouched": True,
            "next_step": "D98 may create rollback/restore command pack. Real apply remains blocked.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_protected_core_no_touch_reconfirmation(), ensure_ascii=False, indent=2))
