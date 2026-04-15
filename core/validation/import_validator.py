from __future__ import annotations

from typing import Dict, Any, List
import py_compile


def validate_import_targets(paths: List[str]) -> Dict[str, Any]:
    errors: List[str] = []

    for path in paths:
        path = str(path).strip()
        if not path.endswith(".py"):
            continue
        try:
            py_compile.compile(path, doraise=True)
        except Exception as e:
            errors.append(f"{path}: {e}")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
    }
