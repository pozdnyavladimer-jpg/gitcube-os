from __future__ import annotations

import py_compile
from typing import Dict, Any, List


def validate_changed_files(paths: List[str]) -> Dict[str, Any]:
    errors: List[str] = []

    for path in paths:
        if not str(path).endswith(".py"):
            continue
        try:
            py_compile.compile(path, doraise=True)
        except Exception as e:
            errors.append(f"{path}: {e}")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
    }
