from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Any


IGNORED_STDLIB_SHADOWS = {
    "__future__",
}


def find_shadowed_stdlib(repo_root: str = ".") -> List[str]:
    root = Path(repo_root)

    stdlib_names = set(getattr(sys, "stdlib_module_names", set()))
    builtin_names = set(getattr(sys, "builtin_module_names", tuple()))
    blocked = (stdlib_names | builtin_names) - IGNORED_STDLIB_SHADOWS

    conflicts: List[str] = []

    for path in root.rglob("*.py"):
        if "__pycache__" in path.parts or ".git" in path.parts or ".venv" in path.parts:
            continue

        if path.name == "__init__.py":
            continue

        module_name = path.stem
        if module_name in blocked:
            conflicts.append(str(path))

    return sorted(conflicts)


def build_shadow_report(repo_root: str = ".") -> Dict[str, Any]:
    conflicts = find_shadowed_stdlib(repo_root)
    return {
        "ok": len(conflicts) == 0,
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
    }


if __name__ == "__main__":
    from pprint import pprint
    pprint(build_shadow_report("."))
