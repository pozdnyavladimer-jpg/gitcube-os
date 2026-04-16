from __future__ import annotations

from typing import Dict, Any


def _f(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def _has_shadow_backup(task: Dict[str, Any], leader_result: Dict[str, Any] | None = None, mage_result: Dict[str, Any] | None = None) -> bool:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}

    if payload.get("has_shadow_backup") is True:
        return True

    for node in (leader_result or {}, mage_result or {}):
        if not isinstance(node, dict):
            continue
        if node.get("backup_files"):
            return True

        result = node.get("result")
        if isinstance(result, dict) and result.get("backup_files"):
            return True

        execution = node.get("execution")
        if isinstance(execution, dict) and execution.get("backup_files"):
            return True

    return False


def evaluate_tank_policy(
    task: Dict[str, Any],
    leader_result: Dict[str, Any] | None = None,
    mage_result: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    priority = str(task.get("priority", "normal")).strip().lower()
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}

    mesh = {}
    for node in (leader_result or {}, mage_result or {}):
        if not isinstance(node, dict):
            continue

        if isinstance(node.get("mesh"), dict):
            mesh = node["mesh"]

        result = node.get("result")
        if isinstance(result, dict) and isinstance(result.get("mesh"), dict):
            mesh = result["mesh"]

        execution = node.get("execution")
        if isinstance(execution, dict) and isinstance(execution.get("mesh"), dict):
            mesh = execution["mesh"]

    stabilization_score = _f(mesh.get("stabilization_score", 0.0), 0.0)
    avg_tension = _f(mesh.get("avg_tension", 0.0), 0.0)
    force_publish = bool(payload.get("force_publish", False))
    has_shadow_backup = _has_shadow_backup(task, leader_result, mage_result)

    base_threshold = 0.85

    # критичний режим: майже відкритий шлюз
    if priority == "critical":
        required_score = 0.10
    else:
        required_score = base_threshold

        # якщо є backup — страх падає
        if has_shadow_backup:
            required_score *= 0.5   # 0.425

        # якщо напруга низька, ще трохи опускаємо поріг
        if avg_tension <= 0.20:
            required_score -= 0.05

        # не даємо порогу піти нижче розумного мінімуму
        required_score = max(0.35, round(required_score, 3))

    allow_mage = stabilization_score >= required_score

    # додатковий "шанс Мага":
    # якщо є тінь + score вже не катастрофічний, пропускаємо
    if (not allow_mage) and has_shadow_backup and priority in {"high", "critical"} and stabilization_score >= 0.40:
        allow_mage = True

    return {
        "mode": "adaptive_shadow_policy",
        "severity": "critical" if priority == "critical" else "normal",
        "force_publish": force_publish,
        "block_local_execution": not allow_mage,
        "allow_mage": allow_mage,
        "has_shadow_backup": has_shadow_backup,
        "stabilization_score": round(stabilization_score, 3),
        "avg_tension": round(avg_tension, 3),
        "required_score": round(required_score, 3),
        "note": "mage_cleared" if allow_mage else "blocked_low_stabilization_score",
        "policy_owner": "TANK",
        "policy_version": "adaptive_shadow_v2",
    }
