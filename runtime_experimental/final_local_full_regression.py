
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

D95_REPORT = "reports/d95_human_signed_execution_intent.json"
D95_SIGNATURE = "reports/d95_execution_intent_signature.json"
D95_BLOCKED = "reports/d95_apply_still_blocked.json"

OUT = "reports/d96_final_local_full_regression.json"
RESULTS_OUT = "reports/d96_full_regression_results.json"
STILL_BLOCKED_OUT = "reports/d96_apply_still_blocked.json"
D97_SCOPE_OUT = "reports/d96_d97_no_touch_reconfirmation_scope.json"

REQ_D95_DECISION = "HUMAN_SIGNED_EXECUTION_INTENT_READY"
REQ_D96_GATE = "D96_FINAL_LOCAL_FULL_REGRESSION"
REQ_D95_PHRASE = "APPROVE_D95_HUMAN_SIGNED_EXECUTION_INTENT_FOR_D96_REGRESSION_ONLY"

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

SAFE_REGRESSION_COMMANDS = [
    [sys.executable, "-m", "py_compile", "runtime_experimental/final_local_full_regression.py"],
    [sys.executable, "-m", "unittest", "tests.test_d90_controlled_apply_plan", "-v"],
    [sys.executable, "-m", "unittest", "tests.test_d91_explicit_apply_scope_approval", "-v"],
    [sys.executable, "-m", "unittest", "tests.test_d92_guarded_apply_dry_run_package", "-v"],
    [sys.executable, "-m", "unittest", "tests.test_d93_dry_run_recheck_gate", "-v"],
    [sys.executable, "-m", "unittest", "tests.test_d94_final_execution_approval_request", "-v"],
    [sys.executable, "-m", "unittest", "tests.test_d95_human_signed_execution_intent", "-v"],
    [sys.executable, "-m", "unittest", "tests.test_d96_final_local_full_regression", "-v"],
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


def check_false_flags(label, data, errors):
    for key in FALSE_FLAGS:
        if data.get(key) is not False:
            errors.append(f"{label}.{key} must be false")


def validate_d95(d95, signature, blocked):
    errors = []
    warnings = []

    if not d95:
        errors.append("missing D95 human signed execution intent")
        return errors, warnings

    if d95.get("ok") is not True:
        errors.append("D95 ok must be true")
    if d95.get("decision") != REQ_D95_DECISION:
        errors.append(f"D95 decision invalid: {d95.get('decision')}")

    guard = d95.get("guardrails") if isinstance(d95.get("guardrails"), dict) else {}
    check_false_flags("D95.guardrails", guard, errors)
    if guard.get("human_signed_intent_only") is not True:
        errors.append("D95 human_signed_intent_only must be true")
    if guard.get("d96_regression_only") is not True:
        errors.append("D95 d96_regression_only must be true")
    if guard.get("approval_for_real_apply") is not False:
        errors.append("D95 approval_for_real_apply must be false")

    signed_intent = d95.get("signed_intent") if isinstance(d95.get("signed_intent"), dict) else {}
    if not signed_intent:
        errors.append("D95 embedded signed_intent missing")
    else:
        if signed_intent.get("approved_next_gate") != REQ_D96_GATE:
            errors.append("D95 signed_intent approved_next_gate must be D96")
        if signed_intent.get("signed_phrase") != REQ_D95_PHRASE:
            errors.append("D95 signed_intent phrase invalid")
        for key in ["apply_allowed_now", "route_insert_allowed_now", "protected_core_mutation_allowed_now"]:
            if signed_intent.get(key) is not False:
                errors.append(f"D95 signed_intent {key} must be false")
        for item in FORBIDDEN_REAL_ACTIONS:
            if item not in signed_intent.get("not_approved", []):
                errors.append(f"D95 signed_intent not_approved missing {item}")

    if not signature:
        errors.append("missing D95 execution intent signature")
    else:
        if signature.get("ok") is not True:
            errors.append("D95 signature ok must be true")
        if signature.get("approval_phrase") != REQ_D95_PHRASE:
            errors.append("D95 signature approval_phrase invalid")
        if signature.get("signed_scope") != "D96_FINAL_LOCAL_FULL_REGRESSION_ONLY":
            errors.append("D95 signature signed_scope invalid")
        if not signature.get("signature_sha256"):
            errors.append("D95 signature sha missing")
        for item in FORBIDDEN_REAL_ACTIONS:
            if item not in signature.get("not_approved", []):
                errors.append(f"D95 signature not_approved missing {item}")

    if not blocked:
        errors.append("missing D95 apply-still-blocked report")
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
                errors.append(f"D95 blocked {key} must be false")
        if blocked.get("next_required_gate") != REQ_D96_GATE:
            errors.append("D95 blocked next_required_gate must be D96")

    return errors, warnings


def command_is_safe(cmd):
    joined = " ".join(cmd).lower()
    banned = ["git apply", "git commit", "git push", "route insert", "curl ", "wget ", "ssh ", "scp "]
    if any(x in joined for x in banned):
        return False
    if cmd[:2] != [sys.executable, "-m"]:
        return False
    if len(cmd) < 3:
        return False
    return cmd[2] in {"py_compile", "unittest"}


def run_command(root, cmd, timeout=90):
    if not command_is_safe(cmd):
        return {
            "command": " ".join(cmd),
            "ok": False,
            "returncode": 999,
            "stdout_tail": "",
            "stderr_tail": "blocked unsafe regression command",
            "duration_timeout_seconds": timeout,
        }

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(root),
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return {
            "command": " ".join(cmd),
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-4000:],
            "stderr_tail": proc.stderr[-4000:],
            "duration_timeout_seconds": timeout,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": " ".join(cmd),
            "ok": False,
            "returncode": 124,
            "stdout_tail": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": "timeout expired",
            "duration_timeout_seconds": timeout,
        }


def build_results(regression_id, intent_id, command_results):
    all_green = all(item.get("ok") is True for item in command_results)
    return {
        "state": "D96_FULL_REGRESSION_RESULTS",
        "ok": all_green,
        "regression_id": regression_id,
        "intent_id": intent_id,
        "created_at": now(),
        "commands_executed_locally": True,
        "network_accessed": False,
        "external_ai_called": False,
        "command_results": command_results,
        "summary": {
            "commands_count": len(command_results),
            "passed_count": sum(1 for x in command_results if x.get("ok") is True),
            "failed_count": sum(1 for x in command_results if x.get("ok") is not True),
        },
    }


def build_still_blocked(regression_id):
    return {
        "state": "D96_APPLY_STILL_BLOCKED",
        "ok": True,
        "regression_id": regression_id,
        "created_at": now(),
        "apply_allowed_now": False,
        "route_insert_allowed_now": False,
        "protected_core_mutation_allowed_now": False,
        "canonical_memory_mutation_allowed_now": False,
        "external_ai_call_allowed_now": False,
        "git_action_by_ai_allowed_now": False,
        "reason": "D96 runs local regression only. It does not grant execution permission.",
        "next_required_gate": "D97_PROTECTED_CORE_NO_TOUCH_RECONFIRMATION",
    }


def build_d97_scope(regression_id, intent_id):
    return {
        "state": "D96_D97_NO_TOUCH_RECONFIRMATION_SCOPE",
        "ok": True,
        "regression_id": regression_id,
        "intent_id": intent_id,
        "created_at": now(),
        "allowed_next_gate": "D97_PROTECTED_CORE_NO_TOUCH_RECONFIRMATION",
        "d97_allowed_to_create": [
            "protected_core_no_touch_reconfirmation",
            "protected_file_hash_snapshot",
            "no_route_insert_reconfirmation",
        ],
        "d97_must_not_execute": FORBIDDEN_REAL_ACTIONS,
        "apply_allowed_after_d96": False,
        "route_insert_allowed_after_d96": False,
        "protected_core_mutation_allowed_after_d96": False,
        "required_phrase_for_later_gate": "APPROVE_D97_PROTECTED_CORE_NO_TOUCH_RECONFIRMATION_ONLY",
    }


def create_final_local_full_regression(root=".", run_commands=True):
    root = Path(root).resolve()

    d95 = read_json(root / D95_REPORT, {}) or {}
    signature = read_json(root / D95_SIGNATURE, {}) or {}
    blocked = read_json(root / D95_BLOCKED, {}) or {}

    errors, warnings = validate_d95(d95, signature, blocked)

    intent_id = str(d95.get("intent_id") or signature.get("intent_id") or blocked.get("intent_id") or "")
    request_id = str(d95.get("request_id") or signature.get("request_id") or "")
    package_id = str(d95.get("package_id") or signature.get("package_id") or "")

    regression_id = "d96-" + digest({
        "intent_id": intent_id,
        "request_id": request_id,
        "package_id": package_id,
        "d95_decision": d95.get("decision"),
    })

    command_results = []
    if not errors and run_commands:
        command_results = [run_command(root, cmd) for cmd in SAFE_REGRESSION_COMMANDS]

    if command_results and not all(item.get("ok") is True for item in command_results):
        errors.append("one or more final local regression commands failed")

    ok = not errors
    decision = "FINAL_LOCAL_FULL_REGRESSION_PASSED" if ok else "FINAL_LOCAL_FULL_REGRESSION_BLOCKED"
    result = "D96_FINAL_LOCAL_FULL_REGRESSION_COMPLETED" if ok else "D96_FINAL_LOCAL_FULL_REGRESSION_BLOCKED"

    results = build_results(regression_id, intent_id, command_results)
    blocked_out = build_still_blocked(regression_id)
    d97_scope = build_d97_scope(regression_id, intent_id)

    if ok:
        write_json(root / RESULTS_OUT, results)
        write_json(root / STILL_BLOCKED_OUT, blocked_out)
        write_json(root / D97_SCOPE_OUT, d97_scope)

    report = {
        "state": "D96_FINAL_LOCAL_FULL_REGRESSION",
        "result": result,
        "route": "FIELD_INTENT_FINAL_LOCAL_FULL_REGRESSION",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "regression_id": regression_id,
        "intent_id": intent_id,
        "request_id": request_id,
        "package_id": package_id,
        "results_path": str(root / RESULTS_OUT) if ok else "",
        "apply_still_blocked_path": str(root / STILL_BLOCKED_OUT) if ok else "",
        "d97_scope_path": str(root / D97_SCOPE_OUT) if ok else "",
        "input_reports": {
            "d95_report_path": str(root / D95_REPORT),
            "d95_signature_path": str(root / D95_SIGNATURE),
            "d95_blocked_path": str(root / D95_BLOCKED),
        },
        "regression_results": results if ok else {},
        "apply_still_blocked": blocked_out if ok else {},
        "d97_scope": d97_scope if ok else {},
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "local_regression_only": True,
            "approval_for_real_apply": False,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "regression_id": regression_id,
            "intent_id": intent_id,
            "commands_count": len(command_results),
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "final_local_full_regression_completed": ok,
            "all_local_regression_commands_green": ok,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_untouched": True,
            "next_step": "D97 may reconfirm protected-core no-touch state. Real apply remains blocked.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_final_local_full_regression(), ensure_ascii=False, indent=2))
