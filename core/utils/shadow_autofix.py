from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Any


IGNORED_STDLIB_SHADOWS = {
    "__future__",
}


def find_shadowed_stdlib(repo_root: str = ".") -> List[Path]:
    root = Path(repo_root)

    stdlib_names = set(getattr(sys, "stdlib_module_names", set()))
    builtin_names = set(getattr(sys, "builtin_module_names", tuple()))
    blocked = (stdlib_names | builtin_names) - IGNORED_STDLIB_SHADOWS

    conflicts: List[Path] = []

    for path in root.rglob("*.py"):
        if "__pycache__" in path.parts or ".git" in path.parts or ".venv" in path.parts:
            continue

        if path.name == "__init__.py":
            continue

        if path.stem in blocked:
            conflicts.append(path)

    return sorted(conflicts)


def suggest_rename(path: Path) -> Path:
    return path.with_name(f"repo_{path.stem}.py")


def autofix_shadowed_stdlib(repo_root: str = ".", apply: bool = False) -> Dict[str, Any]:
    conflicts = find_shadowed_stdlib(repo_root)
    actions: List[Dict[str, str]] = []
    skipped: List[Dict[str, str]] = []

    for old_path in conflicts:
        new_path = suggest_rename(old_path)

        if new_path.exists():
            skipped.append({
                "path": str(old_path),
                "reason": f"target_exists:{new_path}",
            })
            continue

        actions.append({
            "from": str(old_path),
            "to": str(new_path),
        })

        if apply:
            old_path.rename(new_path)

    return {
        "ok": len(skipped) == 0,
        "apply": apply,
        "conflict_count": len(conflicts),
        "rename_count": len(actions),
        "skipped_count": len(skipped),
        "actions": actions,
        "skipped": skipped,
    }


if __name__ == "__main__":
    from pprint import pprint
    pprint(autofix_shadowed_stdlib(".", apply=False))
