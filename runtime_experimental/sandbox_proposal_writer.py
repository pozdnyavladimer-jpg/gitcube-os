
from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

D107_REPORT = "reports/d107_proposal_schema_validator.json"
D107_PROPOSAL = "reports/d107_mock_valid_proposal.json"
D107_ACCEPTANCE = "reports/d107_acceptance_manifest.json"
D107_D108_SCOPE = "reports/d107_d108_sandbox_proposal_writer_scope.json"

SANDBOX_DIR = "runtime_experimental/ai_sandbox_work"
SANDBOX_PROPOSAL = "runtime_experimental/ai_sandbox_work/d108_accepted_proposal.json"
SANDBOX_MANIFEST = "runtime_experimental/ai_sandbox_work/d108_sandbox_proposal_manifest.json"
SANDBOX_RECEIPT = "runtime_experimental/ai_sandbox_work/d108_writer_receipt.json"

OUT = "reports/d108_sandbox_proposal_writer.json"
REPORT_MANIFEST = "reports/d108_sandbox_proposal_manifest.json"
REPORT_RECEIPT = "reports/d108_writer_receipt.json"
D109_SCOPE = "reports/d108_d109_regression_runner_scope.json"

REQ_D107_DECISION = "PROPOSAL_SCHEMA_VALIDATOR_READY"
REQ_D108_GATE = "D108_SANDBOX_PROPOSAL_WRITER"
REQ_D109_GATE = "D109_REGRESSION_RUNNER"

ALLOWED_PREFIXES = ["runtime_experimental/ai_sandbox_work/", "reports/", "tests/", "docs/"]
BLOCKED_PREFIXES = ["app/orchestration/", "core/", "runtime/", "bridges/", "memory/"]

FORBIDDEN_FIELDS = [
    "api_key", "api_secret", "token", "password", "raw_shell_command",
    "shell_command", "subprocess", "exec", "eval", "auto_apply",
    "apply_now", "git_commit", "git_push", "route_insert",
    "protected_core_mutation", "canonical_memory_overwrite", "direct_core_edit",
]

FALSE_GUARDS = [
    "external_ai_called", "network_accessed", "shell_executed",
    "actual_apply_executed", "route_inserted", "protected_core_mutated",
    "canonical_memory_mutated", "git_commit_by_ai",
]


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]


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


def starts(path, prefixes):
    return any(str(path).startswith(prefix) for prefix in prefixes)


def has_forbidden_content(obj):
    hits = []
    tokens = [x.lower() for x in FORBIDDEN_FIELDS]

    def walk(x, path=""):
        if isinstance(x, dict):
            for k, v in x.items():
                k_text = str(k)
                k_low = k_text.lower()
                if not path.startswith("guardrails.") and k_low in tokens:
                    hits.append(path + k_text)
                walk(v, path + k_text + ".")
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, path + f"{i}.")
        elif isinstance(x, str):
            s = x.lower()
            for token in tokens:
                if token in s:
                    hits.append(path.rstrip(".") + f":contains:{token}")

    walk(obj)
    return sorted(set(hits))


def validate_inputs(d107, proposal, acceptance, scope):
    errors = []

    if not d107:
        errors.append("missing D107 report")
        return errors

    if d107.get("ok") is not True:
        errors.append("D107 ok must be true")
    if d107.get("decision") != REQ_D107_DECISION:
        errors.append("D107 decision must be PROPOSAL_SCHEMA_VALIDATOR_READY")

    d107_guard = d107.get("guardrails", {})
    for key in [
        "external_ai_called", "network_accessed", "api_key_read", "secret_read",
        "shell_executed", "runtime_code_mutated", "protected_core_mutated",
        "canonical_memory_mutated", "actual_apply_executed", "route_inserted",
        "git_commit_by_ai", "rollback_executed", "restore_executed",
    ]:
        if d107_guard.get(key) is not False:
            errors.append(f"D107 guardrails.{key} must be false")

    for key in ["schema_validation_only", "sandbox_writer_not_called", "proposal_only"]:
        if d107_guard.get(key) is not True:
            errors.append(f"D107 guardrails.{key} must be true")

    if not proposal:
        errors.append("missing D107 accepted proposal")
    else:
        if proposal.get("requires_human_review") is not True:
            errors.append("proposal requires_human_review must be true")
        if has_forbidden_content(proposal):
            errors.append("proposal contains forbidden field/content")
        target = str(proposal.get("target_scope", ""))
        if starts(target, BLOCKED_PREFIXES):
            errors.append("proposal target_scope is blocked")
        if target and not starts(target, ALLOWED_PREFIXES):
            errors.append("proposal target_scope is not allowed")
        files = proposal.get("candidate_files", [])
        if not isinstance(files, list):
            errors.append("proposal candidate_files must be list")
        else:
            for item in files:
                item = str(item)
                if starts(item, BLOCKED_PREFIXES):
                    errors.append(f"blocked candidate path: {item}")
                if item and not starts(item, ALLOWED_PREFIXES):
                    errors.append(f"candidate path not allowed: {item}")
        guardrails = proposal.get("guardrails", {})
        for key in FALSE_GUARDS:
            if guardrails.get(key) is not False:
                errors.append(f"proposal guardrails.{key} must be false")

    if not acceptance:
        errors.append("missing D107 acceptance manifest")
    else:
        if acceptance.get("ok") is not True:
            errors.append("acceptance ok must be true")
        if acceptance.get("accepted_for") != "D108_SANDBOX_PROPOSAL_WRITER_ONLY":
            errors.append("acceptance must be for D108 only")
        if proposal and acceptance.get("accepted_proposal_id") != proposal.get("proposal_id"):
            errors.append("acceptance proposal id mismatch")
        for key in ["sandbox_write_executed", "actual_apply_executed", "protected_core_mutated", "route_inserted"]:
            if acceptance.get(key) is not False:
                errors.append(f"acceptance {key} must be false")

    if not scope:
        errors.append("missing D107 D108 scope")
    else:
        if scope.get("ok") is not True:
            errors.append("D108 scope ok must be true")
        if scope.get("allowed_next_gate") != REQ_D108_GATE:
            errors.append("D108 scope allowed_next_gate invalid")
        if scope.get("sandbox_write_allowed_after_d107") is not True:
            errors.append("sandbox_write_allowed_after_d107 must be true")
        for key in ["actual_apply_allowed_after_d107", "route_insert_allowed_after_d107", "protected_core_mutation_allowed_after_d107"]:
            if scope.get(key) is not False:
                errors.append(f"{key} must be false")

    return errors


def make_manifest(writer_id, proposal):
    return {
        "state": "D108_SANDBOX_PROPOSAL_MANIFEST",
        "ok": True,
        "writer_id": writer_id,
        "proposal_id": proposal.get("proposal_id"),
        "created_at": now(),
        "write_mode": "SANDBOX_JSON_COPY_ONLY",
        "sandbox_dir": SANDBOX_DIR,
        "sandbox_files": [SANDBOX_PROPOSAL, SANDBOX_MANIFEST, SANDBOX_RECEIPT],
        "source_candidate_files": proposal.get("candidate_files", []),
        "actual_apply_executed": False,
        "candidate_executed": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "canonical_memory_mutated": False,
    }


def make_receipt(writer_id, proposal, manifest):
    return {
        "state": "D108_WRITER_RECEIPT",
        "ok": True,
        "writer_id": writer_id,
        "proposal_id": proposal.get("proposal_id"),
        "created_at": now(),
        "written_files": manifest["sandbox_files"],
        "writes_limited_to": ["runtime_experimental/ai_sandbox_work/", "reports/"],
        "not_written_to": BLOCKED_PREFIXES,
        "external_ai_called": False,
        "network_accessed": False,
        "shell_executed": False,
        "actual_apply_executed": False,
        "candidate_executed": False,
        "git_commit_by_ai": False,
    }


def make_d109_scope(writer_id, proposal):
    return {
        "state": "D108_D109_REGRESSION_RUNNER_SCOPE",
        "ok": True,
        "writer_id": writer_id,
        "proposal_id": proposal.get("proposal_id"),
        "created_at": now(),
        "allowed_next_gate": REQ_D109_GATE,
        "d109_allowed_to_create": [
            "regression_runner", "sandbox_static_checks", "sandbox_regression_results",
            "sandbox_diff_summary", "d110_human_review_gate_scope",
        ],
        "d109_must_not_execute": [
            "real_apply", "auto_apply", "route_insert", "protected_core_mutation",
            "canonical_memory_overwrite", "external_ai_network_call", "shell_exec_from_ai",
            "git_commit_by_ai", "git_push_by_ai", "rollback_execute", "restore_execute",
            "apply_sandbox_candidate", "execute_sandbox_candidate", "commit_sandbox_candidate",
        ],
        "actual_apply_allowed_after_d108": False,
        "route_insert_allowed_after_d108": False,
        "protected_core_mutation_allowed_after_d108": False,
        "sandbox_candidate_execution_allowed_after_d108": False,
        "required_phrase_for_later_gate": "APPROVE_D109_REGRESSION_RUNNER_ONLY",
    }


def create_sandbox_proposal_writer(root="."):
    root = Path(root).resolve()
    d107 = read_json(root / D107_REPORT, {}) or {}
    proposal = read_json(root / D107_PROPOSAL, {}) or {}
    acceptance = read_json(root / D107_ACCEPTANCE, {}) or {}
    scope = read_json(root / D107_D108_SCOPE, {}) or {}

    errors = validate_inputs(d107, proposal, acceptance, scope)
    writer_id = "d108-" + sha({
        "validator_id": d107.get("validator_id"),
        "boundary_id": d107.get("boundary_id"),
        "proposal_id": proposal.get("proposal_id"),
    })

    ok = not errors
    decision = "SANDBOX_PROPOSAL_WRITER_READY" if ok else "SANDBOX_PROPOSAL_WRITER_BLOCKED"
    result = "D108_SANDBOX_PROPOSAL_WRITER_CREATED" if ok else "D108_SANDBOX_PROPOSAL_WRITER_BLOCKED"

    manifest = make_manifest(writer_id, proposal)
    receipt = make_receipt(writer_id, proposal, manifest)
    d109_scope = make_d109_scope(writer_id, proposal)

    if ok:
        sandbox_copy = {
            "state": "D108_ACCEPTED_PROPOSAL_SANDBOX_COPY",
            "ok": True,
            "writer_id": writer_id,
            "source": D107_PROPOSAL,
            "proposal": proposal,
            "sandbox_copy_only": True,
            "actual_apply_executed": False,
            "candidate_executed": False,
        }
        write_json(root / SANDBOX_PROPOSAL, sandbox_copy)
        write_json(root / SANDBOX_MANIFEST, manifest)
        write_json(root / SANDBOX_RECEIPT, receipt)
        write_json(root / REPORT_MANIFEST, manifest)
        write_json(root / REPORT_RECEIPT, receipt)
        write_json(root / D109_SCOPE, d109_scope)

    report = {
        "state": "D108_SANDBOX_PROPOSAL_WRITER",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_PROPOSAL_WRITER",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "writer_id": writer_id,
        "validator_id": d107.get("validator_id"),
        "boundary_id": d107.get("boundary_id"),
        "proposal_id": proposal.get("proposal_id"),
        "sandbox_proposal_path": SANDBOX_PROPOSAL if ok else "",
        "sandbox_manifest": manifest if ok else {},
        "writer_receipt": receipt if ok else {},
        "d109_scope": d109_scope if ok else {},
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "api_key_read": False,
            "secret_read": False,
            "shell_executed": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "rollback_executed": False,
            "restore_executed": False,
            "sandbox_write_only": True,
            "proposal_json_copy_only": True,
            "candidate_execution_allowed": False,
        },
        "validation": {"ok": ok, "errors": errors, "warnings": []},
        "summary": {
            "decision": decision,
            "writer_id": writer_id,
            "proposal_id": proposal.get("proposal_id"),
            "errors_count": len(errors),
            "warnings_count": 0,
            "next_step": REQ_D109_GATE,
        },
        "success_condition": {
            "sandbox_proposal_written": ok,
            "sandbox_manifest_created": ok,
            "writer_receipt_created": ok,
            "d109_scope_created": ok,
            "real_ai_called": False,
            "actual_apply_executed": False,
            "candidate_executed": False,
            "protected_core_untouched": True,
            "next_step": "D109 may run regression/static checks on sandbox artifacts only.",
        },
    }
    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_proposal_writer(), ensure_ascii=False, indent=2))
