#!/usr/bin/env python3
# D70_SANDBOX_BUNDLE_REVIEWER_BOOT.py
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
print("D70 SANDBOX BUNDLE REVIEWER BOOT: repo =", ROOT)

REVIEWER_CODE = 'from __future__ import annotations\n\nimport importlib.util\nimport json\nfrom datetime import datetime, timezone\nfrom pathlib import Path\nfrom typing import Any, Dict, List, Tuple\n\nDEFAULT_D69_BUNDLE = "reports/d69_sandbox_patch_bundle.json"\nDEFAULT_D69_REPORT = "reports/d69_sandbox_patch_write_report.json"\nDEFAULT_CORE_POLICY = "runtime_experimental/core_guard_policy.json"\nDEFAULT_OUTPUT = "reports/d70_sandbox_bundle_review.json"\n\nALLOWED_SANDBOX_PREFIXES = (\n    "runtime_experimental/ai_bypass_proposals/",\n    "reports/",\n    "tests/",\n)\n\n\ndef _now() -> str:\n    return datetime.now(timezone.utc).isoformat()\n\n\ndef _read_json(path: str | Path, default: Any = None) -> Any:\n    p = Path(path)\n    if not p.exists():\n        return default\n    try:\n        return json.loads(p.read_text(encoding="utf-8"))\n    except Exception:\n        return default\n\n\ndef _write_json(path: str | Path, data: Dict[str, Any]) -> None:\n    p = Path(path)\n    p.parent.mkdir(parents=True, exist_ok=True)\n    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")\n\n\ndef _safe_relative_path(path_value: str) -> str:\n    raw = str(path_value or "").strip().replace("\\\\", "/")\n    raw = raw.lstrip("/")\n    parts: List[str] = []\n    for part in raw.split("/"):\n        if not part or part == ".":\n            continue\n        if part == "..":\n            continue\n        parts.append(part)\n    return "/".join(parts)\n\n\ndef _is_allowed_sandbox_path(path_value: str) -> bool:\n    rel = _safe_relative_path(path_value)\n    return any(rel.startswith(prefix) for prefix in ALLOWED_SANDBOX_PREFIXES)\n\n\ndef _protected_files_from_policy(policy: Dict[str, Any]) -> List[str]:\n    for key in ("protected_files", "immutable_core", "core_files"):\n        value = policy.get(key)\n        if isinstance(value, list):\n            return [str(v) for v in value]\n    return []\n\n\ndef _module_name_from_path(path_value: str) -> str:\n    stem = Path(path_value).stem\n    cleaned = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in stem)\n    return cleaned or "sandbox_module"\n\n\ndef _probe_sandbox_file(root: Path, rel_path: str) -> Tuple[bool, str, Dict[str, Any]]:\n    rel = _safe_relative_path(rel_path)\n    path = root / rel\n    if not path.exists():\n        return False, "sandbox_file_missing", {}\n    if not rel.endswith(".py"):\n        return False, "sandbox_file_not_python", {}\n    try:\n        spec = importlib.util.spec_from_file_location(_module_name_from_path(rel), str(path))\n        if spec is None or spec.loader is None:\n            return False, "spec_loader_missing", {}\n        module = importlib.util.module_from_spec(spec)\n        spec.loader.exec_module(module)\n        if not hasattr(module, "run_sandbox_probe"):\n            return False, "run_sandbox_probe_missing", {}\n        result = module.run_sandbox_probe({"source": "D70_REVIEW"})\n        if not isinstance(result, dict):\n            return False, "probe_result_not_dict", {}\n        if result.get("ok") is not True:\n            return False, "probe_not_ok", result\n        if result.get("proposal_only") is not True:\n            return False, "proposal_only_flag_missing", result\n        if result.get("protected_core_mutated") is not False:\n            return False, "protected_core_mutation_flag_not_false", result\n        if result.get("canonical_memory_mutated") is not False:\n            return False, "canonical_memory_mutation_flag_not_false", result\n        return True, "probe_ok", result\n    except Exception as exc:\n        return False, f"probe_exception:{exc}", {}\n\n\ndef review_sandbox_bundle(\n    root: str | Path = ".",\n    d69_bundle_path: str = DEFAULT_D69_BUNDLE,\n    d69_report_path: str = DEFAULT_D69_REPORT,\n    core_policy_path: str = DEFAULT_CORE_POLICY,\n    output_path: str = DEFAULT_OUTPUT,\n) -> Dict[str, Any]:\n    root_path = Path(root).resolve()\n    bundle = _read_json(root_path / d69_bundle_path, default={}) or {}\n    d69_report = _read_json(root_path / d69_report_path, default={}) or {}\n    policy = _read_json(root_path / core_policy_path, default={}) or {}\n\n    errors: List[str] = []\n    warnings: List[str] = []\n    review_items: List[Dict[str, Any]] = []\n\n    if not bundle:\n        errors.append("D69 sandbox bundle missing or unreadable")\n    if not d69_report:\n        warnings.append("D69 write report missing or unreadable")\n    if not policy:\n        warnings.append("core guard policy missing or unreadable")\n\n    protected_files = _protected_files_from_policy(policy)\n    written_files_raw = bundle.get("written_files", [])\n    written_files = [str(x) for x in written_files_raw] if isinstance(written_files_raw, list) else []\n    if not written_files:\n        errors.append("D69 bundle has no written_files")\n\n    guardrails = bundle.get("guardrails", {}) if isinstance(bundle.get("guardrails"), dict) else {}\n    for key in ("runtime_code_mutated", "protected_core_mutated", "canonical_memory_mutated", "external_ai_called"):\n        if guardrails.get(key) is not False:\n            errors.append(f"guardrail_not_false:{key}")\n    if guardrails.get("sandbox_only") is not True:\n        errors.append("guardrail_sandbox_only_not_true")\n\n    d69_validation = d69_report.get("validation", {}) if isinstance(d69_report.get("validation"), dict) else {}\n    if d69_report and d69_validation.get("ok") is not True:\n        errors.append("D69 write report validation is not ok")\n    if bundle.get("ok") is not True:\n        errors.append("D69 bundle ok flag is not true")\n\n    bundle_probe_results = bundle.get("probe_results", [])\n    if isinstance(bundle_probe_results, list):\n        for item in bundle_probe_results:\n            if isinstance(item, dict) and item.get("ok") is not True:\n                errors.append(f"D69 probe failed for {item.get(\'path\')}: {item.get(\'reason\')}")\n    else:\n        errors.append("D69 bundle probe_results missing or invalid")\n\n    for rel_raw in written_files:\n        rel = _safe_relative_path(rel_raw)\n        item: Dict[str, Any] = {"path": rel, "checks": {}}\n        allowed = _is_allowed_sandbox_path(rel)\n        item["checks"]["allowed_sandbox_path"] = allowed\n        if not allowed:\n            errors.append(f"written file outside allowed sandbox prefixes: {rel}")\n        protected = rel in protected_files\n        item["checks"]["not_protected_file"] = not protected\n        if protected:\n            errors.append(f"written file is protected core: {rel}")\n        exists = (root_path / rel).exists()\n        item["checks"]["exists"] = exists\n        if not exists:\n            errors.append(f"written file missing on disk: {rel}")\n        if exists and rel.endswith(".py"):\n            probe_ok, probe_reason, probe_payload = _probe_sandbox_file(root_path, rel)\n            item["checks"]["probe_ok"] = probe_ok\n            item["checks"]["probe_reason"] = probe_reason\n            item["probe_payload"] = probe_payload\n            if not probe_ok:\n                errors.append(f"D70 probe failed for {rel}: {probe_reason}")\n        review_items.append(item)\n\n    approved = len(errors) == 0\n    decision = "APPROVE_SANDBOX_BUNDLE" if approved else "REJECT_SANDBOX_BUNDLE"\n    result = "D70_REVIEW_APPROVED" if approved else "D70_REVIEW_REJECTED"\n    report = {\n        "state": "D70_SANDBOX_BUNDLE_REVIEWER",\n        "result": result,\n        "route": "FIELD_INTENT_SANDBOX_BUNDLE_REVIEW",\n        "ok": approved,\n        "decision": decision,\n        "created_at": _now(),\n        "source_bundle": str(root_path / d69_bundle_path),\n        "source_report": str(root_path / d69_report_path),\n        "core_policy": str(root_path / core_policy_path),\n        "written_files": written_files,\n        "protected_files": protected_files,\n        "review_items": review_items,\n        "guardrails": {\n            "runtime_code_mutated": False,\n            "protected_core_mutated": False,\n            "canonical_memory_mutated": False,\n            "sandbox_only": True,\n            "external_ai_called": False,\n            "d64_apply_allowed": approved,\n        },\n        "validation": {"ok": approved, "errors": errors, "warnings": warnings},\n        "summary": {\n            "written_files_count": len(written_files),\n            "review_items_count": len(review_items),\n            "errors_count": len(errors),\n            "warnings_count": len(warnings),\n            "decision": decision,\n        },\n        "success_condition": {\n            "sandbox_bundle_reviewed": True,\n            "approved": approved,\n            "d64_may_consume_if_approved": approved,\n            "next_step": "D64 Safe Mutation Gate may consume this review only if decision is APPROVE_SANDBOX_BUNDLE.",\n        },\n    }\n    _write_json(root_path / output_path, report)\n    return report\n\n\nif __name__ == "__main__":\n    print(json.dumps(review_sandbox_bundle(), ensure_ascii=False, indent=2))\n'
TEST_CODE = 'import json\nimport tempfile\nimport unittest\nfrom pathlib import Path\n\nfrom runtime_experimental.sandbox_bundle_reviewer import review_sandbox_bundle\n\n\nSANDBOX_FILE = """\nfrom __future__ import annotations\n\ndef run_sandbox_probe(event=None):\n    return {\n        "ok": True,\n        "proposal_only": True,\n        "protected_core_mutated": False,\n        "canonical_memory_mutated": False,\n        "received": dict(event or {}),\n    }\n"""\n\n\nBAD_SANDBOX_FILE = """\nfrom __future__ import annotations\n\ndef run_sandbox_probe(event=None):\n    return {\n        "ok": False,\n        "proposal_only": False,\n        "protected_core_mutated": True,\n        "canonical_memory_mutated": False,\n    }\n"""\n\n\nclass TestD70SandboxBundleReviewer(unittest.TestCase):\n    def test_approves_valid_sandbox_bundle(self):\n        with tempfile.TemporaryDirectory() as td:\n            root = Path(td)\n            (root / "reports").mkdir(parents=True)\n            (root / "runtime_experimental/ai_bypass_proposals").mkdir(parents=True)\n            rel = "runtime_experimental/ai_bypass_proposals/dispatcher_bypass_proposal.py"\n            (root / rel).write_text(SANDBOX_FILE, encoding="utf-8")\n            (root / "runtime_experimental/core_guard_policy.json").parent.mkdir(parents=True, exist_ok=True)\n            (root / "runtime_experimental/core_guard_policy.json").write_text(\n                json.dumps({"protected_files": ["app/orchestration/task_dispatcher.py"]}),\n                encoding="utf-8",\n            )\n            (root / "reports/d69_sandbox_patch_bundle.json").write_text(\n                json.dumps({\n                    "ok": True,\n                    "written_files": [rel],\n                    "probe_results": [{"path": rel, "ok": True, "reason": "probe_ok"}],\n                    "guardrails": {\n                        "runtime_code_mutated": False,\n                        "protected_core_mutated": False,\n                        "canonical_memory_mutated": False,\n                        "sandbox_only": True,\n                        "external_ai_called": False,\n                    },\n                }),\n                encoding="utf-8",\n            )\n            (root / "reports/d69_sandbox_patch_write_report.json").write_text(\n                json.dumps({"validation": {"ok": True}}), encoding="utf-8"\n            )\n            report = review_sandbox_bundle(root=root)\n            self.assertTrue(report["ok"])\n            self.assertEqual(report["decision"], "APPROVE_SANDBOX_BUNDLE")\n            self.assertTrue(report["guardrails"]["d64_apply_allowed"])\n            self.assertTrue((root / "reports/d70_sandbox_bundle_review.json").exists())\n\n    def test_rejects_protected_or_bad_probe(self):\n        with tempfile.TemporaryDirectory() as td:\n            root = Path(td)\n            (root / "reports").mkdir(parents=True)\n            (root / "runtime_experimental/ai_bypass_proposals").mkdir(parents=True)\n            bad_rel = "runtime_experimental/ai_bypass_proposals/bad_proposal.py"\n            (root / bad_rel).write_text(BAD_SANDBOX_FILE, encoding="utf-8")\n            (root / "runtime_experimental/core_guard_policy.json").parent.mkdir(parents=True, exist_ok=True)\n            (root / "runtime_experimental/core_guard_policy.json").write_text(\n                json.dumps({"protected_files": ["app/orchestration/task_dispatcher.py"]}),\n                encoding="utf-8",\n            )\n            (root / "reports/d69_sandbox_patch_bundle.json").write_text(\n                json.dumps({\n                    "ok": True,\n                    "written_files": [bad_rel, "app/orchestration/task_dispatcher.py"],\n                    "probe_results": [{"path": bad_rel, "ok": True, "reason": "probe_ok"}],\n                    "guardrails": {\n                        "runtime_code_mutated": False,\n                        "protected_core_mutated": False,\n                        "canonical_memory_mutated": False,\n                        "sandbox_only": True,\n                        "external_ai_called": False,\n                    },\n                }),\n                encoding="utf-8",\n            )\n            report = review_sandbox_bundle(root=root)\n            self.assertFalse(report["ok"])\n            self.assertEqual(report["decision"], "REJECT_SANDBOX_BUNDLE")\n            self.assertFalse(report["guardrails"]["d64_apply_allowed"])\n            self.assertGreaterEqual(report["summary"]["errors_count"], 1)\n\n    def test_rejects_missing_bundle(self):\n        with tempfile.TemporaryDirectory() as td:\n            root = Path(td)\n            (root / "reports").mkdir(parents=True)\n            report = review_sandbox_bundle(root=root)\n            self.assertFalse(report["ok"])\n            self.assertEqual(report["decision"], "REJECT_SANDBOX_BUNDLE")\n            self.assertGreaterEqual(report["summary"]["errors_count"], 1)\n\n\nif __name__ == "__main__":\n    unittest.main()\n'

Path("runtime_experimental/sandbox_bundle_reviewer.py").write_text(REVIEWER_CODE, encoding="utf-8")
print("created/updated runtime_experimental/sandbox_bundle_reviewer.py")
Path("tests/test_d70_sandbox_bundle_reviewer.py").write_text(TEST_CODE, encoding="utf-8")
print("created/updated tests/test_d70_sandbox_bundle_reviewer.py")

print("\n== compile ==")
sh([sys.executable, "-m", "py_compile", "runtime_experimental/sandbox_bundle_reviewer.py"], check=True)

print("\n== unit tests ==")
sh([sys.executable, "-m", "unittest", "tests.test_d70_sandbox_bundle_reviewer", "-v"], check=True)

print("\n== run D70 sandbox bundle reviewer ==")
subprocess.run([
    sys.executable,
    "-c",
    "from runtime_experimental.sandbox_bundle_reviewer import review_sandbox_bundle\n"
    "r=review_sandbox_bundle()\n"
    "print('STATE:', r.get('state'))\n"
    "print('RESULT:', r.get('result'))\n"
    "print('OK:', r.get('ok'))\n"
    "print('DECISION:', r.get('decision'))\n"
    "print('SUMMARY:', r.get('summary'))\n",
], check=True)

print("\n== report preview ==")
rp = Path("reports/d70_sandbox_bundle_review.json")
if rp.exists():
    data = json.loads(rp.read_text(encoding="utf-8"))
    print("STATE:", data.get("state"))
    print("RESULT:", data.get("result"))
    print("OK:", data.get("ok"))
    print("DECISION:", data.get("decision"))
    print("SUMMARY:", data.get("summary"))

print("\n== git add/commit ==")
paths = [
    "runtime_experimental/sandbox_bundle_reviewer.py",
    "tests/test_d70_sandbox_bundle_reviewer.py",
    "reports/d70_sandbox_bundle_review.json",
]
try:
    self_path = Path(__file__).resolve()
    rel = self_path.relative_to(ROOT)
    if rel.exists() and rel.name == "D70_SANDBOX_BUNDLE_REVIEWER_BOOT.py":
        paths.append(str(rel))
except Exception:
    pass

for p in paths:
    if Path(p).exists():
        sh(["git", "add", "-f", p], check=False)

status = subprocess.run(["git", "status", "--porcelain", *paths], text=True, capture_output=True)
if status.stdout.strip():
    commit = subprocess.run(["git", "commit", "-m", "bridge: add D70 sandbox bundle reviewer"], text=True, capture_output=True)
    print(commit.stdout)
    if commit.stderr:
        print(commit.stderr)
else:
    print("No D70 sandbox bundle reviewer changes to commit.")

print("\n== final status ==")
sh(["git", "status", "--short"], check=False)
print("\nD70 SANDBOX BUNDLE REVIEWER BOOT DONE")
