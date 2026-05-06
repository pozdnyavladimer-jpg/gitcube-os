from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


D83_REPORT = "reports/d83_sandbox_writer_handoff.json"
D83_MANIFEST = "reports/d83_sandbox_writer_handoff_manifest.json"
OUT = "reports/d84_sandbox_writer_output_review.json"
WRITER_OUTPUT_DIR = "runtime_experimental/ai_sandbox_work"


ALLOWED_WRITE_PREFIXES = [
    "runtime_experimental/ai_sandbox_work/",
    "reports/",
    "tests/",
]

BLOCKED_WRITE_PREFIXES = [
    "app/orchestration/",
    "core/",
    "runtime/",
    "bridges/",
    "memory/",
]

FORBIDDEN_ACTIONS = [
    "direct_core_edit",
    "route_insert",
    "actual_apply",
    "external_ai_network_call",
    "git_commit_or_push_by_ai",
    "canonical_memory_overwrite",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: str | Path, data: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def safe_path(value: str) -> str:
    raw = str(value or "").strip().replace("\\", "/").lstrip("/")
    return "/".join(x for x in raw.split("/") if x and x not in (".", ".."))


def sha256_json(data: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def is_allowed_write_path(path: str) -> bool:
    p = safe_path(path)
    if any(p.startswith(prefix) for prefix in BLOCKED_WRITE_PREFIXES):
        return False
    return any(p.startswith(prefix) for prefix in ALLOWED_WRITE_PREFIXES)


def validate_d83(d83: Dict[str, Any], manifest: Dict[str, Any], errors: List[str]) -> Dict[str, Any]:
    if not d83:
        errors.append("D83 sandbox writer handoff report missing or unreadable")
        return {}

    if d83.get("ok") is not True:
        errors.append("D83 ok flag is not true")
    if d83.get("decision") != "SANDBOX_WRITER_HANDOFF_READY":
        errors.append(f"D83 decision is not SANDBOX_WRITER_HANDOFF_READY: {d83.get('decision')}")

    guard = d83.get("guardrails") if isinstance(d83.get("guardrails"), dict) else {}
    for key in (
        "external_ai_called",
        "network_accessed",
        "runtime_code_mutated",
        "protected_core_mutated",
        "canonical_memory_mutated",
        "actual_apply_executed",
        "route_inserted",
        "git_commit_by_ai",
    ):
        if guard.get(key) is not False:
            errors.append(f"D83 guardrail {key} is not false")
    if guard.get("sandbox_handoff_only") is not True:
        errors.append("D83 sandbox_handoff_only is not true")
    if guard.get("writer_input_only") is not True:
        errors.append("D83 writer_input_only is not true")

    if not manifest:
        errors.append("D83 manifest missing or unreadable")
        return {}

    if manifest.get("ok") is not True:
        errors.append("D83 manifest ok flag is not true")
    if manifest.get("next_gate") != "D84_SANDBOX_WRITER_OUTPUT_REVIEW":
        errors.append(f"D83 manifest next_gate invalid: {manifest.get('next_gate')}")
    if manifest.get("protected_core_touched") is not False:
        errors.append("D83 manifest protected_core_touched is not false")
    if manifest.get("actual_files_mutated") not in ([], None):
        errors.append("D83 manifest actual_files_mutated is not empty")

    writer_input_path = manifest.get("writer_input_path") or d83.get("writer_input_path") or ""
    if not writer_input_path:
        errors.append("D83 writer input path missing")
        return {}

    writer_input = read_json(writer_input_path, {}) or {}
    if not writer_input:
        errors.append("D83 writer input file missing or unreadable")
        return {}

    if writer_input.get("mode") != "SANDBOX_WRITER_INPUT_ONLY":
        errors.append(f"D83 writer input mode invalid: {writer_input.get('mode')}")

    wguard = writer_input.get("guardrails") if isinstance(writer_input.get("guardrails"), dict) else {}
    for key in (
        "actual_apply_allowed",
        "route_insert_allowed",
        "protected_core_mutation_allowed",
        "external_ai_call_allowed",
        "git_action_allowed",
    ):
        if wguard.get(key) is not False:
            errors.append(f"D83 writer input guardrail {key} is not false")
    if wguard.get("proposal_only") is not True:
        errors.append("D83 writer input proposal_only is not true")
    if wguard.get("sandbox_only") is not True:
        errors.append("D83 writer input sandbox_only is not true")

    return writer_input


def build_mock_writer_output(review_id: str, writer_input: Dict[str, Any]) -> Dict[str, Any]:
    source = writer_input.get("source") if isinstance(writer_input.get("source"), dict) else {}
    output_path = f"{WRITER_OUTPUT_DIR}/{review_id}/candidate_proposal.json"
    test_path = f"tests/test_{review_id}_candidate_probe.py"
    report_path = f"reports/{review_id}_candidate_review.json"

    return {
        "state": "D84_SANDBOX_WRITER_MOCK_OUTPUT",
        "ok": True,
        "mode": "SANDBOX_OUTPUT_CANDIDATE_ONLY",
        "created_at": now(),
        "review_id": review_id,
        "source": source,
        "candidate_files": [
            output_path,
            test_path,
            report_path,
        ],
        "candidate_payload": {
            "proposal_type": "SANDBOX_CHILD_MODULE_REVIEW_CANDIDATE",
            "target_scope": "sandbox_only",
            "source_handoff_id": writer_input.get("handoff_id"),
            "summary": "Candidate output remains sandbox-only and waits for D85/D66 review before any guarded apply discussion.",
        },
        "forbidden_actions": FORBIDDEN_ACTIONS,
        "guardrails": {
            "sandbox_output_only": True,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "network_accessed": False,
            "git_commit_by_ai": False,
        },
    }


def review_writer_output(writer_output: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    if not writer_output:
        errors.append("writer output missing or unreadable")
        return

    if writer_output.get("ok") is not True:
        errors.append("writer output ok flag is not true")
    if writer_output.get("mode") != "SANDBOX_OUTPUT_CANDIDATE_ONLY":
        errors.append(f"writer output mode invalid: {writer_output.get('mode')}")

    candidate_files = writer_output.get("candidate_files")
    if not isinstance(candidate_files, list) or not candidate_files:
        errors.append("writer output candidate_files missing or empty")
    else:
        for f in candidate_files:
            p = safe_path(str(f))
            if p != str(f).replace("\\", "/").lstrip("/"):
                errors.append(f"candidate path is unsafe: {f}")
            if not is_allowed_write_path(p):
                errors.append(f"candidate file outside sandbox/reports/tests scope: {p}")

    forbidden = writer_output.get("forbidden_actions")
    if not isinstance(forbidden, list):
        errors.append("writer output forbidden_actions missing or invalid")
    else:
        for action in FORBIDDEN_ACTIONS:
            if action not in forbidden:
                errors.append(f"writer output missing forbidden action: {action}")

    guard = writer_output.get("guardrails") if isinstance(writer_output.get("guardrails"), dict) else {}
    for key in (
        "actual_apply_executed",
        "route_inserted",
        "protected_core_mutated",
        "canonical_memory_mutated",
        "external_ai_called",
        "network_accessed",
        "git_commit_by_ai",
    ):
        if guard.get(key) is not False:
            errors.append(f"writer output guardrail {key} is not false")
    if guard.get("sandbox_output_only") is not True:
        errors.append("writer output sandbox_output_only is not true")


def create_sandbox_writer_output_review(
    root: str | Path = ".",
    d83_report_path: str = D83_REPORT,
    d83_manifest_path: str = D83_MANIFEST,
    output_path: str = OUT,
    writer_output_dir: str = WRITER_OUTPUT_DIR,
    injected_writer_output: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    root = Path(root).resolve()
    d83 = read_json(root / d83_report_path, {}) or {}
    manifest = read_json(root / d83_manifest_path, {}) or {}

    errors: List[str] = []
    warnings: List[str] = []

    writer_input = validate_d83(d83, manifest, errors)

    handoff_id = str(d83.get("handoff_id") or manifest.get("handoff_id") or "")
    intent_id = str((d83.get("evidence") or {}).get("intent_id") or "")
    proposal_id = str((d83.get("evidence") or {}).get("proposal_id") or "")
    review_id = "d84-" + sha256_json(
        {
            "handoff_id": handoff_id,
            "intent_id": intent_id,
            "proposal_id": proposal_id,
        }
    )[:16]

    writer_output = injected_writer_output or build_mock_writer_output(review_id, writer_input)
    review_writer_output(writer_output, errors, warnings)

    ok = not errors
    decision = "SANDBOX_WRITER_OUTPUT_REVIEW_READY" if ok else "SANDBOX_WRITER_OUTPUT_REVIEW_BLOCKED"
    result = "D84_SANDBOX_WRITER_OUTPUT_REVIEW_CREATED" if ok else "D84_SANDBOX_WRITER_OUTPUT_REVIEW_BLOCKED"

    writer_output_rel = safe_path(f"{writer_output_dir}/{review_id}/writer_output_candidate.json")
    writer_output_abs = root / writer_output_rel

    if ok:
        write_json(writer_output_abs, writer_output)

    report = {
        "state": "D84_SANDBOX_WRITER_OUTPUT_REVIEW",
        "result": result,
        "route": "FIELD_INTENT_SANDBOX_WRITER_OUTPUT_REVIEW",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "review_id": review_id,
        "writer_output_path": str(writer_output_abs) if ok else "",
        "input_reports": {
            "d83_report_path": str(root / d83_report_path),
            "d83_manifest_path": str(root / d83_manifest_path),
        },
        "evidence": {
            "handoff_id": handoff_id,
            "intent_id": intent_id,
            "proposal_id": proposal_id,
            "writer_output_mode": writer_output.get("mode") if isinstance(writer_output, dict) else None,
            "candidate_files": writer_output.get("candidate_files") if isinstance(writer_output, dict) else [],
        },
        "review": {
            "candidate_files_count": len(writer_output.get("candidate_files", [])) if isinstance(writer_output, dict) else 0,
            "allowed_write_prefixes": ALLOWED_WRITE_PREFIXES,
            "blocked_write_prefixes": BLOCKED_WRITE_PREFIXES,
            "forbidden_actions": FORBIDDEN_ACTIONS,
            "approved_for_guarded_apply": False,
            "approved_for_route_insert": False,
            "approved_for_protected_core": False,
            "approved_for_next_sandbox_gate": ok,
        },
        "guardrails": {
            "external_ai_called": False,
            "network_accessed": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
            "sandbox_output_review_only": True,
            "writer_output_candidate_only": True,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "review_id": review_id,
            "handoff_id": handoff_id,
            "proposal_id": proposal_id,
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "sandbox_writer_output_reviewed": ok,
            "writer_output_candidate_created": ok,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_untouched": True,
            "next_step": "D85 can create regression/rollback evidence bundle for reviewed sandbox output; real apply still blocked.",
        },
    }

    write_json(root / output_path, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_sandbox_writer_output_review(), ensure_ascii=False, indent=2))
