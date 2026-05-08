#!/usr/bin/env python3
# D104_FINAL_AUDIT_LEDGER_BOOT.py
#
# Creates D104 Final Audit Ledger.
#
# D104 validates D103 rollback evidence builder and creates:
# - final audit ledger
# - replay log index
# - guarded autonomy chain summary
# - terminal safety state
#
# D104 is documentation/audit only.
# It does NOT execute apply, rollback, restore, route insertion, protected-core mutation,
# network/AI calls, candidate deletion, or AI git actions.

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


MODULE = r"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D103_REPORT = "reports/d103_rollback_evidence_builder.json"
D103_BUNDLE = "reports/d103_rollback_evidence_bundle.json"
D103_RESTORE = "reports/d103_restore_point_reference.json"
D103_READY = "reports/d103_rollback_readiness_summary.json"
D103_SCOPE = "reports/d103_d104_final_audit_ledger_scope.json"

OUT = "reports/d104_final_audit_ledger.json"
REPLAY_OUT = "reports/d104_replay_log_index.json"
CHAIN_OUT = "reports/d104_guarded_autonomy_chain_summary.json"
TERMINAL_OUT = "reports/d104_terminal_safety_state.json"

REQ_D103_DECISION = "ROLLBACK_EVIDENCE_BUILDER_READY"
REQ_D104_GATE = "D104_FINAL_AUDIT_LEDGER"
REQ_D104_PHRASE = "APPROVE_D104_FINAL_AUDIT_LEDGER_ONLY"

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
    "actual_apply_by_ai",
    "route_insert_by_ai",
    "protected_core_mutation_by_ai",
    "canonical_memory_overwrite_by_ai",
    "external_ai_network_execution",
    "git_commit_or_push_by_ai",
    "execute_rollback_by_ai",
    "delete_runtime_candidate_by_ai",
    "run_manual_apply_now",
    "execute_post_fix_mutation",
    "execute_rollback_now",
    "restore_files_now",
    "delete_generated_candidate",
    "execute_final_apply",
    "mutate_chain_history",
]

ALLOWED = [
    "final_audit_ledger",
    "replay_log_index",
    "guarded_autonomy_chain_summary",
    "terminal_safety_state",
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
    raw = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def check_false_flags(label, data, errors):
    for key in FALSE_FLAGS:
        if data.get(key) is not False:
            errors.append(f"{label}.{key} must be false")


def validate_d103(d103, bundle, restore, ready, scope):
    errors = []
    warnings = []

    if not d103:
        return ["missing D103 rollback evidence builder report"], warnings

    if d103.get("ok") is not True:
        errors.append("D103 ok must be true")
    if d103.get("decision") != REQ_D103_DECISION:
        errors.append(f"D103 decision invalid: {d103.get('decision')}")

    guard = d103.get("guardrails") if isinstance(d103.get("guardrails"), dict) else {}
    check_false_flags("D103.guardrails", guard, errors)

    for key in ["rollback_executed", "restore_executed", "approval_for_real_apply"]:
        if guard.get(key) is not False:
            errors.append(f"D103 guardrails.{key} must be false")
    if guard.get("rollback_evidence_only") is not True:
        errors.append("D103 rollback_evidence_only must be true")

    builder = d103.get("rollback_evidence_builder") if isinstance(d103.get("rollback_evidence_builder"), dict) else {}
    if not builder:
        errors.append("D103 embedded rollback_evidence_builder missing")
    else:
        if builder.get("ok") is not True:
            errors.append("D103 builder ok must be true")
        if builder.get("next_required_gate") != REQ_D104_GATE:
            errors.append("D103 builder next_required_gate must be D104")
        for key in [
            "rollback_allowed_now",
            "restore_allowed_now",
            "apply_allowed_now",
            "route_insert_allowed_now",
            "protected_core_mutation_allowed_now",
        ]:
            if builder.get(key) is not False:
                errors.append(f"D103 builder {key} must be false")

    if not bundle:
        errors.append("missing D103 rollback evidence bundle")
    else:
        if bundle.get("ok") is not True:
            errors.append("D103 bundle ok must be true")
        if bundle.get("rollback_executed") is not False:
            errors.append("D103 bundle rollback_executed must be false")
        if bundle.get("restore_executed") is not False:
            errors.append("D103 bundle restore_executed must be false")

    if not restore:
        errors.append("missing D103 restore point reference")
    else:
        if restore.get("ok") is not True:
            errors.append("D103 restore ref ok must be true")
        if restore.get("restore_executed") is not False:
            errors.append("D103 restore_executed must be false")
        if restore.get("restore_point_created_by_script") is not False:
            errors.append("D103 restore_point_created_by_script must be false")
        if restore.get("human_review_required") is not True:
            errors.append("D103 restore human_review_required must be true")

    if not ready:
        errors.append("missing D103 rollback readiness summary")
    else:
        if ready.get("ok") is not True:
            errors.append("D103 readiness ok must be true")
        for key in [
            "rollback_executed",
            "restore_executed",
            "actual_apply_executed",
            "route_inserted",
            "protected_core_mutated",
            "canonical_memory_mutated",
            "external_ai_called",
            "network_accessed",
            "git_commit_by_ai",
        ]:
            if ready.get(key) is not False:
                errors.append(f"D103 readiness {key} must be false")
        if ready.get("ready_for_d104") is not True:
            errors.append("D103 readiness ready_for_d104 must be true")

    if not scope:
        errors.append("missing D103 D104 final audit ledger scope")
    else:
        if scope.get("ok") is not True:
            errors.append("D103 D104 scope ok must be true")
        if scope.get("allowed_next_gate") != REQ_D104_GATE:
            errors.append("D103 D104 scope allowed_next_gate must be D104")
        for item in ALLOWED:
            if item not in scope.get("d104_allowed_to_create", []):
                errors.append(f"D103 D104 scope missing allowed item: {item}")
        for item in FORBIDDEN:
            if item not in scope.get("d104_must_not_execute", []):
                errors.append(f"D103 D104 scope missing must-not-execute item: {item}")
        if scope.get("apply_allowed_after_d103") is not False:
            errors.append("D103 scope apply_allowed_after_d103 must be false")
        if scope.get("route_insert_allowed_after_d103") is not False:
            errors.append("D103 scope route_insert_allowed_after_d103 must be false")
        if scope.get("protected_core_mutation_allowed_after_d103") is not False:
            errors.append("D103 scope protected_core_mutation_allowed_after_d103 must be false")
        if scope.get("required_phrase_for_later_gate") != REQ_D104_PHRASE:
            errors.append("D103 scope required phrase invalid")

    return errors, warnings


def list_chain_reports(root: Path):
    reports = root / "reports"
    if not reports.exists():
        return []
    prefixes = tuple(f"d{i}_" for i in range(90, 105))
    return sorted(
        p.relative_to(root).as_posix()
        for p in reports.iterdir()
        if p.is_file() and p.name.startswith(prefixes)
    )


def build_replay_index(ledger_id, builder_id, root):
    chain_reports = list_chain_reports(root)
    return {
        "state": "D104_REPLAY_LOG_INDEX",
        "ok": True,
        "ledger_id": ledger_id,
        "builder_id": builder_id,
        "created_at": now(),
        "replay_mode": "AUDIT_REPLAY_INDEX_ONLY",
        "chain_reports_count": len(chain_reports),
        "chain_reports": chain_reports,
        "replay_commands_for_human_review_only": [
            "git log --oneline -20",
            "git status --short",
            "python -m unittest discover -s tests -v",
            "cat reports/d104_final_audit_ledger.json",
        ],
        "commands_executed_by_d104": [],
    }


def build_chain_summary(ledger_id, builder_id):
    chain = [
        "D90 Controlled Apply Plan",
        "D91 Explicit Apply Scope Approval",
        "D92 Guarded Apply Dry-Run Package",
        "D93 Dry-Run Recheck Gate",
        "D94 Final Execution Approval Request",
        "D95 Human Signed Execution Intent",
        "D96 Final Local Full Regression",
        "D97 Protected Core No-Touch Reconfirmation",
        "D98 Rollback Restore Command Pack",
        "D99 Final Guarded Execution Capsule",
        "D100 Controlled Human Execution Decision",
        "D101 One-Shot Manual Execution Capsule",
        "D102 Post-Execution Verifier",
        "D103 Rollback Evidence Builder",
        "D104 Final Audit Ledger",
    ]
    return {
        "state": "D104_GUARDED_AUTONOMY_CHAIN_SUMMARY",
        "ok": True,
        "ledger_id": ledger_id,
        "builder_id": builder_id,
        "created_at": now(),
        "chain": chain,
        "chain_length": len(chain),
        "core_rule": "AI proposes; system verifies; human approves; execution remains gated.",
        "current_terminal_status": "PRE_EXECUTION_AUDIT_CHAIN_SEALED",
        "real_apply_status": "BLOCKED",
        "ai_mode": "PROPOSE_ONLY",
    }


def build_terminal_safety_state(ledger_id, builder_id):
    return {
        "state": "D104_TERMINAL_SAFETY_STATE",
        "ok": True,
        "ledger_id": ledger_id,
        "builder_id": builder_id,
        "created_at": now(),
        "terminal_decision": "GUARDED_AUTONOMY_PRE_EXECUTION_CHAIN_SEALED",
        "actual_apply_executed": False,
        "route_inserted": False,
        "protected_core_mutated": False,
        "canonical_memory_mutated": False,
        "external_ai_called": False,
        "network_accessed": False,
        "git_commit_by_ai": False,
        "rollback_executed": False,
        "restore_executed": False,
        "ai_autonomous_execution_allowed": False,
        "human_review_required_for_any_future_execution": True,
        "safe_next_options": [
            "create README/update documentation",
            "start a new propose-only AI connector track",
            "create D105 optional audit dashboard",
            "stop here and tag the guarded chain",
        ],
    }


def create_final_audit_ledger(root="."):
    root = Path(root).resolve()

    d103 = read_json(root / D103_REPORT, {}) or {}
    bundle = read_json(root / D103_BUNDLE, {}) or {}
    restore = read_json(root / D103_RESTORE, {}) or {}
    ready = read_json(root / D103_READY, {}) or {}
    scope = read_json(root / D103_SCOPE, {}) or {}

    errors, warnings = validate_d103(d103, bundle, restore, ready, scope)

    builder_id = str(d103.get("builder_id") or bundle.get("builder_id") or restore.get("builder_id") or ready.get("builder_id") or scope.get("builder_id") or "")
    verifier_id = str(d103.get("verifier_id") or bundle.get("verifier_id") or restore.get("verifier_id") or scope.get("verifier_id") or "")
    capsule_id = str(d103.get("capsule_id") or bundle.get("capsule_id") or restore.get("capsule_id") or ready.get("capsule_id") or scope.get("capsule_id") or "")
    decision_id = str(d103.get("decision_id") or "")

    ledger_id = "d104-" + digest({
        "builder_id": builder_id,
        "verifier_id": verifier_id,
        "capsule_id": capsule_id,
        "decision_id": decision_id,
        "d103_decision": d103.get("decision"),
    })

    ok = not errors
    decision = "FINAL_AUDIT_LEDGER_READY" if ok else "FINAL_AUDIT_LEDGER_BLOCKED"
    result = "D104_FINAL_AUDIT_LEDGER_CREATED" if ok else "D104_FINAL_AUDIT_LEDGER_BLOCKED"

    replay = build_replay_index(ledger_id, builder_id, root)
    summary = build_chain_summary(ledger_id, builder_id)
    terminal = build_terminal_safety_state(ledger_id, builder_id)

    ledger = {
        "state": "D104_FINAL_AUDIT_LEDGER_ARTIFACT",
        "ok": True,
        "ledger_id": ledger_id,
        "builder_id": builder_id,
        "verifier_id": verifier_id,
        "capsule_id": capsule_id,
        "decision_id": decision_id,
        "created_at": now(),
        "mode": "FINAL_AUDIT_LEDGER_DOCUMENTATION_ONLY",
        "audits": [
            "D103 rollback evidence exists",
            "D103 restore point reference is reference-only",
            "D103 rollback readiness is ready for D104",
            "no actual apply executed",
            "no route insertion executed",
            "no protected-core mutation executed",
            "no rollback or restore executed",
            "no AI git action executed",
        ],
        "terminal_status": "PRE_EXECUTION_GUARDED_CHAIN_COMPLETE",
        "real_apply_allowed_now": False,
        "autonomous_ai_execution_allowed": False,
        "next_required_gate": "NONE_TERMINAL_AUDIT_STATE",
    }

    if ok:
        write_json(root / REPLAY_OUT, replay)
        write_json(root / CHAIN_OUT, summary)
        write_json(root / TERMINAL_OUT, terminal)

    report = {
        "state": "D104_FINAL_AUDIT_LEDGER",
        "result": result,
        "route": "FIELD_INTENT_FINAL_AUDIT_LEDGER",
        "ok": ok,
        "decision": decision,
        "created_at": now(),
        "ledger_id": ledger_id,
        "builder_id": builder_id,
        "verifier_id": verifier_id,
        "capsule_id": capsule_id,
        "decision_id": decision_id,
        "final_audit_ledger": ledger if ok else {},
        "replay_log_index": replay if ok else {},
        "guarded_autonomy_chain_summary": summary if ok else {},
        "terminal_safety_state": terminal if ok else {},
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
            "final_audit_only": True,
            "terminal_safety_state_created": ok,
            "approval_for_real_apply": False,
        },
        "validation": {
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        },
        "summary": {
            "decision": decision,
            "ledger_id": ledger_id,
            "builder_id": builder_id,
            "verifier_id": verifier_id,
            "capsule_id": capsule_id,
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "success_condition": {
            "final_audit_ledger_created": ok,
            "replay_log_index_created": ok,
            "guarded_autonomy_chain_summary_created": ok,
            "terminal_safety_state_created": ok,
            "actual_apply_executed": False,
            "rollback_executed": False,
            "restore_executed": False,
            "protected_core_untouched": True,
            "next_step": "Guarded pre-execution chain D90-D104 is sealed. Real apply remains blocked.",
        },
    }

    write_json(root / OUT, report)
    return report


if __name__ == "__main__":
    print(json.dumps(create_final_audit_ledger(), ensure_ascii=False, indent=2))
"""

TESTS = r"""
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.final_audit_ledger import create_final_audit_ledger


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data), encoding="utf-8")


class TestD104FinalAuditLedger(unittest.TestCase):
    def root(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "reports").mkdir()

        false_flags = {
            "external_ai_called": False,
            "network_accessed": False,
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "git_commit_by_ai": False,
        }

        write(root / "reports/d103_rollback_evidence_builder.json", {
            "ok": True,
            "decision": "ROLLBACK_EVIDENCE_BUILDER_READY",
            "builder_id": "d103-test",
            "verifier_id": "d102-test",
            "capsule_id": "d101-test",
            "decision_id": "d100-test",
            "rollback_evidence_builder": {
                "ok": True,
                "next_required_gate": "D104_FINAL_AUDIT_LEDGER",
                "rollback_allowed_now": False,
                "restore_allowed_now": False,
                "apply_allowed_now": False,
                "route_insert_allowed_now": False,
                "protected_core_mutation_allowed_now": False,
            },
            "guardrails": {
                **false_flags,
                "rollback_executed": False,
                "restore_executed": False,
                "rollback_evidence_only": True,
                "approval_for_real_apply": False,
            },
        })

        write(root / "reports/d103_rollback_evidence_bundle.json", {
            "ok": True,
            "builder_id": "d103-test",
            "verifier_id": "d102-test",
            "capsule_id": "d101-test",
            "rollback_executed": False,
            "restore_executed": False,
        })

        write(root / "reports/d103_restore_point_reference.json", {
            "ok": True,
            "builder_id": "d103-test",
            "verifier_id": "d102-test",
            "capsule_id": "d101-test",
            "restore_point_created_by_script": False,
            "restore_executed": False,
            "human_review_required": True,
        })

        write(root / "reports/d103_rollback_readiness_summary.json", {
            "ok": True,
            "builder_id": "d103-test",
            "verifier_id": "d102-test",
            "capsule_id": "d101-test",
            "rollback_executed": False,
            "restore_executed": False,
            "actual_apply_executed": False,
            "route_inserted": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "external_ai_called": False,
            "network_accessed": False,
            "git_commit_by_ai": False,
            "ready_for_d104": True,
        })

        write(root / "reports/d103_d104_final_audit_ledger_scope.json", {
            "ok": True,
            "builder_id": "d103-test",
            "verifier_id": "d102-test",
            "capsule_id": "d101-test",
            "allowed_next_gate": "D104_FINAL_AUDIT_LEDGER",
            "d104_allowed_to_create": [
                "final_audit_ledger",
                "replay_log_index",
                "guarded_autonomy_chain_summary",
                "terminal_safety_state",
            ],
            "d104_must_not_execute": [
                "actual_apply_by_ai",
                "route_insert_by_ai",
                "protected_core_mutation_by_ai",
                "canonical_memory_overwrite_by_ai",
                "external_ai_network_execution",
                "git_commit_or_push_by_ai",
                "execute_rollback_by_ai",
                "delete_runtime_candidate_by_ai",
                "run_manual_apply_now",
                "execute_post_fix_mutation",
                "execute_rollback_now",
                "restore_files_now",
                "delete_generated_candidate",
                "execute_final_apply",
                "mutate_chain_history",
            ],
            "apply_allowed_after_d103": False,
            "route_insert_allowed_after_d103": False,
            "protected_core_mutation_allowed_after_d103": False,
            "required_phrase_for_later_gate": "APPROVE_D104_FINAL_AUDIT_LEDGER_ONLY",
        })

        return td, root

    def test_creates_final_audit_only(self):
        td, root = self.root()
        try:
            r = create_final_audit_ledger(root)
            self.assertTrue(r["ok"])
            self.assertEqual(r["decision"], "FINAL_AUDIT_LEDGER_READY")
            self.assertTrue(r["guardrails"]["final_audit_only"])
            self.assertFalse(r["guardrails"]["approval_for_real_apply"])
            self.assertEqual(r["final_audit_ledger"]["next_required_gate"], "NONE_TERMINAL_AUDIT_STATE")
            self.assertEqual(r["terminal_safety_state"]["terminal_decision"], "GUARDED_AUTONOMY_PRE_EXECUTION_CHAIN_SEALED")
            self.assertTrue((root / "reports/d104_final_audit_ledger.json").exists())
            self.assertTrue((root / "reports/d104_replay_log_index.json").exists())
            self.assertTrue((root / "reports/d104_guarded_autonomy_chain_summary.json").exists())
            self.assertTrue((root / "reports/d104_terminal_safety_state.json").exists())
        finally:
            td.cleanup()

    def test_blocks_missing_d103(self):
        td, root = self.root()
        try:
            (root / "reports/d103_rollback_evidence_builder.json").unlink()
            r = create_final_audit_ledger(root)
            self.assertFalse(r["ok"])
            self.assertEqual(r["decision"], "FINAL_AUDIT_LEDGER_BLOCKED")
        finally:
            td.cleanup()

    def test_blocks_if_restore_executed(self):
        td, root = self.root()
        try:
            p = root / "reports/d103_restore_point_reference.json"
            data = json.loads(p.read_text())
            data["restore_executed"] = True
            p.write_text(json.dumps(data))
            r = create_final_audit_ledger(root)
            self.assertFalse(r["ok"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
"""


def sh(cmd, check=False):
    print("$", " ".join(cmd))
    return subprocess.run(cmd, text=True, capture_output=False, check=check)


def repo_root():
    here = Path.cwd()
    for p in [here, *here.parents]:
        if (p / ".git").exists():
            return p
    return here


ROOT = repo_root()
os.chdir(ROOT)
Path("runtime_experimental").mkdir(exist_ok=True)
Path("tests").mkdir(exist_ok=True)
Path("reports").mkdir(exist_ok=True)

print("D104 FINAL AUDIT LEDGER BOOT: repo =", ROOT)

Path("runtime_experimental/final_audit_ledger.py").write_text(MODULE, encoding="utf-8")
Path("tests/test_d104_final_audit_ledger.py").write_text(TESTS, encoding="utf-8")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/final_audit_ledger.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d104_final_audit_ledger", "-v"], check=True)

print("\n== run D104 ==")
subprocess.run([
    sys.executable, "-c",
    "from runtime_experimental.final_audit_ledger import create_final_audit_ledger\n"
    "r=create_final_audit_ledger()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
p = Path("reports/d104_final_audit_ledger.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    print("STATE:", d.get("state"))
    print("RESULT:", d.get("result"))
    print("OK:", d.get("ok"))
    print("DECISION:", d.get("decision"))
    print("SUMMARY:", d.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/final_audit_ledger.py",
    "tests/test_d104_final_audit_ledger.py",
    "reports/d104_final_audit_ledger.json",
    "reports/d104_replay_log_index.json",
    "reports/d104_guarded_autonomy_chain_summary.json",
    "reports/d104_terminal_safety_state.json",
]
try:
    self_rel = Path(__file__).resolve().relative_to(ROOT)
    if self_rel.name == "D104_FINAL_AUDIT_LEDGER_BOOT.py":
        paths.append(str(self_rel))
except Exception:
    pass

for item in paths:
    if Path(item).exists():
        sh(["git", "add", "-f", item], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D104 final audit ledger"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D104 changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"])
print("\nD104 FINAL AUDIT LEDGER BOOT DONE")
