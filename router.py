import json
import math
import os
from typing import Dict, Any, Tuple

BUS_PATH = os.environ.get("V_RESONANCE_PATH", "v_resonance.json")

AGENTS = ("TANK", "MAGE", "ARCHER", "HEALER", "ASSASSIN")

STRUCTURAL_PROBLEMS = {
    "missing_init",
    "missing_init_group",
    "python_without_docs",
    "package_structure",
    "missing_root_readme",
    "missing_start_here",
}

PAIR_COMPATIBILITY = {
    ("MAGE", "HEALER"): 0.18,
    ("HEALER", "MAGE"): 0.18,
    ("ARCHER", "HEALER"): 0.12,
    ("HEALER", "ARCHER"): 0.12,
    ("TANK", "HEALER"): 0.10,
    ("HEALER", "TANK"): 0.10,
    ("ASSASSIN", "HEALER"): 0.08,
    ("HEALER", "ASSASSIN"): 0.08,
    ("MAGE", "TANK"): 0.06,
    ("TANK", "MAGE"): 0.06,
}

PAIR_PENALTY = {
    ("ASSASSIN", "ASSASSIN"): 0.20,
    ("TANK", "TANK"): 0.15,
    ("ARCHER", "ARCHER"): 0.10,
}


def clamp01(x: Any) -> float:
    try:
        return max(0.0, min(1.0, float(x)))
    except Exception:
        return 0.0


def load_json(path: str, default: Any):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def read_bus() -> Dict[str, Any]:
    data = load_json(BUS_PATH, {})
    return data if isinstance(data, dict) else {}


def get_memory_bias() -> Dict[str, float]:
    bus = read_bus()
    meta = bus.get("meta", {}) if isinstance(bus.get("meta"), dict) else {}
    raw = meta.get("memory_bias", {})
    if not isinstance(raw, dict):
        raw = {}

    out: Dict[str, float] = {}
    for agent in AGENTS:
        try:
            out[agent] = float(raw.get(agent, 0.0))
        except Exception:
            out[agent] = 0.0
    return out


def get_problem(task: Dict[str, Any]) -> str:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
    return str(payload.get("problem", "")).strip().lower()


def has_target_path(task: Dict[str, Any]) -> bool:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
    path = str(payload.get("path", "")).strip()
    paths = payload.get("paths", [])
    has_paths = isinstance(paths, list) and len(paths) > 0
    return bool(path or has_paths)


def is_structural(task: Dict[str, Any]) -> bool:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
    hint = str(payload.get("executor_hint", "")).strip().upper()
    return get_problem(task) in STRUCTURAL_PROBLEMS or hint == "MAGE"


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


def structural_super_priority(task: Dict[str, Any]) -> float:
    if not is_structural(task):
        return 0.0

    v = get_vector(task)
    bonus = 0.0

    if v["future"] >= 0.70:
        bonus += 0.35
    if v["structure"] <= 0.30:
        bonus += 0.30
    if v["law"] <= 0.35:
        bonus += 0.25
    if not has_target_path(task):
        bonus += 0.10

    return bonus


def score_agents(task: Dict[str, Any]) -> Dict[str, float]:
    v = get_vector(task)
    memory_bias = get_memory_bias()
    structural = is_structural(task)
    has_path = has_target_path(task)

    pressure = v["pressure"]
    flow = v["flow"]
    structure = v["structure"]
    balance = v["balance"]
    law = v["law"]
    future = v["future"]

    scores = {
        "TANK": 0.0,
        "MAGE": 0.0,
        "ARCHER": 0.0,
        "HEALER": 0.0,
        "ASSASSIN": 0.0,
    }

    # TANK: macro containment / high pressure / no-path risk
    scores["TANK"] += 0.55 * pressure
    if not has_path:
        scores["TANK"] += 0.25
    if structure <= 0.30:
        scores["TANK"] += 0.10
    if law <= 0.30:
        scores["TANK"] += 0.10

    # MAGE: structural evolution / low structure / future demand
    scores["MAGE"] += 0.65 * future
    scores["MAGE"] += 0.55 * max(0.0, 1.0 - structure)
    scores["MAGE"] += 0.35 * max(0.0, 1.0 - law)
    if structural:
        scores["MAGE"] += 0.45
    scores["MAGE"] += structural_super_priority(task)

    # ARCHER: path-driven precise action
    if has_path:
        scores["ARCHER"] += 0.55
    scores["ARCHER"] += 0.45 * flow
    scores["ARCHER"] += 0.20 * balance

    # HEALER: balance restoration / safe correction
    scores["HEALER"] += 0.55 * max(0.0, 1.0 - balance)
    scores["HEALER"] += 0.25 * max(0.0, 1.0 - law)
    scores["HEALER"] += 0.20 * pressure

    # ASSASSIN: deletion / harsh cleanup / high pressure + low law
    scores["ASSASSIN"] += 0.40 * pressure
    scores["ASSASSIN"] += 0.35 * max(0.0, 1.0 - law)
    scores["ASSASSIN"] += 0.20 * max(0.0, 1.0 - structure)

    # memory-aware routing (soft influence)
    # bounded effect: enough to guide, not enough to dominate
    scores["TANK"] += 0.20 * memory_bias.get("TANK", 0.0)
    scores["MAGE"] += 0.25 * memory_bias.get("MAGE", 0.0)
    scores["ARCHER"] += 0.20 * memory_bias.get("ARCHER", 0.0)
    scores["HEALER"] += 0.20 * memory_bias.get("HEALER", 0.0)
    scores["ASSASSIN"] += 0.20 * memory_bias.get("ASSASSIN", 0.0)

    # mild damping so negative bias can matter a bit
    for agent in scores:
        scores[agent] = round(max(0.0, scores[agent]), 6)

    return scores


def select_primary(scores: Dict[str, float]) -> str:
    return max(scores, key=scores.get)


def select_support(primary: str, scores: Dict[str, float]) -> Tuple[str, float]:
    candidates = []

    for agent, base_score in scores.items():
        if agent == primary:
            continue

        pair_bonus = PAIR_COMPATIBILITY.get((primary, agent), 0.0)
        pair_penalty = PAIR_PENALTY.get((primary, agent), 0.0)
        total = base_score + pair_bonus - pair_penalty
        candidates.append((agent, total))

    if not candidates:
        return primary, float(scores.get(primary, 0.0))

    candidates.sort(key=lambda x: x[1], reverse=True)
    support, total = candidates[0]
    return support, round(total, 6)


def pair_bonus(primary: str, support: str) -> float:
    return round(
        PAIR_COMPATIBILITY.get((primary, support), 0.0)
        - PAIR_PENALTY.get((primary, support), 0.0),
        6,
    )


def build_reason(task: Dict[str, Any], primary: str, support: str, pair_score: float) -> str:
    v = get_vector(task)
    parts = []

    if is_structural(task):
        parts.append("structural_super_priority")

    if not has_target_path(task):
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

    memory_bias = get_memory_bias()
    if abs(memory_bias.get(primary, 0.0)) > 0.0001:
        parts.append("memory_bias")

    core = ",".join(parts[:8]) if parts else "generic"
    return f"{primary.lower()}+{support.lower()}:{core}"


def select_pair(task: Dict[str, Any]) -> Tuple[str, str, Dict[str, float], str]:
    scores = score_agents(task)
    primary = select_primary(scores)
    support, support_total = select_support(primary, scores)
    pbonus = pair_bonus(primary, support)

    scores_with_pair = dict(scores)
    scores_with_pair["_pair_bonus"] = round(pbonus, 6)
    scores_with_pair["_support_total"] = round(support_total, 6)

    reason = build_reason(task, primary, support, pbonus)
    return primary, support, scores_with_pair, reason


def select_agent(task: Dict[str, Any]) -> Tuple[str, Dict[str, float], str]:
    primary, _support, scores, reason = select_pair(task)
    return primary, scores, reason
