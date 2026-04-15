from __future__ import annotations

import os
from typing import Dict, Any, List


def safe_write_file(path: str, content: str) -> bool:
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception:
        return False


def create_missing_init_files(targets: List[str]) -> Dict[str, Any]:
    changed_files: List[str] = []

    for target in targets:
        target = str(target).strip()
        if not target:
            continue

        if not os.path.exists(target):
            ok = safe_write_file(target, '"""Auto-created package marker."""\n')
            if ok:
                changed_files.append(target)

    return {
        "ok": True,
        "changed_files": changed_files,
        "reason": "package_markers_created_or_already_present",
    }


def execute_structural_fix(task: Dict[str, Any], mesh_result: Dict[str, Any]) -> Dict[str, Any]:
    problem = str(task.get("problem", "")).strip().lower()

    if problem == "missing_init_group":
        targets = list(mesh_result.get("recommended_targets", []))
        return create_missing_init_files(targets)

    return {
        "ok": False,
        "changed_files": [],
        "reason": f"unsupported_problem:{problem}",
    }
