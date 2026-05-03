#!/usr/bin/env python3
'''
D66_CORE_GUARD_REVIEWER_BOOT.py

Adds the live D66 Core Guard Reviewer to GitCube OS.

Run from repo root:
    python D66_CORE_GUARD_REVIEWER_BOOT.py

Creates / patches:
- runtime_experimental/core_guard_reviewer.py
- app/orchestration/task_dispatcher.py
- tests/test_d66_core_guard_reviewer.py
- reports/d66_core_guard_reviewer_report.json

D66 reviews mutation proposals against runtime_experimental/core_guard_policy.json.
It does not mutate runtime code.
'''

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def sh(cmd: list[str], check: bool = False) -> subprocess.CompletedProcess:
    print("$", " ".join(cmd))
    return subprocess.run(cmd, text=True, capture_output=False, check=check)


def find_repo_root() -> Path:
    here = Path.cwd()
    for p in [here, *here.parents]:
        if (p / ".git").exists():
            return p
    return here


ROOT = find_repo_root()
os.chdir(ROOT)
print("D66 REVIEWER BOOT: repo =", ROOT)

Path("runtime_experimental").mkdir(parents=True, exist_ok=True)
Path("reports").mkdir(parents=True, exist_ok=True)
Path("tests").mkdir(parents=True, exist_ok=True)


REVIEWER_CODE = r'''
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set


DECISION_APPROVE = "APPROVE"
DECISION_REJECT = "REJECT"
DECISION_NEEDS_SANDBOX = "NEEDS_SANDBOX"
DECISION_FORBIDDEN_CORE_MUTATION = "FORBIDDEN_CORE_MUTATION"
DECISION_VALIDATION_BYPASS = "VALIDATION_BYPASS"
DECISION_UNSAFE_MEMORY_WRITE = "UNSAFE_MEMORY_WRITE"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def _norm_path(value: Any) -> str:
    text = str(value or "").strip().replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    return text


def _collect_strings(value: Any) -> List[str]:
    out: List[str] = []
    if value is None:
        return out
    if isinstance(value, str):
        if value.strip():
            out.append(value.strip())
        return out
    if isinstance(value, (list, tuple, set)):
        for item in value:
            out.extend(_collect_strings(item))
        return out
    if isinstance(value, dict):
        for key in ("path", "file", "target", "target_file", "target_path", "name", "id"):
            if key in value:
                out.extend(_collect_strings(value.get(key)))
    return out


def _collect_target_files(proposal: Dict[str, Any]) -> List[str]:
    candidates: List[str] = []
    for key in ("target_files", "changed_files", "files", "candidate_target_files", "protected_files", "patch_files"):
        candidates.extend(_collect_strings(proposal.get(key)))

    payload = proposal.get("payload")
    if isinstance(payload, dict):
        for key in ("target_files", "changed_files", "files", "candidate_target_files", "patch_files", "paths"):
            candidates.extend(_collect_strings(payload.get(key)))

    raw_patch = proposal.get("patch") or proposal.get("candidate_patch")
    if isinstance(raw_patch, dict):
        candidates.extend(_collect_strings(raw_patch.get("target_files")))
        candidates.extend(_collect_strings(raw_patch.get("changed_files")))

    normalized: List[str] = []
    seen: Set[str] = set()
    for item in candidates:
        p = _norm_path(item)
        if not p or p in seen:
            continue
        seen.add(p)
        normalized.append(p)
    return normalized


def _collect_actions(proposal: Dict[str, Any]) -> List[str]:
    actions: List[str] = []
    for key in ("actions", "requested_actions", "agent_actions", "forbidden_actions"):
        actions.extend(_collect_strings(proposal.get(key)))

    execution = proposal.get("execution")
    if isinstance(execution, dict):
        actions.extend(_collect_strings(execution.get("actions")))

    payload = proposal.get("payload")
    if isinstance(payload, dict):
        for key in ("actions", "requested_actions", "agent_actions"):
            actions.extend(_collect_strings(payload.get(key)))

    normalized: List[str] = []
    seen: Set[str] = set()
    for item in actions:
        a = str(item or "").strip().lower()
        if not a or a in seen:
            continue
        seen.add(a)
        normalized.append(a)
    return normalized


def _truthy_from_keys(data: Dict[str, Any], keys: Iterable[str]) -> bool:
    for key in keys:
        if bool(data.get(key)) is True:
            return True
    return False


def _collect_validation(proposal: Dict[str, Any]) -> Dict[str, bool]:
    merged: Dict[str, Any] = {}

    for source_key in ("validation", "evidence", "success_condition"):
        if isinstance(proposal.get(source_key), dict):
            merged.update(proposal.get(source_key) or {})

    payload = proposal.get("payload")
    if isinstance(payload, dict):
        for source_key in ("validation", "evidence", "success_condition"):
            if isinstance(payload.get(source_key), dict):
                merged.update(payload.get(source_key) or {})

    unit_tests = _truthy_from_keys(merged, (
        "unit_tests_passed", "tests_passed", "py_compile_passed",
        "local_validation_ok", "local_life_ok", "eye_1_passed",
    ))
    regression = _truthy_from_keys(merged, (
        "regression_passed", "closed_loop_regression_passed",
        "global_validation_ok", "global_life_ok", "eye_2_passed",
    ))
    daemon_smoke = _truthy_from_keys(merged, (
        "daemon_smoke_passed", "daemon_test_passed",
        "runtime_smoke_passed", "runtime_check_passed",
    ))
    backup_plan = _truthy_from_keys(merged, (
        "backup_plan_exists", "backup_created",
        "rollback_plan_exists", "rollback_available",
    ))
    payload_preserved = _truthy_from_keys(merged, (
        "payload_preserved", "resonance_vector_preserved",
        "protected_payload_preserved", "payload_preservation_confirmed",
    ))
    reviewer_approved = _truthy_from_keys(merged, (
        "reviewer_approved", "d66_approved", "independent_review_passed",
    ))

    return {
        "unit_tests_passed": unit_tests,
        "regression_passed": regression,
        "daemon_smoke_passed": daemon_smoke,
        "backup_or_rollback_exists": backup_plan,
        "payload_preserved": payload_preserved,
        "reviewer_approved": reviewer_approved,
        "two_eyes_passed": bool(unit_tests and regression),
    }


def _is_memory_path(path: str) -> bool:
    p = _norm_path(path)
    return p.startswith("memory/") and not (
        p.endswith("_decayed.json")
        or p.endswith("_candidate.json")
        or p.endswith("_reviewed.json")
        or p.endswith(".bak")
    )


def review_core_mutation(
    proposal: Dict[str, Any] | None = None,
    proposal_path: str | None = None,
    policy_path: str = "runtime_experimental/core_guard_policy.json",
    report_path: str = "reports/d66_core_guard_reviewer_report.json",
) -> Dict[str, Any]:
    policy = _load_json(policy_path, default={}) or {}

    if proposal is None:
        proposal = {}

    if proposal_path:
        loaded = _load_json(proposal_path, default=None)
        if isinstance(loaded, dict):
            proposal = loaded

    protected_files = {_norm_path(p) for p in policy.get("protected_files", []) if _norm_path(p)}
    forbidden_actions = {
        str(a or "").strip().lower()
        for a in policy.get("forbidden_without_review", [])
        if str(a or "").strip()
    }

    target_files = _collect_target_files(proposal)
    actions = _collect_actions(proposal)
    validation = _collect_validation(proposal)

    protected_touched = [p for p in target_files if p in protected_files]
    canonical_memory_touched = [p for p in target_files if _is_memory_path(p)]
    forbidden_action_hits = sorted(set(actions).intersection(forbidden_actions))

    errors: List[str] = []
    warnings: List[str] = []

    if "validation_bypass" in forbidden_action_hits or "regression_disable" in forbidden_action_hits:
        decision = DECISION_VALIDATION_BYPASS
        reason = "validation_bypass_detected"
        errors.append("proposal attempts to bypass or disable validation")
    elif canonical_memory_touched and not validation.get("backup_or_rollback_exists"):
        decision = DECISION_UNSAFE_MEMORY_WRITE
        reason = "canonical_memory_write_without_backup_or_rollback"
        errors.append("canonical memory target requires backup/rollback proof")
    elif protected_touched and not validation.get("two_eyes_passed"):
        decision = DECISION_FORBIDDEN_CORE_MUTATION
        reason = "protected_core_touched_without_two_eyes"
        errors.append("protected core mutation requires two eyes: local tests + regression")
    elif protected_touched and not validation.get("payload_preserved"):
        decision = DECISION_FORBIDDEN_CORE_MUTATION
        reason = "protected_core_touched_without_payload_preservation"
        errors.append("protected core mutation requires payload preservation proof")
    elif forbidden_action_hits and not validation.get("two_eyes_passed"):
        decision = DECISION_REJECT
        reason = "forbidden_action_requires_review"
        errors.append("forbidden action requested without two-eye validation")
    elif not validation.get("unit_tests_passed") or not validation.get("regression_passed"):
        decision = DECISION_NEEDS_SANDBOX
        reason = "sandbox_required_before_approval"
        warnings.append("proposal should pass local tests and regression before approval")
    else:
        decision = DECISION_APPROVE
        reason = "two_eyes_policy_satisfied"

    report = {
        "state": "D66_CORE_GUARD_REVIEWER",
        "result": f"D66_REVIEW_{decision}",
        "route": "FIELD_INTENT_CORE_GUARD_REVIEWER",
        "ok": decision == DECISION_APPROVE,
        "created_at": _now(),
        "decision": decision,
        "reason": reason,
        "policy_path": str(policy_path),
        "proposal_path": str(proposal_path or ""),
        "report_path": str(report_path),
        "target_files": target_files,
        "actions": actions,
        "protected_files_touched": protected_touched,
        "canonical_memory_touched": canonical_memory_touched,
        "forbidden_action_hits": forbidden_action_hits,
        "validation": {
            "ok": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            **validation,
        },
        "review_rules": {
            "protected_core_requires_two_eyes": True,
            "canonical_memory_requires_backup": True,
            "validation_bypass_rejected": True,
            "payload_preservation_required_for_core": True,
        },
        "success_condition": {
            "reviewer_executed": True,
            "decision_emitted": True,
            "runtime_code_mutated": False,
            "next_step": "If APPROVE, D64 may use this report as one guarded-apply input. If not, create sandbox/test evidence first.",
        },
        "raw_proposal": proposal,
    }

    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    result = review_core_mutation()
    print(json.dumps(result, ensure_ascii=False, indent=2))
'''

REVIEWER_PATH = Path("runtime_experimental/core_guard_reviewer.py")
REVIEWER_PATH.write_text(REVIEWER_CODE.lstrip(), encoding="utf-8")
print("created/updated", REVIEWER_PATH)


DISPATCHER_PATH = Path("app/orchestration/task_dispatcher.py")
if not DISPATCHER_PATH.exists():
    raise SystemExit(f"missing dispatcher: {DISPATCHER_PATH}")

text = DISPATCHER_PATH.read_text(encoding="utf-8")

HELPER_FUNC = r'''

def _run_field_intent_core_guard_review(task: Dict[str, Any]) -> Dict[str, Any]:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}

    policy_path = str(payload.get("policy_path") or "runtime_experimental/core_guard_policy.json")
    proposal_path = str(
        payload.get("proposal_path")
        or payload.get("patch_proposal_path")
        or payload.get("request_path")
        or ""
    ).strip()
    report_path = str(payload.get("report_path") or "reports/d66_core_guard_reviewer_report.json")

    proposal = payload.get("proposal")
    if not isinstance(proposal, dict):
        proposal = dict(payload)

    from runtime_experimental.core_guard_reviewer import review_core_mutation

    report = review_core_mutation(
        proposal=proposal,
        proposal_path=proposal_path or None,
        policy_path=policy_path,
        report_path=report_path,
    )

    decision = str(report.get("decision") or "REJECT")

    return {
        "route": "FIELD_INTENT_CORE_GUARD_REVIEWER",
        "ok": decision == "APPROVE",
        "reason": str(report.get("reason") or "").strip(),
        "problem": "field_intent_core_guard_review",
        "decision": decision,
        "policy_path": policy_path,
        "proposal_path": proposal_path,
        "report_path": report_path,
        "protected_files_touched": report.get("protected_files_touched", []),
        "canonical_memory_touched": report.get("canonical_memory_touched", []),
        "forbidden_action_hits": report.get("forbidden_action_hits", []),
        "execution": {
            "ok": True,
            "changed_files": [report_path],
            "actions": ["read_core_guard_policy", "review_mutation_proposal", "write_d66_review_report"],
            "note": "D66 reviewed proposal only. No runtime mutation executed.",
        },
        "validation": report.get("validation", {"ok": False, "errors": ["missing D66 validation"]}),
        "auto_commit": {
            "ok": False,
            "reason": "review_report_manual_commit",
        },
    }
'''

if "def _run_field_intent_core_guard_review(" not in text:
    anchor = "\ndef dispatch_task("
    if anchor not in text:
        raise SystemExit("Could not find def dispatch_task anchor")
    text = text.replace(anchor, HELPER_FUNC + anchor, 1)
    print("patched dispatcher helper")
else:
    print("dispatcher helper already present")

ROUTE_BLOCK = r'''    if problem == "field_intent_core_guard_review":
        return _run_field_intent_core_guard_review(task)

    if problem == "field_intent_core_guard_reviewer":
        return _run_field_intent_core_guard_review(task)

'''

if 'problem == "field_intent_core_guard_review"' not in text:
    anchors = [
        '    if problem == "field_intent_apoptosis_decay":\n',
        '    if problem == "field_intent_memory_priority_bias_probe":\n',
        '    if problem == "field_intent_closed_loop_memory_policy":\n',
        '    if problem in FIELD_INTENT_PROBLEMS:\n',
    ]
    inserted = False
    for anchor in anchors:
        if anchor in text:
            text = text.replace(anchor, ROUTE_BLOCK + anchor, 1)
            inserted = True
            print("patched dispatcher route before anchor:", anchor.strip())
            break
    if not inserted:
        raise SystemExit("Could not find route anchor for D66 reviewer")
else:
    print("dispatcher route already present")

DISPATCHER_PATH.write_text(text, encoding="utf-8")


TEST_CODE = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.core_guard_reviewer import review_core_mutation


POLICY = {
    "protected_files": [
        "runtime_experimental/v_kernel_daemon.py",
        "app/orchestration/task_dispatcher.py",
        "memory/field_intent_priority_bias.json",
    ],
    "forbidden_without_review": [
        "direct_core_edit",
        "validation_bypass",
        "canonical_memory_overwrite",
    ],
}


class TestD66CoreGuardReviewer(unittest.TestCase):
    def test_forbidden_core_mutation_without_two_eyes(self):
        with tempfile.TemporaryDirectory() as td:
            policy_path = Path(td) / "policy.json"
            report_path = Path(td) / "report.json"
            policy_path.write_text(json.dumps(POLICY), encoding="utf-8")

            proposal = {
                "target_files": ["app/orchestration/task_dispatcher.py"],
                "actions": ["direct_core_edit"],
                "validation": {
                    "unit_tests_passed": True,
                    "regression_passed": False,
                    "payload_preserved": True,
                },
            }

            report = review_core_mutation(
                proposal=proposal,
                policy_path=str(policy_path),
                report_path=str(report_path),
            )

            self.assertEqual(report["decision"], "FORBIDDEN_CORE_MUTATION")
            self.assertFalse(report["ok"])
            self.assertTrue(report_path.exists())

    def test_safe_isolated_module_with_two_eyes_approved(self):
        with tempfile.TemporaryDirectory() as td:
            policy_path = Path(td) / "policy.json"
            report_path = Path(td) / "report.json"
            policy_path.write_text(json.dumps(POLICY), encoding="utf-8")

            proposal = {
                "target_files": ["runtime_experimental/new_safe_policy.py"],
                "actions": ["create_isolated_module", "create_test"],
                "validation": {
                    "unit_tests_passed": True,
                    "regression_passed": True,
                    "daemon_smoke_passed": True,
                    "payload_preserved": True,
                    "backup_plan_exists": True,
                },
            }

            report = review_core_mutation(
                proposal=proposal,
                policy_path=str(policy_path),
                report_path=str(report_path),
            )

            self.assertEqual(report["decision"], "APPROVE")
            self.assertTrue(report["ok"])

    def test_memory_overwrite_without_backup_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            policy_path = Path(td) / "policy.json"
            report_path = Path(td) / "report.json"
            policy_path.write_text(json.dumps(POLICY), encoding="utf-8")

            proposal = {
                "target_files": ["memory/field_intent_priority_bias.json"],
                "actions": ["canonical_memory_overwrite"],
                "validation": {
                    "unit_tests_passed": True,
                    "regression_passed": True,
                    "payload_preserved": True,
                    "backup_plan_exists": False,
                },
            }

            report = review_core_mutation(
                proposal=proposal,
                policy_path=str(policy_path),
                report_path=str(report_path),
            )

            self.assertEqual(report["decision"], "UNSAFE_MEMORY_WRITE")
            self.assertFalse(report["ok"])


if __name__ == "__main__":
    unittest.main()
'''
TEST_PATH = Path("tests/test_d66_core_guard_reviewer.py")
TEST_PATH.write_text(TEST_CODE.lstrip(), encoding="utf-8")
print("created/updated", TEST_PATH)


print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", str(REVIEWER_PATH)], check=True)
sh([sys.executable, "-m", "py_compile", str(DISPATCHER_PATH)], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d66_core_guard_reviewer", "-v"], check=True)


print("\n== dispatcher probe ==")
probe_code = r'''
from pprint import pprint
from app.orchestration.task_dispatcher import build_kernel_state, ingest_event, dispatch_tick

state = build_kernel_state()

event = {
    "id": "d66_core_guard_reviewer_probe_001",
    "source": "v_kernel_d66",
    "priority": "critical",
    "payload": {
        "problem": "field_intent_core_guard_review",
        "bridge": "D66_FIELD_INTENT_CORE_GUARD_REVIEWER",
        "kind": "FIELD_INTENT_REVIEW_TASK",
        "intent": "REVIEW_CORE_MUTATION",
        "policy_path": "runtime_experimental/core_guard_policy.json",
        "report_path": "reports/d66_core_guard_reviewer_report.json",
        "proposal": {
            "target_files": ["app/orchestration/task_dispatcher.py"],
            "actions": ["direct_core_edit"],
            "validation": {
                "unit_tests_passed": True,
                "regression_passed": False,
                "payload_preserved": True
            }
        },
        "executor_hint": "TANK",
        "target_agent": "TANK",
    },
}

state = ingest_event(state, event)
state = dispatch_tick(state)

print("LAST ROUTE:", state.get("last_route"))
print("LAST PROBLEM:", state.get("last_problem"))
print("LAST RESULT:")
pprint(state.get("last_result"))
'''
subprocess.run([sys.executable, "-c", probe_code], check=True)


print("\n== report preview ==")
report_path = Path("reports/d66_core_guard_reviewer_report.json")
if report_path.exists():
    data = json.loads(report_path.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("RESULT:", data.get("result"))
    print("DECISION:", data.get("decision"))
    print("OK:", data.get("ok"))
    print("REASON:", data.get("reason"))


print("\n== git add/commit ==")
paths = [
    "app/orchestration/task_dispatcher.py",
    "runtime_experimental/core_guard_reviewer.py",
    "tests/test_d66_core_guard_reviewer.py",
    "reports/d66_core_guard_reviewer_report.json",
]

try:
    self_path = Path(__file__).resolve()
    rel = self_path.relative_to(ROOT)
    if rel.exists() and rel.name == "D66_CORE_GUARD_REVIEWER_BOOT.py":
        paths.append(str(rel))
except Exception:
    pass

for p in paths:
    if Path(p).exists():
        sh(["git", "add", "-f", p], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(
        ["git", "commit", "-m", "bridge: add D66 core guard reviewer"],
        text=True,
        capture_output=True,
    )
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D66 reviewer changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"], check=False)

print("\nD66 REVIEWER BOOT DONE")
