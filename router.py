from typing import Dict, Any, Tuple

AGENTS = ("TANK", "MAGE", "ARCHER", "HEALER", "ASSASSIN")

PAIR_COMPATIBILITY = {
    ("TANK", "HEALER"): 0.12,
    ("HEALER", "TANK"): 0.12,
    ("MAGE", "TANK"): 0.10,
    ("TANK", "MAGE"): 0.10,
    ("MAGE", "ARCHER"): 0.08,
    ("ARCHER", "MAGE"): 0.08,
    ("ASSASSIN", "HEALER"): 0.10,
    ("HEALER", "ASSASSIN"): 0.10,
    ("ARCHER", "HEALER"): 0.06,
    ("HEALER", "ARCHER"): 0.06,
    ("ASSASSIN", "TANK"): 0.04,
    ("TANK", "ASSASSIN"): 0.04,
}


def clamp01(x: Any) -> float:
    try:
        return max(0.0, min(1.0, float(x)))
    except Exception:
        return 0.0


def task_vector(task: Dict[str, Any]) -> Dict[str, float]:
    rv = task.get("resonance_vector", {}) or {}
    return {
        "pressure": clamp01(rv.get("pressure", 0.5)),
        "flow": clamp01(rv.get("flow", 0.5)),
        "structure": clamp01(rv.get("structure", 0.5)),
        "balance": clamp01(rv.get("balance", 0.5)),
        "law": clamp01(rv.get("law", 0.5)),
        "future": clamp01(rv.get("future", 0.5)),
    }


def payload_info(task: Dict[str, Any]) -> Dict[str, Any]:
    payload = task.get("payload", {}) or {}
    path = str(payload.get("path", "") or "").strip()
    paths = payload.get("paths", [])
    if not isinstance(paths, list):
        paths = []

    count_paths = len([p for p in paths if str(p).strip()])
    has_path = bool(path or count_paths > 0)
    multi_path = count_paths > 1

    problem = str(payload.get("problem", "") or "").strip().lower()
    priority = str(payload.get("priority", "") or "").strip().lower()
    executor_hint = str(payload.get("executor_hint", "") or "").strip().upper()

    return {
        "path": path,
        "paths": paths,
        "has_path": has_path,
        "multi_path": multi_path,
        "count_paths": count_paths,
        "problem": problem,
        "priority": priority,
        "executor_hint": executor_hint,
    }


def hint_bonus(agent: str, info: Dict[str, Any]) -> float:
    hint = info.get("executor_hint", "")
    if not hint:
        return 0.0
    if hint == agent:
        return 0.18
    return 0.0


def score_tank(vec: Dict[str, float], info: Dict[str, Any]) -> Tuple[float, str]:
    pressure = vec["pressure"]
    structure = vec["structure"]
    balance = vec["balance"]
    law = vec["law"]

    score = 0.0
    reasons = []

    score += 0.40 * pressure
    if pressure >= 0.65:
        reasons.append("high_pressure")

    score += 0.22 * (1.0 - structure)
    if structure <= 0.40:
        reasons.append("low_structure")

    score += 0.18 * (1.0 - balance)
    if balance <= 0.45:
        reasons.append("low_balance")

    score += 0.12 * (1.0 - law)
    if law <= 0.40:
        reasons.append("low_law")

    if not info["has_path"]:
        score += 0.15
        reasons.append("no_path")

    score += hint_bonus("TANK", info)
    if hint_bonus("TANK", info) > 0:
        reasons.append("hint_tank")

    return round(score, 6), ",".join(reasons) or "tank_baseline"


def score_mage(vec: Dict[str, float], info: Dict[str, Any]) -> Tuple[float, str]:
    structure = vec["structure"]
    law = vec["law"]
    future = vec["future"]
    flow = vec["flow"]

    score = 0.0
    reasons = []

    score += 0.34 * (1.0 - structure)
    if structure <= 0.45:
        reasons.append("low_structure")

    score += 0.28 * (1.0 - law)
    if law <= 0.45:
        reasons.append("low_law")

    score += 0.16 * future
    if future >= 0.60:
        reasons.append("future_pull")

    score += 0.08 * flow
    if flow >= 0.55:
        reasons.append("enough_flow")

    if info["problem"] in {"missing_init", "missing_init_group", "python_without_docs"}:
        score += 0.18
        reasons.append("structural_problem")

    if info["multi_path"]:
        score += 0.12
        reasons.append("multi_path")

    if info["has_path"]:
        score += 0.05

    score += hint_bonus("MAGE", info)
    if hint_bonus("MAGE", info) > 0:
        reasons.append("hint_mage")

    return round(score, 6), ",".join(reasons) or "mage_baseline"


def score_archer(vec: Dict[str, float], info: Dict[str, Any]) -> Tuple[float, str]:
    structure = vec["structure"]
    flow = vec["flow"]
    law = vec["law"]
    pressure = vec["pressure"]

    score = 0.0
    reasons = []

    if not info["has_path"]:
        return 0.0, "no_path"

    score += 0.24 * structure
    if structure >= 0.55:
        reasons.append("enough_structure")

    score += 0.22 * flow
    if flow >= 0.55:
        reasons.append("high_flow")

    score += 0.18 * law
    if law >= 0.50:
        reasons.append("enough_law")

    score += 0.14
    reasons.append("has_path")

    if not info["multi_path"]:
        score += 0.08
        reasons.append("single_target")

    score -= 0.08 * pressure
    if pressure >= 0.70:
        reasons.append("pressure_penalty")

    if info["problem"] == "debug_prints_group":
        score += 0.12
        reasons.append("debug_prints_fit")

    score += hint_bonus("ARCHER", info)
    if hint_bonus("ARCHER", info) > 0:
        reasons.append("hint_archer")

    return round(max(0.0, score), 6), ",".join(reasons) or "archer_baseline"


def score_healer(vec: Dict[str, float], info: Dict[str, Any]) -> Tuple[float, str]:
    pressure = vec["pressure"]
    balance = vec["balance"]
    law = vec["law"]
    structure = vec["structure"]

    score = 0.0
    reasons = []

    score += 0.22 * pressure
    if pressure >= 0.55:
        reasons.append("pressure")

    score += 0.26 * (1.0 - balance)
    if balance <= 0.45:
        reasons.append("low_balance")

    score += 0.24 * (1.0 - law)
    if law <= 0.45:
        reasons.append("low_law")

    score += 0.10 * (1.0 - structure)
    if structure <= 0.45:
        reasons.append("low_structure")

    if not info["has_path"]:
        score += 0.10
        reasons.append("no_path")

    if info["problem"] in {"bare_except_group", "python_without_docs"}:
        score += 0.08
        reasons.append("repair_fit")

    score += hint_bonus("HEALER", info)
    if hint_bonus("HEALER", info) > 0:
        reasons.append("hint_healer")

    return round(score, 6), ",".join(reasons) or "healer_baseline"


def score_assassin(vec: Dict[str, float], info: Dict[str, Any]) -> Tuple[float, str]:
    pressure = vec["pressure"]
    flow = vec["flow"]
    structure = vec["structure"]

    score = 0.0
    reasons = []

    if not info["has_path"]:
        score -= 0.10
        reasons.append("no_path_penalty")
    else:
        score += 0.08
        reasons.append("has_path")

    score += 0.22 * pressure
    if pressure >= 0.55:
        reasons.append("pressure")

    score += 0.24 * flow
    if flow >= 0.55:
        reasons.append("high_flow")

    score += 0.12 * structure
    if structure >= 0.50:
        reasons.append("enough_structure")

    if info["problem"] in {"todo_group", "debug_prints_group", "pass_blocks_group"}:
        score += 0.14
        reasons.append("cleanup_fit")

    score += hint_bonus("ASSASSIN", info)
    if hint_bonus("ASSASSIN", info) > 0:
        reasons.append("hint_assassin")

    return round(max(0.0, score), 6), ",".join(reasons) or "assassin_baseline"


def score_agents(task: Dict[str, Any]) -> Dict[str, float]:
    vec = task_vector(task)
    info = payload_info(task)

    tank, _ = score_tank(vec, info)
    mage, _ = score_mage(vec, info)
    archer, _ = score_archer(vec, info)
    healer, _ = score_healer(vec, info)
    assassin, _ = score_assassin(vec, info)

    return {
        "TANK": round(tank, 6),
        "MAGE": round(mage, 6),
        "ARCHER": round(archer, 6),
        "HEALER": round(healer, 6),
        "ASSASSIN": round(assassin, 6),
    }


def pair_bonus(primary: str, support: str) -> float:
    base = PAIR_COMPATIBILITY.get((primary, support), 0.0)

    if primary == support:
        return -0.08

    if primary == "HEALER" and support == "TANK":
        return base

    if primary == "MAGE" and support in {"TANK", "ARCHER"}:
        return base

    if primary == "ASSASSIN" and support == "HEALER":
        return base

    if primary == "ARCHER" and support in {"HEALER", "MAGE"}:
        return base

    return base


def select_support(primary: str, scores: Dict[str, float]) -> Tuple[str, float]:
    best_agent = "NONE"
    best_total = -999.0

    for agent in AGENTS:
        if agent == primary:
            continue

        total = float(scores.get(agent, 0.0)) + pair_bonus(primary, agent)

        if total > best_total:
            best_total = total
            best_agent = agent

    return best_agent, round(best_total, 6)


def build_reason(task: Dict[str, Any], primary: str, support: str, bonus: float) -> str:
    vec = task_vector(task)
    info = payload_info(task)

    features = []

    if vec["pressure"] >= 0.65:
        features.append("high_pressure")
    if vec["structure"] <= 0.45:
        features.append("low_structure")
    if vec["law"] <= 0.45:
        features.append("low_law")
    if vec["balance"] <= 0.45:
        features.append("low_balance")
    if vec["future"] >= 0.60:
        features.append("future_pull")
    if not info["has_path"]:
        features.append("no_path")
    if info["multi_path"]:
        features.append("multi_path")
    if info["executor_hint"]:
        features.append(f"hint_{info['executor_hint'].lower()}")
    if bonus < 0:
        features.append("pair_penalty")
    elif bonus > 0:
        features.append("pair_bonus")

    core = ",".join(features[:6]) if features else "baseline"
    return f"{primary.lower()}+{support.lower()}:{core}"


def select_pair(task: Dict[str, Any]) -> Tuple[str, str, Dict[str, float], str]:
    scores = score_agents(task)

    primary = max(scores, key=scores.get)
    support, support_total = select_support(primary, scores)
    bonus = pair_bonus(primary, support)
    reason = build_reason(task, primary, support, bonus)

    scores_with_pair = dict(scores)
    scores_with_pair["_pair_bonus"] = round(bonus, 6)
    scores_with_pair["_support_total"] = round(support_total, 6)

    return primary, support, scores_with_pair, reason


def select_agent(task: Dict[str, Any]) -> Tuple[str, Dict[str, float], str]:
    primary, support, scores, reason = select_pair(task)
    return primary, scores, reason
