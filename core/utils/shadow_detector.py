from __future__ import annotations

import importlib
from pathlib import Path
from typing import Dict, Any, List


CRITICAL = {"re", "difflib", "json", "os", "sys", "typing", "pathlib", "shutil"}


def find_shadow_conflicts(repo_root: str = ".") -> List[str]:
    root = Path(repo_root)
    found: List[str] = []

    for path in root.rglob("*.py"):
        if any(part in {".git", ".venv", "__pycache__"} for part in path.parts):
            continue
        if path.stem in CRITICAL:
            found.append(str(path))

    return sorted(found)


def build_shadow_event(repo_root: str = ".") -> Dict[str, Any]:
    conflicts = find_shadow_conflicts(repo_root)
    return {
        "ok": len(conflicts) == 0,
        "problem": "shadow_stdlib_group",
        "paths": conflicts,
        "count": len(conflicts),
    }


if __name__ == "__main__":
    print(build_shadow_event("."))
