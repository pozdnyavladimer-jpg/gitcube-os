from typing import Dict, Any, Optional


STRUCTURAL_PROBLEMS = {
    "missing_init",
    "missing_init_group",
    "python_without_docs",
    "package_structure",
    "missing_root_readme",
    "missing_start_here",
}

MACRO_PROBLEMS = {
    "routing_failure",
    "no_target_path",
    "global_block",
}


def clamp01(x: Any) -> float:
    try:
        return max(0.0, min(1.0, float(x)))
    except Exception:
        return 0.0


def get_problem(task: Dict[str, Any]) -> str:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
    return str(payload.get("problem", "")).strip().lower()


def has_target_path(task: Dict[str, Any]) -> bool:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
    path = str(payload.get("path", "")).strip()
    paths = payload.get("paths", [])
    has_paths = isinstance(paths, list) and len(paths) > 0
    return bool(path or has_paths)


def get_vector(task: Dict[str, Any]) -> Dict[str, float]:
    rv = task.get("resonance_vector", {}) if isinstance(task.get("resonance_vector"), dict) else {}
    return {
        "pressure": clamp01(rv.get("pressure", 0.0)),
        "flow": clamp01(rv.get("flow", 0.0)),
        "structure": clamp01(rv.get("structure", 0.0)),
        "balance": clamp01(rv.get("balance", 0.0)),
        "law": clamp01(rv.get("law", 0.0)),
        "future": clamp01(rv.get("future", 0.0)),
    }


def is_structural(task: Dict[str, Any]) -> bool:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
    hint = str(payload.get("executor_hint", "")).strip().upper()
    return get_problem(task) in STRUCTURAL_PROBLEMS or hint == "MAGE"


def is_macro(task: Dict[str, Any]) -> bool:
    return get_problem(task) in MACRO_PROBLEMS


def evaluate_pair_policy(
    task: Dict[str, Any],
    primary_agent: str,
    support_agent: str,
    scores: Dict[str, float],
) -> Dict[str, Any]:
    problem = get_problem(task)
    has_path = has_target_path(task)
    v = get_vector(task)

    pressure = v["pressure"]
    structure = v["structure"]
    law = v["law"]
    balance = v["balance"]

    primary_agent = str(primary_agent or "").strip().upper()
    support_agent = str(support_agent or "").strip().upper()

    # Builder / structural tasks should not be force-published by default
    if problem in STRUCTURAL_PROBLEMS:
        return {
            "mode": "builder_lane",
            "severity": "normal",
            "force_publish": False,
            "block_local_execution": False,
            "note": "tank_policy:structural_builder_task",
            "policy_owner": "TANK",
            "policy_version": "party_native_v1",
        }

    # Macro no-path unstable tasks -> containment
    if (not has_path) and (
        pressure >= 0.70
        or structure <= 0.30
        or law <= 0.30
        or balance <= 0.35
    ):
        return {
            "mode": "containment",
            "severity": "normal",
            "force_publish": True,
            "block_local_execution": True,
            "note": "tank_policy:no_path_macro_containment",
            "policy_owner": "TANK",
            "policy_version": "party_native_v1",
        }

    # Destructive pair with high pressure
    if primary_agent == "ASSASSIN" and pressure >= 0.70:
        return {
            "mode": "destructive_guard",
            "severity": "high",
            "force_publish": True,
            "block_local_execution": True,
            "note": "tank_policy:assassin_high_pressure",
            "policy_owner": "TANK",
            "policy_version": "party_native_v1",
        }

    return {
        "mode": "pass",
        "severity": "low",
        "force_publish": False,
        "block_local_execution": False,
        "note": "tank_policy:pass",
        "policy_owner": "TANK",
        "policy_version": "party_native_v1",
    }


def evaluate_party_policy(
    task: Dict[str, Any],
    leader: str,
    builder: str,
    stabilizer: str,
    guard: str,
    cleanup: Optional[str],
    scores: Dict[str, float],
) -> Dict[str, Any]:
    problem = get_problem(task)
    has_path = has_target_path(task)
    v = get_vector(task)

    pressure = v["pressure"]
    flow = v["flow"]
    structure = v["structure"]
    balance = v["balance"]
    law = v["law"]
    future = v["future"]

    leader = str(leader or "").strip().upper()
    builder = str(builder or "").strip().upper()
    stabilizer = str(stabilizer or "").strip().upper()
    guard = str(guard or "").strip().upper()
    cleanup = str(cleanup or "").strip().upper() if cleanup else None

    party_risk = 0.0
    if not has_path:
        party_risk += 0.35
    if pressure >= 0.70:
        party_risk += 0.20
    if structure <= 0.30:
        party_risk += 0.20
    if law <= 0.35:
        party_risk += 0.15
    if balance <= 0.35:
        party_risk += 0.10

    # Structural party = allowed to work locally first
    if problem in STRUCTURAL_PROBLEMS or (
        leader == "MAGE" and builder == "ARCHER"
    ):
        return {
            "mode": "party_builder_lane",
            "severity": "normal",
            "force_publish": False,
            "block_local_execution": False,
            "party_risk": round(party_risk, 6),
            "note": "tank_policy:party_structural_builder_lane",
            "policy_owner": "TANK",
            "policy_version": "party_native_v1",
        }

    # Macro party without path and high instability -> contain
    if is_macro(task) and (not has_path) and (
        pressure >= 0.70 or structure <= 0.30 or law <= 0.35
    ):
        return {
            "mode": "party_containment",
            "severity": "high",
            "force_publish": True,
            "block_local_execution": True,
            "party_risk": round(party_risk, 6),
            "note": "tank_policy:party_macro_containment",
            "policy_owner": "TANK",
            "policy_version": "party_native_v1",
        }

    # Cleanup slot + pressure = force safe escalation
    if cleanup == "ASSASSIN" and pressure >= 0.75:
        return {
            "mode": "party_cleanup_guard",
            "severity": "high",
            "force_publish": True,
            "block_local_execution": True,
            "party_risk": round(party_risk, 6),
            "note": "tank_policy:party_cleanup_high_pressure",
            "policy_owner": "TANK",
            "policy_version": "party_native_v1",
        }

    # Future-heavy but still structurally incomplete -> let party try first
    if future >= 0.70 and structure <= 0.35:
        return {
            "mode": "party_growth_lane",
            "severity": "normal",
            "force_publish": False,
            "block_local_execution": False,
            "party_risk": round(party_risk, 6),
            "note": "tank_policy:party_growth_lane",
            "policy_owner": "TANK",
            "policy_version": "party_native_v1",
        }

    return {
        "mode": "party_pass",
        "severity": "low",
        "force_publish": False,
        "block_local_execution": False,
        "party_risk": round(party_risk, 6),
        "note": "tank_policy:party_pass",
        "policy_owner": "TANK",
        "policy_version": "party_native_v1",
    }


def evaluate_tank_policy(
    task: Dict[str, Any],
    primary_agent: Optional[str] = None,
    support_agent: Optional[str] = None,
    scores: Optional[Dict[str, float]] = None,
    *,
    leader: Optional[str] = None,
    builder: Optional[str] = None,
    stabilizer: Optional[str] = None,
    guard: Optional[str] = None,
    cleanup: Optional[str] = None,
    mode: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Backward compatible:
      evaluate_tank_policy(task, primary_agent, support_agent, scores)

    Native party-aware:
      evaluate_tank_policy(
          task,
          leader="MAGE",
          builder="ARCHER",
          stabilizer="HEALER",
          guard="TANK",
          cleanup=None,
          scores=scores,
          mode="party",
      )
    """
    if scores is None or not isinstance(scores, dict):
        scores = {}

    requested_mode = str(mode or "").strip().lower()

    if requested_mode == "party" or any([leader, builder, stabilizer, guard, cleanup]):
        return evaluate_party_policy(
            task=task,
            leader=leader or primary_agent or "MAGE",
            builder=builder or primary_agent or "ARCHER",
            stabilizer=stabilizer or support_agent or "HEALER",
            guard=guard or "TANK",
            cleanup=cleanup,
            scores=scores,
        )

    return evaluate_pair_policy(
        task=task,
        primary_agent=primary_agent or "ARCHER",
        support_agent=support_agent or "HEALER",
        scores=scores,
    )
