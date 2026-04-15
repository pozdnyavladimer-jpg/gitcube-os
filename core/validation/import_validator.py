from __future__ import annotations

import py_compile
from typing import List, Dict, Any


def validate_import_targets(paths: List[str]) -> Dict[str, Any]:
    errors = []

    for path in paths:
        try:
            py_compile.compile(path, doraise=True)
        except Exception as e:
            errors.append(f"{path}: {e}")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
    }
