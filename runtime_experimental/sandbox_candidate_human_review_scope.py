
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D126_REPORT = "reports/d126_proposal_to_sandbox_candidate_scope.json"
D126_WRITE_PLAN = "reports/d126_sandbox_candidate_write_plan.json"
D126_STATIC_SCAN = "reports/d126_sandbox_candidate_static_scan.json"
D126_D127_SCOPE = "reports/d126_d127_sandbox_candidate_human_review_scope.json"

OUT = "reports/d127_sandbox_candidate_human_review_scope.json"
REVIEW_PACKET_OUT = "reports/d127_sandbox_candidate_review_packet.json"
APPROVAL_RECORD_OUT = "reports/d127_sandbox_candidate_approval_or_rejection_record.json"
D128_SCOPE_OUT = "reports/d127_d128_sandbox_candidate_test_plan_scope.json"

REQ_D126_DECISION = "PROPOSAL_TO_SANDBOX_CANDIDATE_SCOPE_READY"
REQ_D127_GATE = "D127_SANDBOX_CANDIDATE_HUMAN_REVIEW_SCOPE"
REQ_D128_GATE = "D128_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE"
REQ_D126_APPROVAL_SCOPE = "D127_SANDBOX_CANDIDATE_HUMAN_REVIEW_SCOPE_ONLY"

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

BLOCKED_PREFIXES = [
    "app/orchestration/",
    "core/",
    "runtime/",
    "bridges/",
    "memory/",
]


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


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


def validate_d126(d126, write_plan, static_scan, d127_scope):
    errors = []

    if not d126:
        errors.append("missing D126 proposal to sandbox candidate scope report")
        return errors

    if d126.get("ok") is not True:
        errors.append("D126 ok must be true")
    if d126.get("decision") != REQ_D126_DECISION:
        errors.append("D126 decision must be PROPOSAL_TO_SANDBOX_CANDIDATE_SCOPE_READY")

    guard = d126.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D126 guardrails.{key} must be false")
    for key in [
        "proposal_to_sandbox_candidate_scope_only",
        "sandbox_write_plan_only",
        "static_scan_only",
        "approval_for_d127_human_review_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D126 guardrails.{key} must be true")
    for key in [
        "candidate_files_written_now",
        "candidate_executed_now",
        "approval_for_real_apply_by_ai",
        "candidate_execution_allowed_by_ai",
        "commands_executed_by_ai",
    ]:
        if guard.get(key) is not False:
            errors.append(f"D126 guardrails.{key} must be false")

    summary = d126.get("summary", {})
    if summary.get("sandbox_candidate_status") != "PLAN_CREATED_NOT_WRITTEN_NOT_EXECUTED":
        errors.append("D126 sandbox_candidate_status must be PLAN_CREATED_NOT_WRITTEN_NOT_EXECUTED")
    if summary.get("static_scan_status") != "PASS":
        errors.append("D126 static_scan_status must be PASS")
    if summary.get("real_provider_status") != "NOT_CALLED":
        errors.append("D126 real_provider_status must be NOT_CALLED")
    if summary.get("network_status") != "NOT_ACCESSED":
        errors.append("D126 network_status must be NOT_ACCESSED")
    if summary.get("secret_status") != "NOT_READ":
        errors.append("D126 secret_status must be NOT_READ")
    if summary.get("real_apply_by_ai_status") != "BLOCKED":
        errors.append("D126 real_apply_by_ai_status must be BLOCKED")
    if summary.get("approval_scope") != REQ_D126_APPROVAL_SCOPE:
        errors.append("D126 approval_scope must be D127 human review scope only")
    if summary.get("next_step") != REQ_D127_GATE:
        errors.append("D126 next_step must be D127")

    if not write_plan:
        errors.append("missing D126 sandbox candidate write plan")
    else:
        if write_plan.get("ok") is not True:
            errors.append("D126 write plan ok must be true")
        if write_plan.get("plan_mode") != "SANDBOX_CANDIDATE_PLAN_ONLY_NO_EXECUTION":
            errors.append("D126 write plan mode must be sandbox plan only")
        if write_plan.get("human_review_required") is not True:
            errors.append("D126 write plan must require human review")
        for key in [
            "candidate_files_written_now",
            "candidate_executed_now",
            "actual_apply_executed",
            "shell_executed_by_ai",
            "git_action_by_ai",
        ]:
            if write_plan.get(key) is not False:
                errors.append(f"D126 write plan {key} must be false")
        for item in write_plan.get("planned_files", []):
            path = item.get("path", "")
            if any(str(path).startswith(prefix) for prefix in BLOCKED_PREFIXES):
                errors.append(f"D126 planned file hits blocked prefix: {path}")

    if not static_scan:
        errors.append("missing D126 sandbox candidate static scan")
    else:
        if static_scan.get("ok") is not True:
            errors.append("D126 static scan ok must be true")
        if static_scan.get("scan_mode") != "STATIC_PLAN_SCAN_ONLY_NO_EXECUTION":
            errors.append("D126 static scan mode must be static plan scan only")
        if static_scan.get("allowed_prefixes_ok") is not True:
            errors.append("D126 static scan allowed_prefixes_ok must be true")
        if static_scan.get("blocked_prefix_hits") not in ([], None):
            errors.append("D126 static scan blocked_prefix_hits must be empty")
        if static_scan.get("forbidden_marker_hits") not in ([], None):
            errors.append("D126 static scan forbidden_marker_hits must be empty")
        if static_scan.get("errors") not in ([], None):
            errors.append("D126 static scan errors must be empty")
        for key in [
            "candidate_files_written_now",
            "candidate_executed_now",
            "actual_apply_executed",
            "shell_executed_by_ai",
            "git_action_by_ai",
        ]:
            if static_scan.get(key) is not False:
                errors.append(f"D126 static scan {key} must be false")

    if not d127_scope:
        errors.append("missing D126 D127 sandbox candidate human review scope")
    else:
        if d127_scope.get("ok") is not True:
            errors.append("D126 D127 scope ok must be true")
        if d127_scope.get("allowed_next_gate") != REQ_D127_GATE:
            errors.append("D126 D127 scope allowed_next_gate must be D127")
        if d127_scope.get("sandbox_candidate_human_review_scope_only") is not True:
            errors.append("D126 D127 scope sandbox_candidate_human_review_scope_only must be true")
        if d127_scope.get("human_review_required") is not True:
            errors.append("D126 D127 scope must require human review")
        if d127_scope.get("static_scan_ok") is not True:
            errors.append("D126 D127 scope static_scan_ok must be true")
        for key in [
            "candidate_written_after_d126",
            "candidate_executed_after_d126_by_ai",
            "real_apply_allowed_after_d126_by_ai",
            "route_insert_allowed_after_d126_by_ai",
            "protected_core_mutation_allowed_after_d126_by_ai",
        ]:
            if d127_scope.get(key) is not False:
                errors.append(f"D126 D127 scope {key} must be false")

    return errors


def build_review_packet(review_id, d126, write_plan, static_scan):
    return {
        "state": "D127_SANDBOX_CANDIDATE_REVIEW_PACKET",
        "ok": True,
        "review_id": review_id,
        "candidate_id": d126.get("candidate_id"),
        "intake_id": d126.get("intake_id"),
        "ping_id": d126.get("ping_id"),
        "config_id": d126.get("config_id"),
        "dashboard_id": d126.get("dashboard_id"),
        "adapter_id": d126.get("adapter_id"),
        "seal_id": d126.get("seal_id"),
        "proposal_id": d126.get("proposal_id"),
        "created_at": now(),
        "packet_mode": "HUMAN_REVIEW_PACKET_ONLY_NO_EXECUTION",
        "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
        "write_plan_reference": D126_WRITE_PLAN,
        "static_scan_reference": D126_STATIC_SCAN,
        "candidate_root": write_plan.get("candidate_root"),
        "planned_files": write_plan.get("planned_files", []),
        "static_scan_ok": static_scan.get("ok") is True,
        "review_questions": [
            "Does the sandbox candidate stay inside allowed sandbox/report/test/doc scope?",
            "Does the plan avoid protected core/runtime/memory/route mutation?",
            "Does the plan avoid shell, network, secret, apply, rollback, restore, and git actions?",
            "Is it safe to proceed to D128 test-plan scope only?",
        ],
        "candidate_files_written_now": False,
        "candidate_executed_now": False,
        "actual_apply_executed": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "human_review_required": True,
    }


def build_approval_record(review_id, d126):
    return {
        "state": "D127_SANDBOX_CANDIDATE_APPROVAL_OR_REJECTION_RECORD",
        "ok": True,
        "review_id": review_id,
        "candidate_id": d126.get("candidate_id"),
        "proposal_id": d126.get("proposal_id"),
        "created_at": now(),
        "record_mode": "REVIEW_RECORD_TEMPLATE_ONLY",
        "operator_decision": "PENDING_HUMAN_REVIEW",
        "approved_for_d128_test_plan_scope_now": True,
        "approved_for_candidate_execution": False,
        "approved_for_real_apply": False,
        "approved_for_route_insert": False,
        "approved_for_protected_core_mutation": False,
        "approved_for_git_action_by_ai": False,
        "required_phrase_for_d128": "APPROVE_D128_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE_ONLY",
        "human_review_required": True,
    }


def build_d128_scope(review_id, d126):
    return {
        "state": "D127_D128_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE",
        "ok": True,
        "review_id": review_id,
        "candidate_id": d126.get("candidate_id"),
        "intake_id": d126.get("intake_id"),
        "ping_id": d126.get("ping_id"),
        "config_id": d126.get("config_id"),
        "dashboard_id": d126.get("dashboard_id"),
        "adapter_id": d126.get("adapter_id"),
        "seal_id": d126.get("seal_id"),
        "proposal_id": d126.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D128_GATE,
        "d128_allowed_to_create": [
            "sandbox_candidate_test_plan_scope",
            "sandbox_candidate_test_matrix",
            "sandbox_candidate_no_touch_assertions",
            "d129_sandbox_candidate_dry_test_runner_scope",
        ],
        "d128_must_not_execute": [
            "execute_sandbox_candidate_by_ai",
            "commit_sandbox_candidate_by_ai",
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
        ],
        "sandbox_candidate_test_plan_scope_only": True,
        "human_review_required": True,
        "candidate_written_after_d127": False,
        "candidate_executed_after_d127_by_ai": False,
        "real_apply_allowed_after_d127_by_ai": False,
        "route_insert_allowed_after_d127_by_ai": False,
        "protected_core_mutation_allowed_after_d127_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D128_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE_ONLY",
    }


def create_sandbox_candidate_human_review_scope(root="."):
    root = Path(root).resolve()

    d126 = read_json(root / D126_REPORT, {}) or {}
    write_plan = read_json(root / D126_WRITE_PLAN, {}) or {}
    static_scan = read_json(root / D126_STATIC_SCAN, {}) or {}
    d127_scope = read_json(root / D126_D127_SCOPE, {}) or {}

    errors = validate_d126(d126, write_plan, static_scan, d127_scope)

    review_id = "d127-" + digest({
        "candidate_id": d126.get("candidate_id"),
        "intake_id": d126.get("intake_id"),
        "adapter_id": d126.get("adapter_id"),
        "proposal_id": d126.get("proposal_id"),
    })

    review_packet = build_review_packet(review_id, d126, write_plan, static_scan)
    approval_record = build_approval_record(review_id, d126)
    d128_scope = build_d128_scope(review_id, d126)

    for item_name, item in [("review_packet", review_packet)]:
        for key in [
            "candidate_files_written_now",
            "candidate_executed_now",
            "actual_apply_executed",
            "shell_executed_by_ai",
            "git_action_by_ai",
        ]:
            if item.get(key) is not False:
                errors.append(f"{item_name} {key} must be false")

    for key in [
        "approved_for_candidate_execution",
        "approved_for_real_apply",
        "approved_for_route_insert",
        "approved_for_protected_core_mutation",
        "approved_for_git_action_by_ai",
    ]:
        if approval_record.get(key) is not False:
            errors.append(f"approval record {key} must be false")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_HUMAN_REVIEW_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_HUMAN_REVIEW_SCOPE_BLOCKED"
    result = "D127_SANDBOX_CANDIDATE_HUMAN_REVIEW_SCOPE_CREATED" if ok else "D127_SANDBOX_CANDIDATE_HUMAN_REVIEW_SCOPE_BLOCKED"

    if ok:
        write_json(root / REVIEW_PACKET_OUT, review_packet)
        write_json(root / APPROVAL_RECORD_OUT, approval_record)
        write_json(root / D128_SCOPE_OUT, d128_scope)

    report = {
        "state": "D127_SANDBOX_CANDIDATE_HUMAN_REVIEW_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_HUMAN_REVIEW_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "review_id": review_id,
        "candidate_id": d126.get("candidate_id"),
        "intake_id": d126.get("intake_id"),
        "ping_id": d126.get("ping_id"),
        "config_id": d126.get("config_id"),
        "dashboard_id": d126.get("dashboard_id"),
        "adapter_id": d126.get("adapter_id"),
        "seal_id": d126.get("seal_id"),
        "proposal_id": d126.get("proposal_id"),
        "source_d126_report": D126_REPORT,
        "sandbox_candidate_review_packet": review_packet if ok else {},
        "sandbox_candidate_approval_or_rejection_record": approval_record if ok else {},
        "d128_scope": d128_scope if ok else {},
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
            "sandbox_candidate_human_review_scope_only": True,
            "review_packet_only": True,
            "approval_record_template_only": True,
            "candidate_files_written_now": False,
            "candidate_executed_now": False,
            "approval_for_d128_test_plan_scope_only": ok,
            "approval_for_candidate_execution": False,
            "approval_for_real_apply_by_ai": False,
            "candidate_execution_allowed_by_ai": False,
            "commands_executed_by_ai": False,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": [],
        },
        "summary": {
            "decision": decision,
            "review_id": review_id,
            "candidate_id": d126.get("candidate_id"),
            "intake_id": d126.get("intake_id"),
            "adapter_id": d126.get("adapter_id"),
            "seal_id": d126.get("seal_id"),
            "proposal_id": d126.get("proposal_id"),
            "review_status": "PENDING_HUMAN_REVIEW_PACKET_CREATED" if ok else "BLOCKED",
            "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
            "static_scan_status": "PASS" if static_scan.get("ok") is True else "FAIL",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "real_apply_by_ai_status": "BLOCKED",
            "approval_scope": "D128_SANDBOX_CANDIDATE_TEST_PLAN_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D128_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_human_review_scope_created": ok,
            "sandbox_candidate_review_packet_created": ok,
            "approval_or_rejection_record_created": ok,
            "d128_scope_created": ok,
            "candidate_files_written": False,
            "candidate_executed_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D128 may create sandbox candidate test plan scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_human_review_scope(), ensure_ascii=False, indent=2))
