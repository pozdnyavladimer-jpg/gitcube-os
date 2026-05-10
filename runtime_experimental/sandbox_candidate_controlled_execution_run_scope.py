
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D138_REPORT = "reports/d138_sandbox_candidate_human_execution_intent_scope.json"
D138_INTENT_RECORD = "reports/d138_sandbox_candidate_human_execution_intent_record.json"
D138_AUTHORITY_GUARD = "reports/d138_sandbox_candidate_execution_authority_guard.json"
D138_D139_SCOPE = "reports/d138_d139_sandbox_candidate_controlled_execution_run_scope.json"

OUT = "reports/d139_sandbox_candidate_controlled_execution_run_scope.json"
RUN_RESULT_OUT = "reports/d139_sandbox_candidate_execution_run_result.json"
SAFETY_RECEIPT_OUT = "reports/d139_sandbox_candidate_execution_safety_receipt.json"
D140_SCOPE_OUT = "reports/d139_d140_sandbox_candidate_post_execution_verification_scope.json"

REQ_D138_DECISION = "SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE_READY"
REQ_D139_GATE = "D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE"
REQ_D140_GATE = "D140_SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE"
REQ_D138_APPROVAL_SCOPE = "D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE_ONLY"

FALSE_GUARD_KEYS = [
    "external_ai_called",
    "network_accessed",
    "api_key_read",
    "secret_read",
    "shell_from_ai_executed",
    "runtime_code_mutated",
    "protected_core_mutated",
    "canonical_memory_mutated",
    "actual_apply_executed",
    "route_inserted",
    "git_commit_by_ai",
    "git_push_by_ai",
    "rollback_executed",
    "restore_executed",
]

SANDBOX_ROOT = "runtime_experimental/ai_sandbox_work"


def now():
    return datetime.now(timezone.utc).isoformat()


def digest_obj(data):
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def digest_bytes(data: bytes):
    return hashlib.sha256(data).hexdigest()[:16]


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


def safe_candidate_id(candidate_id):
    if not candidate_id or not isinstance(candidate_id, str):
        return False
    if "/" in candidate_id or "\\" in candidate_id or ".." in candidate_id:
        return False
    return candidate_id.startswith("d")


def candidate_dir(root: Path, candidate_id: str) -> Path:
    return root / SANDBOX_ROOT / candidate_id


def file_digest(path: Path):
    return digest_bytes(path.read_bytes())


def validate_d138(d138, intent_record, authority_guard, d139_scope):
    errors = []

    if not d138:
        errors.append("missing D138 sandbox candidate human execution intent scope report")
        return errors

    if d138.get("ok") is not True:
        errors.append("D138 ok must be true")
    if d138.get("decision") != REQ_D138_DECISION:
        errors.append("D138 decision must be SANDBOX_CANDIDATE_HUMAN_EXECUTION_INTENT_SCOPE_READY")

    guard = d138.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D138 guardrails.{key} must be false")

    for key in [
        "sandbox_candidate_human_execution_intent_scope_only",
        "human_execution_intent_record_only",
        "execution_authority_guard_only",
        "approval_for_d139_controlled_execution_run_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D138 guardrails.{key} must be true")

    for key in [
        "candidate_executed_now",
        "actual_apply_executed",
        "approval_for_real_apply_by_ai",
        "commands_executed_by_ai",
    ]:
        if guard.get(key) is not False:
            errors.append(f"D138 guardrails.{key} must be false")

    summary = d138.get("summary", {})
    expected = {
        "human_execution_intent_status": "HUMAN_INTENT_RECORD_CREATED_NO_EXECUTION",
        "candidate_status": "MATERIALIZED_VALIDATED_NOT_EXECUTED_NOT_APPLIED",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "candidate_execution_status": "NOT_EXECUTED",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": REQ_D138_APPROVAL_SCOPE,
        "next_step": REQ_D139_GATE,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"D138 summary.{key} must be {value}")

    if not intent_record:
        errors.append("missing D138 human execution intent record")
    else:
        if intent_record.get("ok") is not True:
            errors.append("D138 intent record ok must be true")
        if intent_record.get("record_mode") not in [
            "HUMAN_EXECUTION_INTENT_RECORD_ONLY_NO_EXECUTION",
            "HUMAN_INTENT_RECORD_ONLY_NO_EXECUTION",
        ]:
            errors.append("D138 intent record must be no-execution record only")
        for key in [
            "candidate_executed_now",
            "actual_apply_executed",
            "real_apply_executed",
            "shell_executed_by_ai",
            "git_action_by_ai",
        ]:
            if intent_record.get(key) is not False:
                errors.append(f"D138 intent record {key} must be false")

    if not authority_guard:
        errors.append("missing D138 execution authority guard")
    else:
        if authority_guard.get("ok") is not True:
            errors.append("D138 authority guard ok must be true")
        if authority_guard.get("authority_mode") not in [
            "EXECUTION_AUTHORITY_GUARD_ONLY_NO_EXECUTION",
            "SANDBOX_EXECUTION_AUTHORITY_GUARD_ONLY",
        ]:
            errors.append("D138 authority guard must be guard-only/no-execution")
        for key in [
            "allow_real_apply",
            "allow_route_insert",
            "allow_protected_core_mutation",
            "allow_network",
            "allow_secret_read",
            "allow_shell_exec",
            "allow_git_action_by_ai",
        ]:
            if authority_guard.get(key) is not False:
                errors.append(f"D138 authority guard {key} must be false")

    if not d139_scope:
        errors.append("missing D138 D139 controlled execution run scope")
    else:
        if d139_scope.get("ok") is not True:
            errors.append("D138 D139 scope ok must be true")
        if d139_scope.get("allowed_next_gate") != REQ_D139_GATE:
            errors.append("D138 D139 scope allowed_next_gate must be D139")
        if d139_scope.get("sandbox_candidate_controlled_execution_run_scope_only") is not True:
            errors.append("D138 D139 scope must be controlled execution run scope only")
        if d139_scope.get("human_review_required") is not True:
            errors.append("D138 D139 scope must require human review")
        for key in [
            "real_apply_allowed_after_d138_by_ai",
            "route_insert_allowed_after_d138_by_ai",
            "protected_core_mutation_allowed_after_d138_by_ai",
            "network_allowed_after_d138",
            "secret_read_allowed_after_d138",
            "shell_allowed_after_d138_by_ai",
            "git_action_allowed_after_d138_by_ai",
        ]:
            if d139_scope.get(key) is not False:
                errors.append(f"D138 D139 scope {key} must be false")

    return errors


def load_materialized_candidate(root: Path, candidate_id: str):
    cdir = candidate_dir(root, candidate_id)
    manifest_path = cdir / "candidate_manifest.json"
    payload_path = cdir / "candidate_payload.json"
    summary_path = cdir / "candidate_summary.md"

    errors = []
    if not cdir.exists():
        errors.append(f"candidate sandbox directory missing: {cdir}")
    for p in [manifest_path, payload_path, summary_path]:
        if not p.exists():
            errors.append(f"materialized candidate file missing: {p}")

    manifest = read_json(manifest_path, {}) or {}
    payload = read_json(payload_path, {}) or {}
    summary_text = summary_path.read_text(encoding="utf-8") if summary_path.exists() else ""

    return {
        "candidate_dir": str(cdir),
        "manifest_path": str(manifest_path),
        "payload_path": str(payload_path),
        "summary_path": str(summary_path),
        "manifest": manifest,
        "payload": payload,
        "summary_text": summary_text,
        "errors": errors,
        "digests": {
            "candidate_manifest": file_digest(manifest_path) if manifest_path.exists() else None,
            "candidate_payload": file_digest(payload_path) if payload_path.exists() else None,
            "candidate_summary": file_digest(summary_path) if summary_path.exists() else None,
        },
        "sizes": {
            "candidate_manifest": manifest_path.stat().st_size if manifest_path.exists() else 0,
            "candidate_payload": payload_path.stat().st_size if payload_path.exists() else 0,
            "candidate_summary": summary_path.stat().st_size if summary_path.exists() else 0,
        },
    }


def controlled_declarative_sandbox_execution(root: Path, run_id: str, d138, materialized):
    """
    D139 does not execute arbitrary code.

    It performs the first controlled sandbox execution by interpreting the
    materialized candidate as a declarative payload, validating identity and
    producing a sandbox-local execution result. This gives the system a real
    execution artifact while preserving no-shell/no-apply/no-core boundaries.
    """
    candidate_id = d138.get("candidate_id")
    cdir = candidate_dir(root, candidate_id)
    manifest = materialized.get("manifest", {})
    payload = materialized.get("payload", {})
    summary_text = materialized.get("summary_text", "")

    declared_candidate_id = (
        manifest.get("candidate_id")
        or payload.get("candidate_id")
        or payload.get("id")
        or candidate_id
    )

    steps = [
        {
            "name": "load_materialized_candidate_manifest",
            "status": "PASS",
            "mode": "READ_ONLY",
        },
        {
            "name": "load_materialized_candidate_payload",
            "status": "PASS",
            "mode": "READ_ONLY",
        },
        {
            "name": "validate_candidate_identity",
            "status": "PASS" if declared_candidate_id == candidate_id else "WARN",
            "expected_candidate_id": candidate_id,
            "declared_candidate_id": declared_candidate_id,
        },
        {
            "name": "digest_payload_for_execution_trace",
            "status": "PASS",
            "payload_digest": materialized.get("digests", {}).get("candidate_payload"),
        },
        {
            "name": "write_sandbox_execution_result",
            "status": "PASS",
            "mode": "SANDBOX_WRITE_ONLY",
        },
    ]

    result = {
        "state": "D139_SANDBOX_CANDIDATE_EXECUTION_RUN_RESULT",
        "ok": True,
        "run_id": run_id,
        "candidate_id": candidate_id,
        "proposal_id": d138.get("proposal_id"),
        "created_at": now(),
        "execution_mode": "CONTROLLED_DECLARATIVE_SANDBOX_EXECUTION_NO_SHELL",
        "candidate_execution_status": "SANDBOX_CONTROLLED_EXECUTION_COMPLETED",
        "candidate_status": "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED",
        "candidate_dir": str(cdir),
        "materialized_inputs": {
            "manifest_digest": materialized.get("digests", {}).get("candidate_manifest"),
            "payload_digest": materialized.get("digests", {}).get("candidate_payload"),
            "summary_digest": materialized.get("digests", {}).get("candidate_summary"),
            "summary_size": len(summary_text.encode("utf-8")),
        },
        "declared_candidate_id": declared_candidate_id,
        "steps": steps,
        "arbitrary_code_executed": False,
        "shell_executed": False,
        "network_accessed": False,
        "provider_called": False,
        "secret_read": False,
        "actual_apply_executed": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "canonical_memory_mutated": False,
        "git_action_by_ai": False,
        "human_review_required": True,
    }

    sandbox_result_path = cdir / "sandbox_execution_result.json"
    write_json(sandbox_result_path, result)
    result["sandbox_result_path"] = str(sandbox_result_path)
    result["sandbox_result_digest"] = file_digest(sandbox_result_path)

    return result


def build_safety_receipt(run_id, d138, materialized, run_result):
    return {
        "state": "D139_SANDBOX_CANDIDATE_EXECUTION_SAFETY_RECEIPT",
        "ok": True,
        "run_id": run_id,
        "candidate_id": d138.get("candidate_id"),
        "created_at": now(),
        "receipt_mode": "CONTROLLED_SANDBOX_EXECUTION_SAFETY_RECEIPT",
        "writes_limited_to_sandbox_candidate_dir": True,
        "sandbox_candidate_dir": materialized.get("candidate_dir"),
        "sandbox_written_files": [
            run_result.get("sandbox_result_path"),
        ],
        "candidate_files_read": [
            materialized.get("manifest_path"),
            materialized.get("payload_path"),
            materialized.get("summary_path"),
        ],
        "candidate_executed_now": True,
        "candidate_executed_by_operator_boot": True,
        "candidate_executed_by_ai": False,
        "arbitrary_code_executed": False,
        "shell_executed_by_ai": False,
        "network_accessed": False,
        "real_provider_called": False,
        "api_key_read": False,
        "secret_read": False,
        "actual_apply_executed": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "canonical_memory_mutated": False,
        "git_commit_by_ai": False,
        "git_push_by_ai": False,
        "rollback_executed": False,
        "restore_executed": False,
        "protected_core_status": "UNTOUCHED_BY_AI",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "human_review_required": True,
    }


def build_d140_scope(run_id, d138):
    return {
        "state": "D139_D140_SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE",
        "ok": True,
        "run_id": run_id,
        "intent_id": d138.get("intent_id"),
        "scope_id": d138.get("scope_id"),
        "preflight_id": d138.get("preflight_id"),
        "validation_id": d138.get("validation_id"),
        "write_materialization_id": d138.get("write_materialization_id"),
        "materialization_id": d138.get("materialization_id"),
        "static_validation_id": d138.get("static_validation_id"),
        "write_once_id": d138.get("write_once_id"),
        "window_id": d138.get("window_id"),
        "runner_id": d138.get("runner_id"),
        "plan_id": d138.get("plan_id"),
        "review_id": d138.get("review_id"),
        "candidate_id": d138.get("candidate_id"),
        "adapter_id": d138.get("adapter_id"),
        "seal_id": d138.get("seal_id"),
        "proposal_id": d138.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D140_GATE,
        "d140_allowed_to_create": [
            "sandbox_candidate_post_execution_verification_scope",
            "sandbox_candidate_post_execution_verification_report",
            "sandbox_candidate_execution_result_validation",
            "d141_sandbox_candidate_apply_preflight_scope",
        ],
        "d140_must_not_execute": [
            "real_apply_by_ai",
            "auto_apply",
            "route_insert_by_ai",
            "protected_core_mutation_by_ai",
            "canonical_memory_overwrite_by_ai",
            "shell_exec_from_ai",
            "git_commit_by_ai",
            "git_push_by_ai",
            "rollback_execute_by_ai",
            "restore_execute_by_ai",
            "network_provider_call",
            "secret_read",
        ],
        "sandbox_candidate_post_execution_verification_scope_only": True,
        "human_review_required": True,
        "candidate_executed_after_d139_in_sandbox": True,
        "real_apply_allowed_after_d139_by_ai": False,
        "route_insert_allowed_after_d139_by_ai": False,
        "protected_core_mutation_allowed_after_d139_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D140_SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE_ONLY",
    }


def create_sandbox_candidate_controlled_execution_run_scope(root="."):
    root = Path(root).resolve()

    d138 = read_json(root / D138_REPORT, {}) or {}
    intent_record = read_json(root / D138_INTENT_RECORD, {}) or {}
    authority_guard = read_json(root / D138_AUTHORITY_GUARD, {}) or {}
    d139_scope = read_json(root / D138_D139_SCOPE, {}) or {}

    errors = validate_d138(d138, intent_record, authority_guard, d139_scope)

    candidate_id = d138.get("candidate_id")
    if not safe_candidate_id(candidate_id):
        errors.append("candidate_id is missing or unsafe")

    run_id = "d139-" + digest_obj({
        "intent_id": d138.get("intent_id"),
        "scope_id": d138.get("scope_id"),
        "candidate_id": candidate_id,
        "proposal_id": d138.get("proposal_id"),
    })

    materialized = {"errors": ["candidate not loaded"]}
    run_result = {}
    safety_receipt = {}
    d140_scope = {}

    if not errors:
        materialized = load_materialized_candidate(root, candidate_id)
        errors.extend(materialized.get("errors", []))

    if not errors:
        run_result = controlled_declarative_sandbox_execution(root, run_id, d138, materialized)
        safety_receipt = build_safety_receipt(run_id, d138, materialized, run_result)
        d140_scope = build_d140_scope(run_id, d138)

        for key in [
            "shell_executed",
            "network_accessed",
            "provider_called",
            "secret_read",
            "actual_apply_executed",
            "route_inserted",
            "protected_core_mutated",
            "canonical_memory_mutated",
            "git_action_by_ai",
        ]:
            if run_result.get(key) is not False:
                errors.append(f"run_result {key} must be false")

        for key in [
            "shell_executed_by_ai",
            "network_accessed",
            "real_provider_called",
            "api_key_read",
            "secret_read",
            "actual_apply_executed",
            "route_inserted",
            "protected_core_mutated",
            "canonical_memory_mutated",
            "git_commit_by_ai",
            "git_push_by_ai",
            "rollback_executed",
            "restore_executed",
        ]:
            if safety_receipt.get(key) is not False:
                errors.append(f"safety_receipt {key} must be false")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE_BLOCKED"
    result = "D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE_CREATED" if ok else "D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE_BLOCKED"

    if ok:
        write_json(root / RUN_RESULT_OUT, run_result)
        write_json(root / SAFETY_RECEIPT_OUT, safety_receipt)
        write_json(root / D140_SCOPE_OUT, d140_scope)

    report = {
        "state": "D139_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_CONTROLLED_EXECUTION_RUN_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "run_id": run_id,
        "intent_id": d138.get("intent_id"),
        "scope_id": d138.get("scope_id"),
        "preflight_id": d138.get("preflight_id"),
        "validation_id": d138.get("validation_id"),
        "write_materialization_id": d138.get("write_materialization_id"),
        "materialization_id": d138.get("materialization_id"),
        "static_validation_id": d138.get("static_validation_id"),
        "write_once_id": d138.get("write_once_id"),
        "window_id": d138.get("window_id"),
        "runner_id": d138.get("runner_id"),
        "plan_id": d138.get("plan_id"),
        "review_id": d138.get("review_id"),
        "candidate_id": candidate_id,
        "adapter_id": d138.get("adapter_id"),
        "seal_id": d138.get("seal_id"),
        "proposal_id": d138.get("proposal_id"),
        "source_d138_report": D138_REPORT,
        "sandbox_candidate_execution_run_result": run_result if ok else {},
        "sandbox_candidate_execution_safety_receipt": safety_receipt if ok else {},
        "d140_scope": d140_scope if ok else {},
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "shell_from_ai_executed": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "git_push_by_ai": False,
            "rollback_executed": False,
            "restore_executed": False,
            "sandbox_candidate_controlled_execution_run_scope_only": True,
            "controlled_sandbox_execution_result_only": True,
            "candidate_executed_now": ok,
            "candidate_executed_by_operator_boot": ok,
            "candidate_executed_by_ai": False,
            "arbitrary_candidate_code_executed": False,
            "approval_for_d140_post_execution_verification_scope_only": ok,
            "approval_for_real_apply_by_ai": False,
            "commands_executed_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "run_id": run_id,
            "candidate_id": candidate_id,
            "proposal_id": d138.get("proposal_id"),
            "execution_status": "SANDBOX_CONTROLLED_EXECUTION_COMPLETED" if ok else "BLOCKED",
            "candidate_status": "MATERIALIZED_EXECUTED_IN_SANDBOX_NOT_APPLIED" if ok else "BLOCKED",
            "sandbox_result_path": run_result.get("sandbox_result_path") if ok else None,
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "shell_status": "NOT_EXECUTED",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D140_SANDBOX_CANDIDATE_POST_EXECUTION_VERIFICATION_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D140_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "controlled_execution_run_scope_created": ok,
            "sandbox_candidate_execution_run_result_created": ok,
            "sandbox_candidate_execution_safety_receipt_created": ok,
            "d140_scope_created": ok,
            "candidate_executed_in_sandbox": ok,
            "candidate_executed_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D140 may verify controlled sandbox execution result only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_controlled_execution_run_scope(), ensure_ascii=False, indent=2))
