from typing import Dict, Any


def evaluate_tank_policy(
    task: Dict[str, Any],
    primary_agent: str,
    support_agent: str,
    scores: Dict[str, float],
) -> Dict[str, Any]:
    payload = task.get("payload", {}) or {}
    problem = str(payload.get("problem", "")).strip().lower()
    has_path = bool(str(payload.get("path", "")).strip())
    paths = payload.get("paths", [])
    has_paths = isinstance(paths, list) and len(paths) > 0

    resonance = task.get("resonance_vector", {}) or {}
    pressure = float(resonance.get("pressure", 0.0))
    structure = float(resonance.get("structure", 0.0))
    law = float(resonance.get("law", 0.0))
    balance = float(resonance.get("balance", 0.0))

    # structural / builder tasks should not be force-published by TANK
    if problem in {
        "missing_init",
        "missing_init_group",
        "python_without_docs",
        "package_structure",
        "missing_root_readme",
        "missing_start_here",
    }:
        return {
            "mode": "builder_lane",
            "severity": "normal",
            "force_publish": False,
            "block_local_execution": False,
            "note": "tank_policy:structural_builder_task",
        }

    # if task has no local target and looks macro / unstable -> TANK escalation
    if (not has_path and not has_paths) and (
        pressure >= 0.70 or structure <= 0.30 or law <= 0.30 or balance <= 0.35
    ):
        return {
            "mode": "containment",
            "severity": "normal",
            "force_publish": True,
            "block_local_execution": True,
            "note": "tank_policy:no_path_macro_containment",
        }

    return {
        "mode": "pass",
        "severity": "low",
        "force_publish": False,
        "block_local_execution": False,
        "note": "tank_policy:pass",
    }
