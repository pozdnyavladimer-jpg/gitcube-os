
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D133_REPORT = "reports/d133_sandbox_candidate_materialization_scope.json"
D133_MATERIALIZATION_MANIFEST = "reports/d133_sandbox_candidate_materialization_manifest.json"
D133_MATERIALIZATION_PREFLIGHT = "reports/d133_sandbox_candidate_materialization_preflight.json"
D133_D134_SCOPE = "reports/d133_d134_sandbox_candidate_write_materialization_scope.json"

OUT = "reports/d134_sandbox_candidate_write_materialization_scope.json"
WRITE_RECEIPT_OUT = "reports/d134_sandbox_candidate_write_materialization_receipt.json"
WRITE_POSTCHECK_OUT = "reports/d134_sandbox_candidate_write_materialization_postcheck.json"
D135_SCOPE_OUT = "reports/d134_d135_sandbox_candidate_post_write_validation_scope.json"

REQ_D133_DECISION = "SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE_READY"
REQ_D134_GATE = "D134_SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_SCOPE"
REQ_D135_GATE = "D135_SANDBOX_CANDIDATE_POST_WRITE_VALIDATION_SCOPE"
REQ_D133_APPROVAL_SCOPE = "D134_SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_SCOPE_ONLY"

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

PROTECTED_TARGETS = [
    "app/orchestration/",
    "core/",
    "runtime/",
    "bridges/",
    "memory/",
]

EXPECTED_CANDIDATE_FILENAMES = [
    "candidate_manifest.json",
    "candidate_summary.md",
    "candidate_payload.json",
]


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def text_digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


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


def is_safe_candidate_root(root_value):
    return (
        isinstance(root_value, str)
        and root_value.startswith("runtime_experimental/ai_sandbox_work/")
        and root_value.endswith("/")
        and ".." not in root_value
        and not root_value.startswith("/")
    )


def is_safe_candidate_path(path_value, root_value):
    return (
        isinstance(path_value, str)
        and isinstance(root_value, str)
        and path_value.startswith(root_value)
        and ".." not in path_value
        and not path_value.startswith("/")
        and not path_value.endswith("/")
    )


def expected_candidate_paths(root_value):
    return [f"{root_value}{name}" for name in EXPECTED_CANDIDATE_FILENAMES]


def planned_paths_from_manifest(materialization_manifest):
    planned = materialization_manifest.get("planned_materialization_files", [])
    return [path for path in planned if isinstance(path, str)]


def validate_d133(d133, materialization_manifest, materialization_preflight, d134_scope):
    errors = []

    if not d133:
        errors.append("missing D133 sandbox candidate materialization scope report")
        return errors

    if d133.get("ok") is not True:
        errors.append("D133 ok must be true")
    if d133.get("decision") != REQ_D133_DECISION:
        errors.append("D133 decision must be SANDBOX_CANDIDATE_MATERIALIZATION_SCOPE_READY")

    guard = d133.get("guardrails", {})
    for key in FALSE_GUARD_KEYS:
        if guard.get(key) is not False:
            errors.append(f"D133 guardrails.{key} must be false")

    for key in [
        "sandbox_candidate_materialization_scope_only",
        "materialization_manifest_only",
        "materialization_preflight_only",
        "approval_for_d134_write_materialization_scope_only",
    ]:
        if guard.get(key) is not True:
            errors.append(f"D133 guardrails.{key} must be true")

    for key in [
        "candidate_files_written_now",
        "candidate_executed_now",
        "approval_for_candidate_execution",
        "approval_for_real_apply_by_ai",
        "candidate_execution_allowed_by_ai",
        "commands_executed_by_ai",
    ]:
        if guard.get(key) is not False:
            errors.append(f"D133 guardrails.{key} must be false")

    summary = d133.get("summary", {})
    expected = {
        "materialization_status": "MATERIALIZATION_SCOPE_DECLARED_NOT_WRITTEN",
        "materialization_preflight_status": "MATERIALIZATION_PREFLIGHT_PASS_NO_WRITE",
        "candidate_status": "PLANNED_ONLY_NOT_WRITTEN_NOT_EXECUTED",
        "real_provider_status": "NOT_CALLED",
        "network_status": "NOT_ACCESSED",
        "secret_status": "NOT_READ",
        "real_apply_by_ai_status": "BLOCKED",
        "route_insert_status": "BLOCKED",
        "protected_core_status": "UNTOUCHED_BY_AI",
        "approval_scope": REQ_D133_APPROVAL_SCOPE,
        "next_step": REQ_D134_GATE,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"D133 summary.{key} must be {value}")

    if not materialization_manifest:
        errors.append("missing D133 sandbox candidate materialization manifest")
    else:
        if materialization_manifest.get("ok") is not True:
            errors.append("D133 materialization manifest ok must be true")
        if materialization_manifest.get("manifest_mode") != "MATERIALIZATION_MANIFEST_ONLY_NO_CANDIDATE_WRITE":
            errors.append("D133 materialization manifest mode must be no-write")
        if materialization_manifest.get("materialization_status") != "MATERIALIZATION_SCOPE_DECLARED_NOT_WRITTEN":
            errors.append("D133 materialization manifest status must be declared-not-written")
        root_value = materialization_manifest.get("allowed_candidate_write_root")
        if not is_safe_candidate_root(root_value):
            errors.append("D133 materialization manifest root must be safe")
        planned = planned_paths_from_manifest(materialization_manifest)
        expected_paths = expected_candidate_paths(root_value) if is_safe_candidate_root(root_value) else []
        if sorted(planned) != sorted(expected_paths):
            errors.append("D133 materialization manifest must contain exactly the expected candidate files")
        for path in planned:
            if not is_safe_candidate_path(path, root_value):
                errors.append("D133 planned materialization file must stay inside candidate root")
        policy = materialization_manifest.get("materialization_policy", {})
        for key in [
            "static_validation_required",
            "path_boundary_required",
            "candidate_root_only",
            "write_materialization_next_gate_only",
            "single_materialization_attempt",
            "no_overwrite_existing_candidate_files",
            "no_execution_after_materialization",
            "no_apply_after_materialization",
            "no_route_insert_after_materialization",
            "human_review_required",
        ]:
            if policy.get(key) is not True:
                errors.append(f"D133 materialization policy {key} must be true")
        for key in [
            "candidate_files_written_now",
            "candidate_executed_now",
            "actual_apply_executed",
            "route_inserted",
            "protected_core_mutated",
            "canonical_memory_mutated",
            "shell_executed_by_ai",
            "git_action_by_ai",
            "network_accessed",
            "api_key_read",
            "secret_read",
        ]:
            if materialization_manifest.get(key) is not False:
                errors.append(f"D133 materialization manifest {key} must be false")

    if not materialization_preflight:
        errors.append("missing D133 sandbox candidate materialization preflight")
    else:
        if materialization_preflight.get("ok") is not True:
            errors.append("D133 materialization preflight ok must be true")
        if materialization_preflight.get("preflight_mode") != "MATERIALIZATION_PREFLIGHT_ONLY_NO_FILESYSTEM_WRITE":
            errors.append("D133 materialization preflight mode must be no-filesystem-write")
        if materialization_preflight.get("preflight_status") != "MATERIALIZATION_PREFLIGHT_PASS_NO_WRITE":
            errors.append("D133 materialization preflight status must be pass-no-write")
        root_value = materialization_preflight.get("allowed_candidate_write_root")
        if not is_safe_candidate_root(root_value):
            errors.append("D133 materialization preflight root must be safe")
        checks = materialization_preflight.get("checks", {})
        for key in [
            "d132_static_validation_scope_ready",
            "static_validation_report_passed",
            "path_boundary_report_passed",
            "candidate_root_safe",
            "planned_files_present",
            "planned_paths_under_candidate_root",
            "no_blocked_paths",
            "candidate_not_written",
            "candidate_not_executed",
            "real_apply_blocked",
            "route_insert_blocked",
            "protected_core_untouched",
            "no_shell",
            "no_network",
            "no_secret_read",
        ]:
            if checks.get(key) is not True:
                errors.append(f"D133 materialization preflight check {key} must be true")
        for key in ["filesystem_write_executed", "filesystem_scan_executed", "git_diff_executed"]:
            if materialization_preflight.get(key) is not False:
                errors.append(f"D133 materialization preflight {key} must be false")
        for key in [
            "candidate_files_written_now",
            "candidate_executed_now",
            "actual_apply_executed",
            "route_inserted",
            "protected_core_mutated",
            "canonical_memory_mutated",
            "shell_executed_by_ai",
            "git_action_by_ai",
            "network_accessed",
            "api_key_read",
            "secret_read",
        ]:
            if materialization_preflight.get(key) is not False:
                errors.append(f"D133 materialization preflight {key} must be false")

    if not d134_scope:
        errors.append("missing D133 D134 sandbox candidate write materialization scope")
    else:
        if d134_scope.get("ok") is not True:
            errors.append("D133 D134 scope ok must be true")
        if d134_scope.get("allowed_next_gate") != REQ_D134_GATE:
            errors.append("D133 D134 scope allowed_next_gate must be D134")
        if d134_scope.get("sandbox_candidate_write_materialization_scope_only") is not True:
            errors.append("D133 D134 scope must be write materialization scope only")
        if d134_scope.get("human_review_required") is not True:
            errors.append("D133 D134 scope must require human review")
        for key in [
            "candidate_written_after_d133",
            "candidate_executed_after_d133_by_ai",
            "real_apply_allowed_after_d133_by_ai",
            "route_insert_allowed_after_d133_by_ai",
            "protected_core_mutation_allowed_after_d133_by_ai",
        ]:
            if d134_scope.get(key) is not False:
                errors.append(f"D133 D134 scope {key} must be false")

    return errors


def build_candidate_file_contents(write_materialization_id, d133, materialization_manifest):
    candidate_id = d133.get("candidate_id")
    proposal_id = d133.get("proposal_id")
    root_value = materialization_manifest.get("allowed_candidate_write_root")
    planned = planned_paths_from_manifest(materialization_manifest)

    manifest = {
        "state": "SANDBOX_CANDIDATE_MATERIALIZED_MANIFEST",
        "ok": True,
        "write_materialization_id": write_materialization_id,
        "materialization_id": d133.get("materialization_id"),
        "static_validation_id": d133.get("static_validation_id"),
        "write_once_id": d133.get("write_once_id"),
        "window_id": d133.get("window_id"),
        "runner_id": d133.get("runner_id"),
        "plan_id": d133.get("plan_id"),
        "review_id": d133.get("review_id"),
        "candidate_id": candidate_id,
        "proposal_id": proposal_id,
        "candidate_root": root_value,
        "candidate_status": "MATERIALIZED_NOT_EXECUTED_NOT_APPLIED",
        "planned_files": planned,
        "guardrails": {
            "sandbox_only": True,
            "candidate_executed": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "shell_executed_by_ai": False,
            "git_action_by_ai": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
        },
    }

    payload = {
        "state": "SANDBOX_CANDIDATE_MATERIALIZED_PAYLOAD",
        "ok": True,
        "write_materialization_id": write_materialization_id,
        "materialization_id": d133.get("materialization_id"),
        "candidate_id": candidate_id,
        "proposal_id": proposal_id,
        "payload_mode": "SAFE_SANDBOX_CANDIDATE_PLACEHOLDER_NO_EXECUTION",
        "candidate_intent": "preserve guarded autonomy chain candidate for later post-write validation",
        "execution_mode": "NOT_EXECUTED",
        "apply_mode": "NOT_APPLIED",
        "route_insert_mode": "BLOCKED",
        "protected_core_mode": "UNTOUCHED_BY_AI",
        "next_required_gate": REQ_D135_GATE,
    }

    summary = "\n".join([
        f"# Sandbox Candidate {candidate_id}",
        "",
        "Status: MATERIALIZED_NOT_EXECUTED_NOT_APPLIED",
        "",
        "This sandbox candidate was materialized by D134 into the approved candidate root only.",
        "",
        "Guardrails:",
        "- no candidate execution",
        "- no real apply",
        "- no route insert",
        "- no protected core mutation",
        "- no canonical memory overwrite",
        "- no shell execution by AI",
        "- no network/provider call",
        "- no secret read",
        "- no git action by AI",
        "",
        f"Candidate ID: {candidate_id}",
        f"Proposal ID: {proposal_id}",
        f"Write materialization ID: {write_materialization_id}",
        f"Next gate: {REQ_D135_GATE}",
        "",
    ])

    return {
        f"{root_value}candidate_manifest.json": json.dumps(manifest, ensure_ascii=False, indent=2),
        f"{root_value}candidate_summary.md": summary,
        f"{root_value}candidate_payload.json": json.dumps(payload, ensure_ascii=False, indent=2),
    }


def write_candidate_files_once(root, file_contents):
    written = []
    verified_existing = []
    blocked_existing = []

    for rel_path, content in file_contents.items():
        p = root / rel_path
        if p.exists():
            existing = p.read_text(encoding="utf-8")
            if existing == content:
                verified_existing.append(rel_path)
            else:
                blocked_existing.append(rel_path)
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        written.append(rel_path)

    return written, verified_existing, blocked_existing


def build_write_receipt(write_materialization_id, d133, materialization_manifest, written, verified_existing, blocked_existing, file_contents):
    all_paths = list(file_contents.keys())
    file_digests = {path: text_digest(content) for path, content in file_contents.items()}
    ok = not blocked_existing and len(written) + len(verified_existing) == len(all_paths)
    return {
        "state": "D134_SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_RECEIPT",
        "ok": ok,
        "write_materialization_id": write_materialization_id,
        "materialization_id": d133.get("materialization_id"),
        "static_validation_id": d133.get("static_validation_id"),
        "write_once_id": d133.get("write_once_id"),
        "window_id": d133.get("window_id"),
        "runner_id": d133.get("runner_id"),
        "plan_id": d133.get("plan_id"),
        "review_id": d133.get("review_id"),
        "candidate_id": d133.get("candidate_id"),
        "proposal_id": d133.get("proposal_id"),
        "created_at": now(),
        "receipt_mode": "SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_RECEIPT_ONLY",
        "allowed_candidate_write_root": materialization_manifest.get("allowed_candidate_write_root"),
        "candidate_files_expected": all_paths,
        "candidate_files_written_now_paths": written,
        "candidate_files_verified_existing_paths": verified_existing,
        "candidate_files_blocked_existing_paths": blocked_existing,
        "candidate_file_digests": file_digests,
        "candidate_files_materialized": ok,
        "candidate_files_written_now": len(written) > 0,
        "candidate_executed_now": False,
        "actual_apply_executed": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "canonical_memory_mutated": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "network_accessed": False,
        "api_key_read": False,
        "secret_read": False,
        "human_review_required": True,
    }


def build_write_postcheck(root, write_materialization_id, d133, materialization_manifest, file_contents):
    existing = []
    missing = []
    digest_matches = {}
    for rel_path, content in file_contents.items():
        p = root / rel_path
        if not p.exists():
            missing.append(rel_path)
            digest_matches[rel_path] = False
            continue
        existing.append(rel_path)
        digest_matches[rel_path] = p.read_text(encoding="utf-8") == content

    ok = len(missing) == 0 and all(digest_matches.values())
    return {
        "state": "D134_SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_POSTCHECK",
        "ok": ok,
        "write_materialization_id": write_materialization_id,
        "materialization_id": d133.get("materialization_id"),
        "static_validation_id": d133.get("static_validation_id"),
        "write_once_id": d133.get("write_once_id"),
        "window_id": d133.get("window_id"),
        "runner_id": d133.get("runner_id"),
        "plan_id": d133.get("plan_id"),
        "review_id": d133.get("review_id"),
        "candidate_id": d133.get("candidate_id"),
        "proposal_id": d133.get("proposal_id"),
        "created_at": now(),
        "postcheck_mode": "SANDBOX_CANDIDATE_WRITE_POSTCHECK_NO_EXECUTION_NO_APPLY",
        "allowed_candidate_write_root": materialization_manifest.get("allowed_candidate_write_root"),
        "candidate_files_existing": existing,
        "candidate_files_missing": missing,
        "candidate_file_digest_matches": digest_matches,
        "candidate_files_materialized": ok,
        "candidate_executed_now": False,
        "actual_apply_executed": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "canonical_memory_mutated": False,
        "shell_executed_by_ai": False,
        "git_action_by_ai": False,
        "network_accessed": False,
        "api_key_read": False,
        "secret_read": False,
        "human_review_required": True,
    }


def build_d135_scope(write_materialization_id, d133):
    return {
        "state": "D134_D135_SANDBOX_CANDIDATE_POST_WRITE_VALIDATION_SCOPE",
        "ok": True,
        "write_materialization_id": write_materialization_id,
        "materialization_id": d133.get("materialization_id"),
        "static_validation_id": d133.get("static_validation_id"),
        "write_once_id": d133.get("write_once_id"),
        "window_id": d133.get("window_id"),
        "runner_id": d133.get("runner_id"),
        "plan_id": d133.get("plan_id"),
        "review_id": d133.get("review_id"),
        "candidate_id": d133.get("candidate_id"),
        "intake_id": d133.get("intake_id"),
        "ping_id": d133.get("ping_id"),
        "config_id": d133.get("config_id"),
        "dashboard_id": d133.get("dashboard_id"),
        "adapter_id": d133.get("adapter_id"),
        "seal_id": d133.get("seal_id"),
        "proposal_id": d133.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D135_GATE,
        "d135_allowed_to_create": [
            "sandbox_candidate_post_write_validation_scope",
            "sandbox_candidate_post_write_validation_report",
            "sandbox_candidate_materialized_file_inventory",
            "d136_sandbox_candidate_execution_preflight_scope",
        ],
        "d135_must_not_execute": [
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
        "sandbox_candidate_post_write_validation_scope_only": True,
        "human_review_required": True,
        "candidate_executed_after_d134_by_ai": False,
        "real_apply_allowed_after_d134_by_ai": False,
        "route_insert_allowed_after_d134_by_ai": False,
        "protected_core_mutation_allowed_after_d134_by_ai": False,
        "required_phrase_for_later_gate": "APPROVE_D135_SANDBOX_CANDIDATE_POST_WRITE_VALIDATION_SCOPE_ONLY",
    }


def create_sandbox_candidate_write_materialization_scope(root="."):
    root = Path(root).resolve()

    d133 = read_json(root / D133_REPORT, {}) or {}
    materialization_manifest = read_json(root / D133_MATERIALIZATION_MANIFEST, {}) or {}
    materialization_preflight = read_json(root / D133_MATERIALIZATION_PREFLIGHT, {}) or {}
    d134_scope_in = read_json(root / D133_D134_SCOPE, {}) or {}

    errors = validate_d133(d133, materialization_manifest, materialization_preflight, d134_scope_in)

    write_materialization_id = "d134-" + digest({
        "materialization_id": d133.get("materialization_id"),
        "static_validation_id": d133.get("static_validation_id"),
        "write_once_id": d133.get("write_once_id"),
        "window_id": d133.get("window_id"),
        "runner_id": d133.get("runner_id"),
        "plan_id": d133.get("plan_id"),
        "review_id": d133.get("review_id"),
        "candidate_id": d133.get("candidate_id"),
        "proposal_id": d133.get("proposal_id"),
    })

    file_contents = {}
    written = []
    verified_existing = []
    blocked_existing = []
    if not errors:
        file_contents = build_candidate_file_contents(write_materialization_id, d133, materialization_manifest)
        for path in file_contents:
            if not is_safe_candidate_path(path, materialization_manifest.get("allowed_candidate_write_root")):
                errors.append("candidate materialization target must stay inside approved candidate root")
        if not errors:
            written, verified_existing, blocked_existing = write_candidate_files_once(root, file_contents)
            if blocked_existing:
                errors.append("existing candidate files differ from deterministic materialization content")

    write_receipt = build_write_receipt(
        write_materialization_id,
        d133,
        materialization_manifest,
        written,
        verified_existing,
        blocked_existing,
        file_contents,
    )
    write_postcheck = build_write_postcheck(root, write_materialization_id, d133, materialization_manifest, file_contents)
    d135_scope = build_d135_scope(write_materialization_id, d133)

    if write_receipt.get("ok") is not True:
        errors.append("write_materialization_receipt must be ok")
    if write_postcheck.get("ok") is not True:
        errors.append("write_materialization_postcheck must be ok")

    for item_name, item in [("write_receipt", write_receipt), ("write_postcheck", write_postcheck)]:
        for key in [
            "candidate_executed_now",
            "actual_apply_executed",
            "route_inserted",
            "protected_core_mutated",
            "canonical_memory_mutated",
            "shell_executed_by_ai",
            "git_action_by_ai",
            "network_accessed",
            "api_key_read",
            "secret_read",
        ]:
            if item.get(key) is not False:
                errors.append(f"{item_name} {key} must be false")

    ok = not errors
    decision = "SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_SCOPE_READY" if ok else "SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_SCOPE_BLOCKED"
    result = "D134_SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_SCOPE_CREATED" if ok else "D134_SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_SCOPE_BLOCKED"
    files_materialized = ok and write_postcheck.get("candidate_files_materialized") is True
    files_written_now = ok and len(written) > 0
    already_verified = ok and len(written) == 0 and len(verified_existing) == len(file_contents)

    if ok:
        write_json(root / WRITE_RECEIPT_OUT, write_receipt)
        write_json(root / WRITE_POSTCHECK_OUT, write_postcheck)
        write_json(root / D135_SCOPE_OUT, d135_scope)

    report = {
        "state": "D134_SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_SCOPE",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_CANDIDATE_WRITE_MATERIALIZATION_SCOPE",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "write_materialization_id": write_materialization_id,
        "materialization_id": d133.get("materialization_id"),
        "static_validation_id": d133.get("static_validation_id"),
        "write_once_id": d133.get("write_once_id"),
        "window_id": d133.get("window_id"),
        "runner_id": d133.get("runner_id"),
        "plan_id": d133.get("plan_id"),
        "review_id": d133.get("review_id"),
        "candidate_id": d133.get("candidate_id"),
        "intake_id": d133.get("intake_id"),
        "ping_id": d133.get("ping_id"),
        "config_id": d133.get("config_id"),
        "dashboard_id": d133.get("dashboard_id"),
        "adapter_id": d133.get("adapter_id"),
        "seal_id": d133.get("seal_id"),
        "proposal_id": d133.get("proposal_id"),
        "source_d133_report": D133_REPORT,
        "sandbox_candidate_write_materialization_receipt": write_receipt if ok else {},
        "sandbox_candidate_write_materialization_postcheck": write_postcheck if ok else {},
        "d135_scope": d135_scope if ok else {},
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
            "sandbox_candidate_write_materialization_scope_only": True,
            "write_materialization_receipt_only": True,
            "write_materialization_postcheck_only": True,
            "candidate_files_materialized": files_materialized,
            "candidate_files_written_now": files_written_now,
            "candidate_files_verified_existing": already_verified,
            "candidate_executed_now": False,
            "approval_for_d135_post_write_validation_scope_only": ok,
            "approval_for_candidate_execution": False,
            "approval_for_real_apply_by_ai": False,
            "candidate_execution_allowed_by_ai": False,
            "commands_executed_by_ai": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "write_materialization_id": write_materialization_id,
            "materialization_id": d133.get("materialization_id"),
            "static_validation_id": d133.get("static_validation_id"),
            "write_once_id": d133.get("write_once_id"),
            "window_id": d133.get("window_id"),
            "runner_id": d133.get("runner_id"),
            "plan_id": d133.get("plan_id"),
            "review_id": d133.get("review_id"),
            "candidate_id": d133.get("candidate_id"),
            "adapter_id": d133.get("adapter_id"),
            "seal_id": d133.get("seal_id"),
            "proposal_id": d133.get("proposal_id"),
            "write_materialization_status": "CANDIDATE_FILES_MATERIALIZED" if files_written_now else ("CANDIDATE_FILES_ALREADY_MATERIALIZED_VERIFIED" if already_verified else "BLOCKED"),
            "candidate_status": "MATERIALIZED_NOT_EXECUTED_NOT_APPLIED" if ok else "BLOCKED",
            "real_provider_status": "NOT_CALLED",
            "network_status": "NOT_ACCESSED",
            "secret_status": "NOT_READ",
            "real_apply_by_ai_status": "BLOCKED",
            "route_insert_status": "BLOCKED",
            "protected_core_status": "UNTOUCHED_BY_AI",
            "approval_scope": "D135_SANDBOX_CANDIDATE_POST_WRITE_VALIDATION_SCOPE_ONLY" if ok else "BLOCKED",
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D135_GATE if ok else "BLOCKED",
        },
        "success_condition": {
            "sandbox_candidate_write_materialization_scope_created": ok,
            "sandbox_candidate_write_materialization_receipt_created": ok,
            "sandbox_candidate_write_materialization_postcheck_created": ok,
            "d135_scope_created": ok,
            "candidate_files_materialized": files_materialized,
            "candidate_executed_by_ai": False,
            "actual_apply_executed_by_ai": False,
            "route_inserted_by_ai": False,
            "protected_core_untouched_by_ai": True,
            "next_step": "D135 may create sandbox candidate post-write validation scope only.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_candidate_write_materialization_scope(), ensure_ascii=False, indent=2))
