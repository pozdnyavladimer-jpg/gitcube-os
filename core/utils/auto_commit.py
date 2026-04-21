from __future__ import annotations

import subprocess
from typing import Dict, Any, List

from core.utils.auto_branch import ensure_branch


def auto_commit_changes(
    changed_files: List[str],
    message: str,
    branch_name: str | None = None,
) -> Dict[str, Any]:
    files = [str(x).strip() for x in changed_files if str(x).strip()]
    if not files:
        return {"ok": False, "reason": "no_files"}

    branch_result: Dict[str, Any] = {"ok": True, "reason": "branch_not_requested"}
    if branch_name:
        branch_result = ensure_branch(branch_name)
        if not branch_result.get("ok", False):
            return {
                "ok": False,
                "reason": "branch_prepare_failed",
                "branch_result": branch_result,
            }

    try:
        add_cmd = ["git", "add", *files]
        add_run = subprocess.run(add_cmd, capture_output=True, text=True)

        if add_run.returncode != 0:
            return {
                "ok": False,
                "reason": "git_add_failed",
                "stderr": add_run.stderr,
                "stdout": add_run.stdout,
                "branch_result": branch_result,
            }

        commit_cmd = ["git", "commit", "-m", message]
        commit_run = subprocess.run(commit_cmd, capture_output=True, text=True)

        if commit_run.returncode != 0:
            stderr = (commit_run.stderr or "").strip()
            stdout = (commit_run.stdout or "").strip()

            if "nothing to commit" in stdout.lower() or "nothing to commit" in stderr.lower():
                return {
                    "ok": True,
                    "reason": "nothing_to_commit",
                    "stdout": stdout,
                    "stderr": stderr,
                    "branch_result": branch_result,
                }

            return {
                "ok": False,
                "reason": "git_commit_failed",
                "stderr": stderr,
                "stdout": stdout,
                "branch_result": branch_result,
            }

        return {
            "ok": True,
            "reason": "commit_created",
            "stdout": commit_run.stdout,
            "stderr": commit_run.stderr,
            "message": message,
            "files": files,
            "branch_result": branch_result,
        }

    except Exception as e:
        return {
            "ok": False,
            "reason": "exception",
            "error": str(e),
            "branch_result": branch_result,
        }
