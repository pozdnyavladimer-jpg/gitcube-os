from typing import Dict, Any, Tuple, List


AGENTS = ("TANK", "MAGE", "ARCHER", "HEALER", "ASSASSIN")

PAIR_COMPATIBILITY = {
    "TANK": ["MAGE", "HEALER"],
    "MAGE": ["TANK", "HEALER"],
    "ARCHER": ["HEALER", "ASSASSIN"],
    "HEALER": ["ASSASSIN", "ARCHER", "TANK", "MAGE"],
    "ASSASSIN": ["HEALER", "ARCHER"],
}


def _f(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def _has_target_path(task: Dict[str, Any]) -> bool:
    payload = task.get("payload", {}) or {}
    path = str(payload.get("path", "")).strip()
    return bool(path)


def get_resonance_vector(task: Dict[str, Any]) -> Dict[str, float]:
    rv = task.get("resonance_vector", {}) or {}
    return {
        "pressure": _f(rv.get("pressure", 0.0)),
        "flow": _f(rv.get("flow", 0.0)),
        "structure": _f(rv.get("structure", 0.0)),
        "balance": _f(rv.get("balance", 0.0)),
        "law": _f(rv.get("law", 0.0)),
        "future": _f(rv.get("future", 0.0)),
    }


def score_for_tank(task: Dict[str, Any]) -> float:
    rv = get_resonance_vector(task)
    has_path = _has_target_path(task)

    score = 0.0
    score += 0.45 * rv["pressure"]
    score += 0.25 * (1.0 - rv["balance"])
    score += 0.20 * (1.0 - rv["structure"])
    score += 0.10 * (1.0 - rv["law"])

    if not has_path:
        score += 0.20

    return round(score, 6)


def score_for_mage(task: Dict[str, Any]) -> float:
    rv = get_resonance_vector(task)

    score = 0.0
    score += 0.30 * (1.0 - rv["structure"])
    score += 0.30 * (1.0 - rv["law"])
    score += 0.25 * rv["future"]
    score += 0.15 * rv["pressure"]

    return round(score, 6)


def score_for_archer(task: Dict[str, Any]) -> float:
    rv = get_resonance_vector(task)
    has_path = _has_target_path(task)

    if not has_path:
        return 0.0

    score = 0.0
    score += 0.35 * rv["structure"]
    score += 0.25 * rv["law"]
    score += 0.20 * rv["future"]
    score += 0.10 * rv["flow"]
    score += 0.10
    score -= 0.15 * rv["pressure"]

    return round(max(0.0, score), 6)


def score_for_healer(task: Dict[str, Any]) -> float:
    rv = get_resonance_vector(task)

    score = 0.0
    score += 0.35 * (1.0 - rv["balance"])
    score += 0.25 * (1.0 - rv["law"])
    score += 0.20 * (1.0 - rv["pressure"])
    score += 0.20 * rv["future"]

    return round(score, 6)


def score_for_assassin(task: Dict[str, Any]) -> float:
    rv = get_resonance_vector(task)
    has_path = _has_target_path(task)

    score = 0.0
    score += 0.35 * rv["pressure"]
    score += 0.20 * rv["flow"]
    score += 0.20 * (1.0 - rv["structure"])
    score += 0.15 * (1.0 - rv["law"])
    score += 0.10 * (1.0 - rv["balance"])

    if has_path:
        score += 0.10

    return round(score, 6)


def score_agents(task: Dict[str, Any]) -> Dict[str, float]:
    return {
        "TANK": score_for_tank(task),
        "MAGE": score_for_mage(task),
        "ARCHER": score_for_archer(task),
        "HEALER": score_for_healer(task),
        "ASSASSIN": score_for_assassin(task),
    }


def select_primary(scores: Dict[str, float]) -> str:
    return max(scores, key=scores.get)


def select_support(primary: str, scores: Dict[str, float]) -> str:
    compatible = PAIR_COMPATIBILITY.get(primary, [])
    if not compatible:
        return "NONE"

    best_agent = None
    best_score = -1.0

    for agent in compatible:
        s = float(scores.get(agent, 0.0))
        if s > best_score:
            best_score = s
            best_agent = agent

    return best_agent or "NONE"


def build_reason(task: Dict[str, Any], primary: str, support: str) -> str:
    rv = get_resonance_vector(task)
    has_path = _has_target_path(task)

    features: List[str] = []

    if rv["pressure"] >= 0.7:
        features.append("high_pressure")
    if rv["structure"] <= 0.35:
        features.append("low_structure")
    if rv["law"] <= 0.35:
        features.append("low_law")
    if rv["balance"] <= 0.35:
        features.append("low_balance")
    if rv["future"] >= 0.7:
        features.append("high_future")
    if has_path:
        features.append("has_path")
    else:
        features.append("no_path")

    core = ",".join(features[:4])
    return f"{primary.lower()}+{support.lower()}:{core}"


def select_pair(task: Dict[str, Any]) -> Tuple[str, str, Dict[str, float], str]:
    scores = score_agents(task)
    primary = select_primary(scores)
    support = select_support(primary, scores)
    reason = build_reason(task, primary, support)
    return primary, support, scores, reason


def select_agent(task: Dict[str, Any]) -> Tuple[str, Dict[str, float], str]:
    primary, support, scores, reason = select_pair(task)
    return primary, scores, reason
