from typing import Dict, Any, Tuple

AGENTS = ("TANK", "MAGE", "ARCHER", "HEALER", "ASSASSIN")

STRUCTURAL_PROBLEMS = {
    "missing_init",
    "missing_init_group",
    "python_without_docs",
    "package_structure",
    "missing_root_readme",
    "missing_start_here",
}

SAFE_MAGE_HINTS = {
    "MAGE",
    "STRUCTURE",
    "STRUCTURAL",
}


def clamp01(x: Any) -> float:
    try:
        x = float(x)
    except Exception:
        return 0.0
    return max(0.0, min(1.0, x))


def get_payload(task: Dict[str, Any]) -> Dict[str, Any]:
    payload = task.get("payload", {})
    return payload if isinstance(payload, dict) else {}


def get_vector(task: Dict[str, Any]) -> Dict[str, float]:
    rv = task.get("resonance_vector", {})
    if not isinstance(rv, dict):
        rv = {}

    return {
        "pressure": clamp01(rv.get("pressure", 0.0)),
        "flow": clamp01(rv.get("flow", 0.0)),
        "structure": clamp01(rv.get("structure", 0.0)),
        "balance": clamp01(rv.get("balance", 0.0)),
        "law": clamp01(rv.get("law", 0.0)),
        "future": clamp01(rv.get("future", 0.0)),
    }


def get_problem(task: Dict[str, Any]) -> str:
    payload = get_payload(task)
    return str(payload.get("problem", "")).strip().lower()


def get_executor_hint(task: Dict[str, Any]) -> str:
    payload = get_payload(task)
    return str(payload.get("executor_hint", "")).strip().upper()


def get_target_path(task: Dict[str, Any]) -> str:
    payload = get_payload(task)
    return str(payload.get("path", "")).strip()


def get_target_paths(task: Dict[str, Any]):
    payload = get_payload(task)
    paths = payload.get("paths", [])
    return paths if isinstance(paths, list) else []


def has_any_target(task: Dict[str, Any]) -> bool:
    if get_target_path(task):
        return True
    return len(get_target_paths(task)) > 0


def is_structural_task(task: Dict[str, Any]) -> bool:
    problem = get_problem(task)
    hint = get_executor_hint(task)

    if problem in STRUCTURAL_PROBLEMS:
        return True

    if hint in SAFE_MAGE_HINTS:
        return True

    return False


def is_macro_task(task: Dict[str, Any]) -> bool:
    return not has_any_target(task)


def score_tank(task: Dict[str, Any]) -> float:
    v = get_vector(task)
    score = 0.0

    score += 0.50 * v["pressure"]
    score += 0.20 * (1.0 - v["balance"])
    score += 0.20 * (1.0 - v["law"])
    score += 0.10 * (1.0 - v["structure"])

    if is_macro_task(task):
        score += 0.18

    if is_structural_task(task):
        score -= 0.12

    return round(score, 6)


def score_mage(task: Dict[str, Any]) -> float:
    v = get_vector(task)
    score = 0.0

    score += 0.34 * (1.0 - v["structure"])
    score += 0.24 * (1.0 - v["law"])
    score += 0.18 * v["future"]
    score += 0.10 * (1.0 - v["balance"])
    score += 0.08 * v["pressure"]
    score += 0.06 * (1.0 - v["flow"])

    if is_structural_task(task):
        score += 1.50

    if is_macro_task(task) and is_structural_task(task):
        score += 0.20

    return round(score, 6)


def score_archer(task: Dict[str, Any]) -> float:
    v = get_vector(task)
    score = 0.0

    score += 0.28 * v["flow"]
    score += 0.22 * v["structure"]
    score += 0.16 * v["law"]
    score += 0.14 * v["balance"]
    score += 0.10 * (1.0 - v["pressure"])
    score += 0.10 * (1.0 - v["future"])

    if has_any_target(task):
        score += 0.18
    else:
        score = 0.0

    if is_structural_task(task):
        score = 0.0

    return round(score, 6)


def score_healer(task: Dict[str, Any]) -> float:
    v = get_vector(task)
    score = 0.0

    score += 0.28 * (1.0 - v["balance"])
    score += 0.22 * (1.0 - v["law"])
    score += 0.16 * (1.0 - v["structure"])
    score += 0.14 * v["pressure"]
    score += 0.12 * (1.0 - v["flow"])
    score += 0.08 * v["future"]

    if is_macro_task(task):
        score += 0.10

    return round(score, 6)


def score_assassin(task: Dict[str, Any]) -> float:
    v = get_vector(task)
    score = 0.0

    score += 0.30 * v["flow"]
    score += 0.22 * v["pressure"]
    score += 0.16 * (1.0 - v["law"])
    score += 0.12 * (1.0 - v["structure"])
    score += 0.10 * (1.0 - v["balance"])
    score += 0.10 * (1.0 - v["future"])

    if has_any_target(task):
        score += 0.10
    else:
        score -= 0.08

    if is_structural_task(task):
        score *= 0.20

    return round(score, 6)


def score_agents(task: Dict[str, Any]) -> Dict[str, float]:
    return {
        "TANK": score_tank(task),
        "MAGE": score_mage(task),
        "ARCHER": score_archer(task),
        "HEALER": score_healer(task),
        "ASSASSIN": score_assassin(task),
    }


def select_primary(scores: Dict[str, float]) -> str:
    return max(scores, key=scores.get)


def support_bonus(primary: str, support: str) -> float:
    pair = (primary, support)

    bonuses = {
        ("MAGE", "HEALER"): 0.18,
        ("ARCHER", "HEALER"): 0.16,
        ("ASSASSIN", "HEALER"): 0.15,
        ("TANK", "HEALER"): 0.12,
        ("MAGE", "TANK"): 0.08,
        ("ARCHER", "TANK"): 0.06,
        ("ASSASSIN", "TANK"): 0.04,
    }

    return round(bonuses.get(pair, 0.0), 6)


def support_penalty(primary: str, support: str) -> float:
    pair = (primary, support)

    penalties = {
        ("MAGE", "ASSASSIN"): 0.08,
        ("ARCHER", "ASSASSIN"): 0.06,
        ("ASSASSIN", "ARCHER"): 0.05,
        ("TANK", "ASSASSIN"): 0.03,
    }

    return round(penalties.get(pair, 0.0), 6)


def pair_bonus(primary: str, support: str) -> float:
    return round(support_bonus(primary, support) - support_penalty(primary, support), 6)


def select_support(primary: str, scores: Dict[str, float]) -> Tuple[str, float]:
    candidates = []

    for agent, score in scores.items():
        if agent == primary:
            continue

        total = score + pair_bonus(primary, agent)
        candidates.append((agent, round(total, 6)))

    if not candidates:
        return "NONE", 0.0

    candidates.sort(key=lambda x: x[1], reverse=True)
    best_agent, best_total = candidates[0]

    if best_total <= 0.0:
        return "NONE", 0.0

    return best_agent, best_total


def build_reason(task: Dict[str, Any], primary: str, support: str, pair_score: float) -> str:
    v = get_vector(task)
    parts = []

    if is_structural_task(task):
        parts.append("structural_super_priority")

    if is_macro_task(task):
        parts.append("no_path")

    if v["pressure"] >= 0.70:
        parts.append("high_pressure")

    if v["future"] >= 0.70:
        parts.append("high_future")

    if v["structure"] <= 0.30:
        parts.append("low_structure")

    if v["law"] <= 0.30:
        parts.append("low_law")

    if v["balance"] <= 0.35:
        parts.append("low_balance")

    if pair_score > 0:
        parts.append("pair_bonus")

    core = ",".join(parts[:6]) if parts else "generic"
    return f"{primary.lower()}+{support.lower()}:{core}"


def select_pair(task: Dict[str, Any]) -> Tuple[str, str, Dict[str, float], str]:
    scores = score_agents(task)

    primary = select_primary(scores)
    support, support_total = select_support(primary, scores)
    pair_score = pair_bonus(primary, support)

    scores_with_pair = dict(scores)
    scores_with_pair["_pair_bonus"] = round(pair_score, 6)
    scores_with_pair["_support_total"] = round(support_total, 6)

    reason = build_reason(task, primary, support, pair_score)
    return primary, support, scores_with_pair, reason


def select_agent(task: Dict[str, Any]) -> Tuple[str, Dict[str, float], str]:
    primary, support, scores, reason = select_pair(task)
    return primary, scores, reason
