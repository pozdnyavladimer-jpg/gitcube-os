import os
import subprocess


def run(cmd: str):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def normalize_path(path: str) -> str:
    return str(path or "").replace("\\", "/").strip()


def has_target_path(task) -> bool:
    payload = task.get("payload", {}) or {}
    path = normalize_path(payload.get("path"))
    return bool(path)


def validate_python_file(path: str):
    out, err, code = run(f'python -m py_compile "{path}"')
    if code != 0:
        return False, f"validation_failed:{err or out}"
    return True, "validation_ok"


def run_healer_support(task):
    payload = task.get("payload", {}) or {}
    path = normalize_path(payload.get("path"))

    if not path:
        return False, "no_target_path"

    if not os.path.exists(path):
        return False, "path_not_found"

    if not path.endswith(".py"):
        return False, "not_python"

    valid, reason = validate_python_file(path)
    if not valid:
        return False, reason

    return True, "healer_validation_ok"
