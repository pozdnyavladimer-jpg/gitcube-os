#!/usr/bin/env python3
# D69_SANDBOX_PATCH_WRITER_BOOT.py
#
# Adds D69 Sandbox Patch Writer to GitCube OS.
#
# Run from repo root:
#     python D69_SANDBOX_PATCH_WRITER_BOOT.py
#
# Creates:
# - runtime_experimental/sandbox_patch_writer.py
# - tests/test_d69_sandbox_patch_writer.py
# - reports/d69_sandbox_patch_write_report.json
# - reports/d69_sandbox_patch_bundle.json
# - runtime_experimental/ai_bypass_proposals/*.py
#
# D69 does NOT call an external AI API.
# D69 does NOT patch task_dispatcher.py.
# D69 does NOT mutate protected core.
# D69 does NOT overwrite canonical memory.
#
# D69 consumes D68 proposal contract and writes sandbox-only bypass proposal files.

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
Path("runtime_experimental/ai_bypass_proposals").mkdir(parents=True, exist_ok=True)
Path("tests").mkdir(parents=True, exist_ok=True)
Path("reports").mkdir(parents=True, exist_ok=True)

print("D69 SANDBOX PATCH WRITER BOOT: repo =", ROOT)


WRITER_CODE = r'''
from __future__ import annotations

import importlib.util
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


DEFAULT_D68_PROPOSAL = "reports/d68_ai_patch_proposal.json"
DEFAULT_CORE_POLICY = "runtime_experimental/core_guard_policy.json"
DEFAULT_BUNDLE = "reports/d69_sandbox_patch_bundle.json"
DEFAULT_REPORT = "reports/d69_sandbox_patch_write_report.json"

ALLOWED_SANDBOX_PREFIXES = (
    "runtime_experimental/ai_bypass_proposals/",
    "reports/",
    "tests/",
)


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
    return value or "sandbox_proposal"


def _safe_relative_path(path_value: str) -> str:
    raw = str(path_value or "").strip().replace("\\", "/")
    raw = raw.lstrip("/")
    parts = []
    for part in raw.split("/"):
        if not part or part == ".":
            continue
        if part == "..":
            continue
        parts.append(part)
    return "/".join(parts)


def _is_allowed_sandbox_path(path_value: str) -> bool:
    p = _safe_relative_path(path_value)
    return any(p.startswith(prefix) for prefix in ALLOWED_SANDBOX_PREFIXES)


def _protected_files_from_policy(policy: Dict[str, Any]) -> List[str]:
    for key in ("protected_files", "immutable_core", "core_files"):
        value = policy.get(key)
        if isinstance(value, list):
            return [str(v) for v in value]
    return []


def _dedupe(items: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for item in items:
        if item and item not in seen:
            out.append(item)
            seen.add(item)
    return out


def _candidate_files_from_contract(contract: Dict[str, Any]) -> List[str]:
    candidates = contract.get("candidate_created_files")
    if isinstance(candidates, list):
        return [str(x) for x in candidates if x]

    payload = contract.get("llm_ready_payload")
    if isinstance(payload, dict):
        schema = payload.get("expected_json_schema")
        if isinstance(schema, dict):
            created = schema.get("created_files")
            if isinstance(created, list):
                return [str(x) for x in created if isinstance(x, str)]

    return []


def _hot_targets_from_contract(contract: Dict[str, Any]) -> List[str]:
    targets = contract.get("hot_targets")
    if isinstance(targets, list):
        return [str(x) for x in targets if x]
    return []


def _fallback_candidate_for_target(target: str) -> str:
    slug = _slug(target)
    if "task_dispatcher" in slug:
        return "runtime_experimental/ai_bypass_proposals/dispatcher_bypass_proposal.py"
    if "v_kernel_daemon" in slug:
        return "runtime_experimental/ai_bypass_proposals/daemon_bypass_proposal.py"
    if "phase_resync" in slug:
        return "runtime_experimental/ai_bypass_proposals/phase_resync_bypass_proposal.py"
    return f"runtime_experimental/ai_bypass_proposals/{slug}_bypass_proposal.py"


def _module_name_from_path(path_value: str) -> str:
    name = Path(path_value).stem
    return re.sub(r"[^a-zA-Z0-9_]", "_", name)


def _proposal_file_content(
    file_path: str,
    source_contract: Dict[str, Any],
    protected_files: List[str],
    hot_targets: List[str],
) -> str:
    module_name = _module_name_from_path(file_path)
    decision = str(source_contract.get("decision_source") or source_contract.get("summary", {}).get("decision") or "UNKNOWN")
    proposed_action = str(source_contract.get("proposed_action") or "CREATE_ISOLATED_BYPASS_MODULE")
    priority = str(source_contract.get("priority") or source_contract.get("summary", {}).get("priority") or "normal")

    payload = {
        "module": module_name,
        "state": "D69_SANDBOX_BYPASS_PROPOSAL",
        "decision_source": decision,
        "proposed_action": proposed_action,
        "priority": priority,
        "hot_targets": hot_targets,
        "protected_files": protected_files,
        "sandbox_file": file_path,
        "runtime_code_mutated": False,
        "protected_core_mutated": False,
        "canonical_memory_mutated": False,
        "proposal_only": True,
        "validation_gates": source_contract.get("validation_gates", []),
    }

    return f'''from __future__ import annotations

# Auto-generated by D69 Sandbox Patch Writer.
# This is a sandbox-only bypass proposal.
# It must not be imported into the live route until D66/D64 approve it.

from typing import Any, Dict


PROPOSAL = {json.dumps(payload, ensure_ascii=False, indent=2)}


def describe_proposal() -> Dict[str, Any]:
    return dict(PROPOSAL)


def run_sandbox_probe(event: Dict[str, Any] | None = None) -> Dict[str, Any]:
    event = dict(event or {{}})
    return {{
        "ok": True,
        "state": "D69_SANDBOX_PROBE_OK",
        "proposal_module": PROPOSAL.get("module"),
        "proposal_only": True,
        "runtime_code_mutated": False,
        "protected_core_mutated": False,
        "canonical_memory_mutated": False,
        "received_event_keys": sorted(event.keys()),
        "next_step": "D70 may review this sandbox proposal bundle before any guarded apply.",
    }}
'''


def _import_probe_python_file(root: Path, rel_path: str) -> Tuple[bool, str]:
    path = root / rel_path
    try:
        spec = importlib.util.spec_from_file_location(_module_name_from_path(rel_path), str(path))
        if spec is None or spec.loader is None:
            return False, "spec_loader_missing"
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if not hasattr(module, "run_sandbox_probe"):
            return False, "run_sandbox_probe_missing"
        result = module.run_sandbox_probe({"source": "d69_test"})
        if not isinstance(result, dict) or not result.get("ok"):
            return False, "probe_not_ok"
        if result.get("protected_core_mutated") is not False:
            return False, "protected_core_mutation_flag_not_false"
        return True, "probe_ok"
    except Exception as exc:
        return False, f"probe_exception:{exc}"


def write_sandbox_patch_bundle(
    root: str | Path = ".",
    d68_proposal_path: str = DEFAULT_D68_PROPOSAL,
    core_policy_path: str = DEFAULT_CORE_POLICY,
    bundle_path: str = DEFAULT_BUNDLE,
    report_path: str = DEFAULT_REPORT,
) -> Dict[str, Any]:
    root_path = Path(root).resolve()

    contract = _read_json(root_path / d68_proposal_path, default={}) or {}
    policy = _read_json(root_path / core_policy_path, default={}) or {}

    errors: List[str] = []
    warnings: List[str] = []

    if not contract:
        warnings.append("D68 proposal contract missing or unreadable")
    if not policy:
        warnings.append("core guard policy missing or unreadable")

    protected_files = _protected_files_from_policy(policy)
    hot_targets = _hot_targets_from_contract(contract)

    candidate_files = _candidate_files_from_contract(contract)
    if not candidate_files:
        candidate_files = [_fallback_candidate_for_target(t) for t in hot_targets]
    if not candidate_files:
        candidate_files = ["runtime_experimental/ai_bypass_proposals/monitor_only_bypass_proposal.py"]
        warnings.append("no candidate files found; created monitor-only sandbox proposal")

    candidate_files = _dedupe([_safe_relative_path(p) for p in candidate_files])

    safe_files: List[str] = []
    rejected_files: List[Dict[str, str]] = []

    for rel in candidate_files:
        if not _is_allowed_sandbox_path(rel):
            rejected_files.append({"path": rel, "reason": "outside_allowed_sandbox_prefix"})
            continue
        if rel in protected_files:
            rejected_files.append({"path": rel, "reason": "path_is_protected_core"})
            continue
        safe_files.append(rel)

    if not safe_files:
        safe_files = ["runtime_experimental/ai_bypass_proposals/monitor_only_bypass_proposal.py"]
        warnings.append("all requested files rejected; created monitor-only sandbox proposal")

    written_files: List[str] = []
    probe_results: List[Dict[str, Any]] = []

    for rel in safe_files:
        path = root_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        content = _proposal_file_content(
            file_path=rel,
            source_contract=contract,
            protected_files=protected_files,
            hot_targets=hot_targets,
        )
        path.write_text(content, encoding="utf-8")
        written_files.append(rel)

        ok, reason = _import_probe_python_file(root_path, rel)
        probe_results.append({"path": rel, "ok": ok, "reason": reason})
        if not ok:
            errors.append(f"probe failed for {rel}: {reason}")

    bundle = {
        "state": "D69_SANDBOX_PATCH_BUNDLE",
        "result": "SANDBOX_PATCH_BUNDLE_CREATED",
        "route": "FIELD_INTENT_SANDBOX_PATCH_WRITER",
        "ok": len(errors) == 0,
        "created_at": _now(),
        "source_contract": str(root_path / d68_proposal_path),
        "written_files": written_files,
        "rejected_files": rejected_files,
        "probe_results": probe_results,
        "hot_targets": hot_targets,
        "protected_files": protected_files,
        "guardrails": {
            "runtime_code_mutated": False,
            "protected_core_mutated": False,
            "canonical_memory_mutated": False,
            "sandbox_only": True,
            "external_ai_called": False,
        },
        "validation_gates": [
            "SANDBOX_ONLY_PATHS",
            "PYTHON_IMPORT_PROBE",
            "NO_PROTECTED_CORE_MUTATION",
            "NO_CANONICAL_MEMORY_OVERWRITE",
            "D70_REVIEW_REQUIRED_BEFORE_APPLY",
        ],
        "next_step": "D70 may review this sandbox bundle before D64 guarded apply.",
    }

    _write_json(root_path / bundle_path, bundle)

    report = {
        "state": "D69_SANDBOX_PATCH_WRITER",
        "result": "SANDBOX_PATCH_WRITE_COMPLETED",
        "route": "FIELD_INTENT_SANDBOX_PATCH_WRITER",
        "ok": len(errors) == 0,
        "created_at": _now(),
        "proposal_path": str(root_path / d68_proposal_path),
        "bundle_path": str(root_path / bundle_path),
        "report_path": str(root_path / report_path),
        "written_files": written_files,
        "rejected_files": rejected_files,
        "probe_results": probe_results,
        "summary": {
            "written_files_count": len(written_files),
            "rejected_files_count": len(rejected_files),
            "probe_ok_count": len([p for p in probe_results if p.get("ok")]),
            "warnings_count": len(warnings),
            "errors_count": len(errors),
        },
        "validation": {
            "ok": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        },
        "success_condition": {
            "sandbox_files_written": len(written_files) > 0,
            "sandbox_only": True,
            "protected_core_untouched": True,
            "canonical_memory_untouched": True,
            "next_step": "D70 should review the sandbox patch bundle and emit approve/reject evidence.",
        },
    }

    _write_json(root_path / report_path, report)
    return report


if __name__ == "__main__":
    print(json.dumps(write_sandbox_patch_bundle(), ensure_ascii=False, indent=2))
'''

Path("runtime_experimental/sandbox_patch_writer.py").write_text(WRITER_CODE.lstrip(), encoding="utf-8")
print("created/updated runtime_experimental/sandbox_patch_writer.py")


TEST_CODE = r'''
import json
import tempfile
import unittest
from pathlib import Path

from runtime_experimental.sandbox_patch_writer import write_sandbox_patch_bundle


class TestD69SandboxPatchWriter(unittest.TestCase):
    def test_writes_sandbox_files_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "reports").mkdir(parents=True)
            (root / "runtime_experimental").mkdir(parents=True)

            (root / "runtime_experimental/core_guard_policy.json").write_text(
                json.dumps(
                    {
                        "protected_files": [
                            "app/orchestration/task_dispatcher.py",
                            "runtime_experimental/v_kernel_daemon.py",
                        ]
                    }
                ),
                encoding="utf-8",
            )

            (root / "reports/d68_ai_patch_proposal.json").write_text(
                json.dumps(
                    {
                        "state": "D68_AI_PATCH_PROPOSAL",
                        "proposed_action": "CREATE_ISOLATED_BYPASS_MODULE",
                        "decision_source": "PLAN_ISOLATED_BYPASS",
                        "priority": "critical",
                        "hot_targets": ["app/orchestration/task_dispatcher.py"],
                        "candidate_created_files": [
                            "runtime_experimental/ai_bypass_proposals/dispatcher_bypass_proposal.py"
                        ],
                        "validation_gates": ["D66_CORE_GUARD_REVIEW_REQUIRED"],
                    }
                ),
                encoding="utf-8",
            )

            report = write_sandbox_patch_bundle(root=root)

            self.assertTrue(report["ok"])
            self.assertEqual(report["summary"]["written_files_count"], 1)
            self.assertTrue((root / "runtime_experimental/ai_bypass_proposals/dispatcher_bypass_proposal.py").exists())
            self.assertFalse((root / "app/orchestration/task_dispatcher.py").exists())
            self.assertTrue(report["success_condition"]["protected_core_untouched"])
            self.assertTrue(report["success_condition"]["canonical_memory_untouched"])

    def test_rejects_candidate_outside_sandbox(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "reports").mkdir(parents=True)
            (root / "runtime_experimental").mkdir(parents=True)

            (root / "runtime_experimental/core_guard_policy.json").write_text(
                json.dumps({"protected_files": ["app/orchestration/task_dispatcher.py"]}),
                encoding="utf-8",
            )

            (root / "reports/d68_ai_patch_proposal.json").write_text(
                json.dumps(
                    {
                        "state": "D68_AI_PATCH_PROPOSAL",
                        "candidate_created_files": [
                            "app/orchestration/task_dispatcher.py"
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = write_sandbox_patch_bundle(root=root)

            self.assertTrue(report["ok"])
            self.assertGreaterEqual(report["summary"]["rejected_files_count"], 1)
            self.assertTrue((root / "runtime_experimental/ai_bypass_proposals/monitor_only_bypass_proposal.py").exists())
            self.assertFalse((root / "app/orchestration/task_dispatcher.py").exists())

    def test_missing_contract_creates_monitor_only_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "reports").mkdir(parents=True)

            report = write_sandbox_patch_bundle(root=root)

            self.assertTrue(report["ok"])
            self.assertGreaterEqual(report["summary"]["warnings_count"], 1)
            self.assertTrue(report["success_condition"]["sandbox_files_written"])


if __name__ == "__main__":
    unittest.main()
'''

Path("tests/test_d69_sandbox_patch_writer.py").write_text(TEST_CODE.lstrip(), encoding="utf-8")
print("created/updated tests/test_d69_sandbox_patch_writer.py")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_patch_writer.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d69_sandbox_patch_writer", "-v"], check=True)

print("\n== run D69 sandbox writer ==")
subprocess.run(
    [
        sys.executable,
        "-c",
        "from runtime_experimental.sandbox_patch_writer import write_sandbox_patch_bundle\n"
        "r=write_sandbox_patch_bundle()\n"
        "print('STATE:', r.get('state'))\n"
        "print('RESULT:', r.get('result'))\n"
        "print('OK:', r.get('ok'))\n"
        "print('SUMMARY:', r.get('summary'))\n"
        "print('WRITTEN_FILES:', r.get('written_files'))\n",
    ],
    check=True,
)

print("\n== report preview ==")
rp = Path("reports/d69_sandbox_patch_write_report.json")
if rp.exists():
    data = json.loads(rp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("RESULT:", data.get("result"))
    print("OK:", data.get("ok"))
    print("SUMMARY:", data.get("summary"))
    print("WRITTEN_FILES:", data.get("written_files"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_patch_writer.py",
    "tests/test_d69_sandbox_patch_writer.py",
    "reports/d69_sandbox_patch_write_report.json",
    "reports/d69_sandbox_patch_bundle.json",
]

# Add generated sandbox proposal files if they exist.
proposal_dir = Path("runtime_experimental/ai_bypass_proposals")
if proposal_dir.exists():
    paths += [str(p) for p in proposal_dir.glob("*.py")]

try:
    self_path = Path(__file__).resolve()
    rel = self_path.relative_to(ROOT)
    if rel.exists() and rel.name == "D69_SANDBOX_PATCH_WRITER_BOOT.py":
        paths.append(str(rel))
except Exception:
    pass

for p in paths:
    if Path(p).exists():
        sh(["git", "add", "-f", p], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D69 sandbox patch writer"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D69 sandbox patch writer changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"], check=False)
print("\nD69 SANDBOX PATCH WRITER BOOT DONE")
