from __future__ import annotations

import os
import shutil
from typing import Dict, Any, List


def build_prompt(task: Dict[str, Any], original_content: str, path: str) -> str:
    problem = str(task.get("problem", "")).strip()
    return f"""Task type: {problem}
Target file: {path}

Allowed actions:
- fix obviously broken imports
- comment out clearly invalid imports
- keep relative imports intact
- preserve unrelated code

Forbidden actions:
- delete unrelated logic
- rename public APIs
- rewrite the whole file without need

Return only corrected file content.
"""


def request_fix(prompt: str, original_content: str) -> str:
    lines = original_content.splitlines()
    fixed = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("import "):
            if "." not in stripped and any(
                bad in stripped for bad in ["app.", "core.", "runtime_experimental.", "bridges."]
            ):
                fixed.append(f"# FIXME broken import: {line}")
                continue

        if stripped.startswith("from ") and " import " in stripped:
            parts = stripped.split()
            if len(parts) >= 4:
                module = parts[1]

                if module.startswith(("app.", "core.", "runtime_experimental.", "bridges.")):
                    fixed.append(line)
                    continue

                if module in {"os", "sys", "json", "math", "typing", "pathlib", "subprocess"}:
                    fixed.append(line)
                    continue

                fixed.append(f"# FIXME broken import: {line}")
                continue

        fixed.append(line)

    result = "\n".join(fixed)
    if original_content.endswith("\n"):
        result += "\n"
    return result


def make_backup(path: str) -> str:
    backup_path = f"{path}.bak"
    shutil.copy2(path, backup_path)
    return backup_path


def restore_backup(path: str, backup_path: str) -> bool:
    try:
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, path)
            return True
        return False
    except Exception:
        return False


def cleanup_backup(backup_path: str) -> None:
    try:
        if os.path.exists(backup_path):
            os.remove(backup_path)
    except Exception:
        pass


def apply_llm_fix(task: Dict[str, Any], path: str) -> Dict[str, Any]:
    path = str(path).strip()
    if not path or not os.path.exists(path):
        return {
            "ok": False,
            "reason": "target_file_missing",
            "changed_files": [],
            "backup_files": [],
        }

    try:
        with open(path, "r", encoding="utf-8") as f:
            original = f.read()
    except Exception as e:
        return {
            "ok": False,
            "reason": f"read_failed:{e}",
            "changed_files": [],
            "backup_files": [],
        }

    prompt = build_prompt(task, original, path)
    fixed = request_fix(prompt, original)

    if not isinstance(fixed, str) or not fixed.strip():
        return {
            "ok": False,
            "reason": "llm_empty_result",
            "changed_files": [],
            "backup_files": [],
        }

    if fixed == original:
        return {
            "ok": True,
            "reason": "llm_no_change",
            "changed_files": [],
            "backup_files": [],
        }

    try:
        backup_path = make_backup(path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(fixed)
    except Exception as e:
        return {
            "ok": False,
            "reason": f"write_failed:{e}",
            "changed_files": [],
            "backup_files": [],
        }

    return {
        "ok": True,
        "reason": "llm_fix_applied",
        "changed_files": [path],
        "backup_files": [backup_path],
    }


def apply_llm_fix_multi(task: Dict[str, Any], paths: List[str]) -> Dict[str, Any]:
    unique_paths: List[str] = []
    seen = set()

    for p in paths:
        sp = str(p).strip()
        if not sp or sp in seen:
            continue
        seen.add(sp)
        unique_paths.append(sp)

    if not unique_paths:
        return {
            "ok": False,
            "reason": "no_targets",
            "changed_files": [],
            "backup_files": [],
            "results": [],
        }

    changed_files: List[str] = []
    backup_files: List[str] = []
    results: List[Dict[str, Any]] = []
    any_ok = False

    for path in unique_paths[:3]:
        result = apply_llm_fix(task, path)
        results.append({"path": path, **result})

        if result.get("ok"):
            any_ok = True

        for changed in result.get("changed_files", []):
            if changed not in changed_files:
                changed_files.append(changed)

        for backup in result.get("backup_files", []):
            if backup not in backup_files:
                backup_files.append(backup)

    return {
        "ok": any_ok,
        "reason": "llm_multi_fix_applied" if any_ok else "llm_multi_fix_failed",
        "changed_files": changed_files,
        "backup_files": backup_files,
        "results": results,
    }


def rollback_changed_files(changed_files: List[str]) -> Dict[str, Any]:
    restored = []
    failed = []

    for path in changed_files:
        backup_path = f"{path}.bak"
        ok = restore_backup(path, backup_path)
        if ok:
            restored.append(path)
        else:
            failed.append(path)

    return {
        "ok": len(failed) == 0,
        "restored": restored,
        "failed": failed,
    }


def finalize_backups(changed_files: List[str]) -> None:
    for path in changed_files:
        cleanup_backup(f"{path}.bak")
