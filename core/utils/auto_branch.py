from __future__ import annotations

import re
import subprocess
from typing import Dict, Any


def _safe_branch_name(value: str) -> str:
    value = str(value or "").strip().lower()
    value = re.sub(r"[^a-z0-9._/-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "auto/repair"


def ensure_branch(branch_name: str) -> Dict[str, Any]:
    branch_name = _safe_branch_name(branch_name)

    try:
        current = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
        )
        current_name = (current.stdout or "").strip()

        if current.returncode == 0 and current_name == branch_name:
            return {"ok": True, "reason": "already_on_branch", "branch": branch_name}

        check = subprocess.run(
            ["git", "rev-parse", "--verify", branch_name],
            capture_output=True,
            text=True,
        )

        if check.returncode == 0:
            run = subprocess.run(
                ["git", "checkout", branch_name],
                capture_output=True,
                text=True,
            )
            if run.returncode != 0:
                return {
                    "ok": False,
                    "reason": "checkout_failed",
                    "branch": branch_name,
                    "stdout": run.stdout,
                    "stderr": run.stderr,
                }
            return {"ok": True, "reason": "checked_out_existing", "branch": branch_name}

        create = subprocess.run(
            ["git", "checkout", "-b", branch_name],
            capture_output=True,
            text=True,
        )
        if create.returncode != 0:
            return {
                "ok": False,
                "reason": "create_branch_failed",
                "branch": branch_name,
                "stdout": create.stdout,
                "stderr": create.stderr,
            }

        return {"ok": True, "reason": "branch_created", "branch": branch_name}

    except Exception as e:
        return {"ok": False, "reason": "exception", "error": str(e), "branch": branch_name}
