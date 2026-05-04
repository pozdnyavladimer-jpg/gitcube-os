#!/usr/bin/env python3
# D68_AI_PATCH_PROPOSAL_ADAPTER_BOOT.py
#
# Adds D68 AI Patch Proposal Adapter to GitCube OS.
# Run from repo root:
#   python D68_AI_PATCH_PROPOSAL_ADAPTER_BOOT.py
#
# Creates:
# - runtime_experimental/ai_patch_proposal_adapter.py
# - tests/test_d68_ai_patch_proposal_adapter.py
# - reports/d68_ai_patch_proposal.json
#
# D68 does NOT call an external AI API.
# D68 does NOT patch task_dispatcher.py.
# D68 does NOT mutate runtime code, protected core, or canonical memory.

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

Path("runtime_experimental").mkdir(parents=True, exist_ok=True)
Path("tests").mkdir(parents=True, exist_ok=True)
Path("reports").mkdir(parents=True, exist_ok=True)

print("D68 AI PATCH PROPOSAL ADAPTER BOOT: repo =", ROOT)

ADAPTER_CODE = '''
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_D63_REPORT = "reports/d63_field_memory_replay_report.json"
DEFAULT_D67_MAP = "reports/d67_topological_memory_map.json"
DEFAULT_D67_REPORT = "reports/d67_topological_memory_map_report.json"
DEFAULT_D66_REVIEWER_REPORT = "reports/d66_core_guard_reviewer_report.json"
DEFAULT_CORE_POLICY = "runtime_experimental/core_guard_policy.json"
DEFAULT_OUTPUT = "reports/d68_ai_patch_proposal.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: str | Path, data: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _slug(value: str) -> str:
    value = str(value or "").strip().lower()
    value = re.sub(r"[^a-z0-9_./-]+", "_", value)
    value = value.replace("/", "_").replace(".", "_")
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "proposal"


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _protected_files_from_policy(policy: Dict[str, Any]) -> List[str]:
    for key in ("protected_files", "immutable_core", "core_files"):
        value = policy.get(key)
        if isinstance(value, list):
            return [str(v) for v in value]
    return []


def _extract_d67_moves(d67_map: Dict[str, Any], d67_report: Dict[str, Any]) -> List[Dict[str, Any]]:
    for source in (d67_map, d67_report):
        if isinstance(source.get("suggested_moves"), list):
            return [m for m in source["suggested_moves"] if isinstance(m, dict)]
        if isinstance(source.get("top_suggested_moves"), list):
            return [m for m in source["top_suggested_moves"] if isinstance(m, dict)]
    return []


def _extract_hot_targets(d63_report: Dict[str, Any], d67_moves: List[Dict[str, Any]]) -> List[str]:
    macro = d63_report.get("macro_decision") if isinstance(d63_report, dict) else {}
    targets: List[str] = []
    if isinstance(macro, dict):
        for t in _as_list(macro.get("targets")):
            if t:
                targets.append(str(t))
    for move in d67_moves:
        target = move.get("target")
        if target:
            targets.append(str(target))
    out: List[str] = []
    seen = set()
    for item in targets:
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out


def _candidate_module_for_target(target: str) -> str:
    slug = _slug(target)
    if "task_dispatcher" in slug:
        return "runtime_experimental/ai_bypass_proposals/dispatcher_bypass_proposal.py"
    if "v_kernel_daemon" in slug:
        return "runtime_experimental/ai_bypass_proposals/daemon_bypass_proposal.py"
    if "phase_resync" in slug:
        return "runtime_experimental/ai_bypass_proposals/phase_resync_bypass_proposal.py"
    return f"runtime_experimental/ai_bypass_proposals/{slug}_bypass_proposal.py"


def _proposal_prompt(macro_decision: Dict[str, Any], hot_targets: List[str], protected_files: List[str], candidate_files: List[str]) -> str:
    return (
        "You are an AI patch proposal agent for GitCube OS. "
        "Create a patch proposal only. Do not mutate code. "
        "Follow D66 core guard rules. Protected core must not be edited directly. "
        "Use TENUKI: create an isolated bypass module and tests. "
        "Return JSON only with target_files, created_files, test_plan, rollback_plan, and validation_gates. "
        f"Macro decision: {macro_decision}. "
        f"Hot targets: {hot_targets}. "
        f"Protected files: {protected_files}. "
        f"Allowed candidate files: {candidate_files}."
    )


def build_ai_patch_proposal(
    root: str | Path = ".",
    d63_report_path: str = DEFAULT_D63_REPORT,
    d67_map_path: str = DEFAULT_D67_MAP,
    d67_report_path: str = DEFAULT_D67_REPORT,
    d66_reviewer_report_path: str = DEFAULT_D66_REVIEWER_REPORT,
    core_policy_path: str = DEFAULT_CORE_POLICY,
    output_path: str = DEFAULT_OUTPUT,
) -> Dict[str, Any]:
    root_path = Path(root).resolve()
    d63 = _read_json(root_path / d63_report_path, default={}) or {}
    d67_map = _read_json(root_path / d67_map_path, default={}) or {}
    d67_report = _read_json(root_path / d67_report_path, default={}) or {}
    d66_report = _read_json(root_path / d66_reviewer_report_path, default={}) or {}
    core_policy = _read_json(root_path / core_policy_path, default={}) or {}

    warnings: List[str] = []
    errors: List[str] = []
    if not d63:
        warnings.append("D63 replay report missing or unreadable")
    if not d67_map and not d67_report:
        warnings.append("D67 topology map/report missing or unreadable")
    if not d66_report:
        warnings.append("D66 reviewer report missing or unreadable")
    if not core_policy:
        warnings.append("core guard policy missing or unreadable")

    macro_decision = d63.get("macro_decision") if isinstance(d63.get("macro_decision"), dict) else {}
    decision = str(macro_decision.get("decision") or "HOLD_AND_MONITOR")
    priority = str(macro_decision.get("priority") or "normal")
    d67_moves = _extract_d67_moves(d67_map, d67_report)
    hot_targets = _extract_hot_targets(d63, d67_moves)
    protected_files = _protected_files_from_policy(core_policy)

    if not hot_targets:
        hot_targets = ["runtime_experimental/unknown_hotspot.py"]
        warnings.append("no hot targets found; using placeholder proposal target")

    candidate_files = list(dict.fromkeys(_candidate_module_for_target(t) for t in hot_targets))

    forbidden_actions = [
        "direct_core_edit",
        "overwrite_canonical_memory",
        "write_to_protected_file",
        "auto_commit_without_review",
        "execute_generated_patch_without_tests",
    ]
    validation_gates = [
        "D66_CORE_GUARD_REVIEW_REQUIRED",
        "UNIT_TESTS_REQUIRED",
        "REGRESSION_TESTS_REQUIRED",
        "NO_PROTECTED_CORE_MUTATION",
        "NO_CANONICAL_MEMORY_OVERWRITE",
        "ROLLBACK_PLAN_REQUIRED",
    ]

    if decision == "PLAN_ISOLATED_BYPASS":
        proposal_mode = "AI_PROPOSAL_ONLY_ISOLATED_BYPASS"
        proposed_action = "CREATE_ISOLATED_BYPASS_MODULE"
        rationale = "D63/D67 recommend TENUKI around stressed protected core."
    elif decision == "HOLD_CORE_LOCK":
        proposal_mode = "AI_PROPOSAL_ONLY_CORE_LOCK"
        proposed_action = "DESIGN_SANDBOX_ONLY_PROPOSAL"
        rationale = "D66 indicates core mutation risk; hold protected core lock."
    elif decision == "REVIEW_APOPTOSIS_DECAY_CANDIDATE":
        proposal_mode = "AI_PROPOSAL_ONLY_MEMORY_DECAY_REVIEW"
        proposed_action = "REVIEW_DECAYED_MEMORY_CANDIDATE"
        rationale = "D65 produced memory decay candidate requiring guard review."
    else:
        proposal_mode = "AI_PROPOSAL_ONLY_MONITOR"
        proposed_action = "NO_CODE_CHANGE_MONITOR"
        rationale = "No safe mutation action required."

    proposal = {
        "state": "D68_AI_PATCH_PROPOSAL",
        "result": "AI_PATCH_PROPOSAL_CONTRACT_CREATED",
        "route": "FIELD_INTENT_AI_PATCH_PROPOSAL_ADAPTER",
        "ok": len(errors) == 0,
        "created_at": _now(),
        "proposal_mode": proposal_mode,
        "proposed_action": proposed_action,
        "priority": priority,
        "decision_source": decision,
        "rationale": rationale,
        "hot_targets": hot_targets,
        "protected_files": protected_files,
        "candidate_created_files": candidate_files,
        "forbidden_actions": forbidden_actions,
        "validation_gates": validation_gates,
        "llm_ready_payload": {
            "system_contract": "Proposal only. Return JSON. Do not write files. Do not mutate protected core. Do not overwrite canonical memory.",
            "prompt": _proposal_prompt(macro_decision, hot_targets, protected_files, candidate_files),
            "expected_json_schema": {
                "proposal_name": "string",
                "intent": "string",
                "target_files": ["string"],
                "created_files": ["string"],
                "protected_files_not_touched": True,
                "test_plan": ["string"],
                "rollback_plan": ["string"],
                "validation_gates": ["string"],
                "risk_level": "low|medium|high|critical",
            },
        },
        "guardrails": {
            "runtime_code_mutated": False,
            "canonical_memory_mutated": False,
            "protected_core_mutated": False,
            "external_ai_called": False,
            "proposal_only": True,
        },
        "input_reports": {
            "d63_report_path": str(root_path / d63_report_path),
            "d67_map_path": str(root_path / d67_map_path),
            "d67_report_path": str(root_path / d67_report_path),
            "d66_reviewer_report_path": str(root_path / d66_reviewer_report_path),
            "core_policy_path": str(root_path / core_policy_path),
        },
        "summary": {
            "decision": decision,
            "priority": priority,
            "hot_targets_count": len(hot_targets),
            "candidate_files_count": len(candidate_files),
            "validation_gates_count": len(validation_gates),
            "warnings_count": len(warnings),
            "errors_count": len(errors),
        },
        "validation": {"ok": len(errors) == 0, "errors": errors, "warnings": warnings},
        "success_condition": {
            "proposal_contract_created": True,
            "ai_can_read_this_report": True,
            "ai_cannot_mutate_code_from_this_step": True,
            "next_step": "D69 may consume this contract and write sandbox-only files after D66-compatible checks.",
        },
    }
    _write_json(root_path / output_path, proposal)
    return proposal


if __name__ == "__main__":
    print(json.dumps(build_ai_patch_proposal(), ensure_ascii=False, indent=2))
'''

Path("runtime_experimental/ai_patch_proposal_adapter.py").write_text(ADAPTER_CODE.lstrip(), encoding="utf-8")
print("created/updated runtime_experimental/ai_patch_proposal_adapter.py")

TEST_CODE = '''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.ai_patch_proposal_adapter import build_ai_patch_proposal


class TestD68AIPatchProposalAdapter(unittest.TestCase):
    def test_builds_isolated_bypass_contract_without_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "reports").mkdir(parents=True)
            (root / "runtime_experimental").mkdir(parents=True)
            (root / "reports/d63_field_memory_replay_report.json").write_text(
                json.dumps({"macro_decision": {"decision": "PLAN_ISOLATED_BYPASS", "priority": "critical", "targets": ["app/orchestration/task_dispatcher.py", "runtime_experimental/v_kernel_daemon.py"]}}),
                encoding="utf-8",
            )
            (root / "reports/d67_topological_memory_map.json").write_text(
                json.dumps({"suggested_moves": [{"target": "app/orchestration/task_dispatcher.py", "move_type": "TENUKI", "protected_core": True, "pain_score": 0.8125}]}),
                encoding="utf-8",
            )
            (root / "reports/d66_core_guard_reviewer_report.json").write_text(
                json.dumps({"decision": "FORBIDDEN_CORE_MUTATION", "ok": False}), encoding="utf-8"
            )
            (root / "runtime_experimental/core_guard_policy.json").write_text(
                json.dumps({"protected_files": ["app/orchestration/task_dispatcher.py"]}), encoding="utf-8"
            )
            report = build_ai_patch_proposal(root=root, output_path="reports/d68_ai_patch_proposal.json")
            self.assertTrue(report["ok"])
            self.assertEqual(report["proposed_action"], "CREATE_ISOLATED_BYPASS_MODULE")
            self.assertTrue(report["guardrails"]["proposal_only"])
            self.assertFalse(report["guardrails"]["external_ai_called"])
            self.assertFalse(report["guardrails"]["protected_core_mutated"])
            self.assertIn("D66_CORE_GUARD_REVIEW_REQUIRED", report["validation_gates"])
            self.assertTrue((root / "reports/d68_ai_patch_proposal.json").exists())

    def test_missing_inputs_still_creates_hold_contract(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "reports").mkdir(parents=True)
            report = build_ai_patch_proposal(root=root, output_path="reports/d68_ai_patch_proposal.json")
            self.assertTrue(report["ok"])
            self.assertEqual(report["proposed_action"], "NO_CODE_CHANGE_MONITOR")
            self.assertGreaterEqual(report["summary"]["warnings_count"], 1)
            self.assertTrue(report["success_condition"]["proposal_contract_created"])


if __name__ == "__main__":
    unittest.main()
'''

Path("tests/test_d68_ai_patch_proposal_adapter.py").write_text(TEST_CODE.lstrip(), encoding="utf-8")
print("created/updated tests/test_d68_ai_patch_proposal_adapter.py")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/ai_patch_proposal_adapter.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d68_ai_patch_proposal_adapter", "-v"], check=True)

print("\n== run D68 proposal adapter ==")
subprocess.run(
    [
        sys.executable,
        "-c",
        "from runtime_experimental.ai_patch_proposal_adapter import build_ai_patch_proposal\n"
        "r=build_ai_patch_proposal()\n"
        "print('STATE:', r.get('state'))\n"
        "print('RESULT:', r.get('result'))\n"
        "print('OK:', r.get('ok'))\n"
        "print('SUMMARY:', r.get('summary'))\n"
        "print('PROPOSED_ACTION:', r.get('proposed_action'))\n"
        "print('CANDIDATE_FILES:', r.get('candidate_created_files'))\n",
    ],
    check=True,
)

print("\n== report preview ==")
rp = Path("reports/d68_ai_patch_proposal.json")
if rp.exists():
    data = json.loads(rp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("RESULT:", data.get("result"))
    print("OK:", data.get("ok"))
    print("SUMMARY:", data.get("summary"))
    print("PROPOSED_ACTION:", data.get("proposed_action"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/ai_patch_proposal_adapter.py",
    "tests/test_d68_ai_patch_proposal_adapter.py",
    "reports/d68_ai_patch_proposal.json",
]
try:
    self_path = Path(__file__).resolve()
    rel = self_path.relative_to(ROOT)
    if rel.exists() and rel.name == "D68_AI_PATCH_PROPOSAL_ADAPTER_BOOT.py":
        paths.append(str(rel))
except Exception:
    pass

for p in paths:
    if Path(p).exists():
        sh(["git", "add", "-f", p], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D68 AI patch proposal adapter"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D68 AI patch proposal changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"], check=False)
print("\nD68 AI PATCH PROPOSAL ADAPTER BOOT DONE")
