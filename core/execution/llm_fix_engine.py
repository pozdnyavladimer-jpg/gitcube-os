from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional


REPO_ROOT = Path(".")


def build_prompt(task: Dict[str, Any], original_content: str, path: str) -> str:
    problem = str(task.get("problem", "")).strip()
    return f"""Task type: {problem}
Target file: {path}

Allowed actions:
- fix obviously broken imports
- preserve unrelated code
- prefer valid in-repo module paths
- keep relative imports intact

Forbidden actions:
- delete unrelated logic
- rename public APIs
- rewrite the whole file without need

Return only corrected file content.
"""


def module_to_py_path(module: str) -> Path:
    return REPO_ROOT / Path(module.replace(".", "/")).with_suffix(".py")


def module_to_package_init(module: str) -> Path:
    return REPO_ROOT / Path(module.replace(".", "/")) / "__init__.py"


def find_repo_module(module: str) -> Optional[str]:
    module = str(module).strip()
    if not module:
        return None

    py_candidate = module_to_py_path(module)
    if py_candidate.exists():
        return module

    init_candidate = module_to_package_init(module)
    if init_candidate.exists():
        return module

    tail = module.split(".")[-1]
    matches = []

    for path in REPO_ROOT.rglob("*.py"):
        if ".venv" in path.parts or "__pycache__" in path.parts:
            continue

        if path.name == f"{tail}.py":
            rel = path.relative_to(REPO_ROOT).with_suffix("")
            matches.append(".".join(rel.parts))

        elif path.name == "__init__.py" and path.parent.name == tail:
            rel = path.parent.relative_to(REPO_ROOT)
            matches.append(".".join(rel.parts))

    if len(matches) == 1:
        return matches[0]

    return None


def try_fix_from_import(line: str) -> str:
    stripped = line.strip()

    if not (stripped.startswith("from ") and " import " in stripped):
        return line

    parts = stripped.split()
    if len(parts) < 4:
        return line

    module = parts[1]

    if module.startswith("."):
        return line

    if module in {"os", "sys", "json", "math", "typing", "pathlib", "subprocess", "datetime"}:
        return line

    if (module.startswith(("app.", "core.", "runtime_experimental.", "bridges."))
            and (module_to_py_path(module).exists() or module_to_package_init(module).exists())):
        return line

    repaired = find_repo_module(module)
    if repaired and repaired != module:
        return line.replace(f"from {module} import", f"from {repaired} import", 1)

    if repaired == module:
        return line

    return f"# FIXME broken import: {line}"


def try_fix_plain_import(line: str) -> str:
    stripped = line.strip()

    if not stripped.startswith("import "):
        return line

    if "," in stripped:
        return line

    module = stripped.replace("import ", "", 1).strip()

    if not module or module.startswith("."):
        return line

    if module in {"os", "sys", "json", "math", "typing", "pathlib", "subprocess", "datetime"}:
        return line

    if (module.startswith(("app.", "core.", "runtime_experimental.", "bridges."))
            and (module_to_py_path(module).exists() or module_to_package_init(module).exists())):
        return line

    repaired = find_repo_module(module)
    if repaired and repaired != module:
        return line.replace(f"import {module}", f"import {repaired}", 1)

    if repaired == module:
        return line

    return f"# FIXME broken import: {line}"


def request_fix(prompt: str, original_content: str) -> str:
    lines = original_content.splitlines()
    fixed = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("from ") and " import " in stripped:
            fixed.append(try_fix_from_import(line))
            continue

        if stripped.startswith("import "):
            fixed.append(try_fix_plain_import(line))
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
