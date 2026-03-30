import random
from typing import Dict, Any, Tuple

from core.state import SystemState, normalize_state
from core.evaluation import compute_metrics


CLASSES = {
    "TANK": {
        "pressure": -0.08,
        "structure": 0.18,
        "balance": 0.16,
        "law": 0.04,
    },
    "ARCHER": {
        "balance": 0.16,
        "structure": 0.08,
        "future": 0.18,
        "flow": 0.04,
    },
    "MAGE": {
        "flow": 0.18,
        "future": 0.18,
        "pressure": 0.04,
        "balance": 0.04,
    },
    "HEALER": {
        "balance": 0.22,
        "flow": 0.08,
        "pressure": -0.12,
        "law": 0.04,
    },
    "ASSASSIN": {
        "pressure": -0.10,
        "structure": -0.05,
        "future": 0.10,
        "balance": -0.02,
    },
}


def mutate_state(state: SystemState, weights: Dict[str, float]) -> SystemState:
    base = state.to_dict()
    new_values = {}

    for k, v in base.items():
        delta = weights.get(k, 0.0) * random.uniform(0.55, 1.35)
        new_values[k] = v + delta

    normalized = normalize_state(new_values)
    return SystemState.from_dict(normalized)


def _class_score(class_name: str, metrics: Dict[str, float]) -> float:
    coherence = metrics["coherence"]
    shadow = metrics["shadow"]
    target_fit = metrics["target_fit"]
    vitality = metrics["vitality"]

    # базова формула
    score = coherence - shadow + target_fit + vitality

    # --- BALANCE FIX ---

    if class_name == "TANK":
        score += 0.08
        if shadow > 0.12:
            score += 0.08
        if coherence < 0.86:
            score += 0.05

    elif class_name == "HEALER":
        score += 0.10
        if shadow > 0.10:
            score += 0.12
        if vitality < 0.4:
            score += 0.10

    elif class_name == "MAGE":
        score += 0.03
        if vitality > 0.75:
            score += 0.05
        if target_fit > 0.35:
            score += 0.03

    elif class_name == "ARCHER":
        score += 0.07
        if target_fit > 0.34:
            score += 0.10
        if coherence > 0.88:
            score += 0.04

    elif class_name == "ASSASSIN":
        # кризовий клас — не базовий
        score -= 0.22
        if shadow > 0.14:
            score += 0.18
        if coherence > 0.92 and shadow < 0.08:
            score -= 0.10
        if target_fit < 0.18:
            score -= 0.05

    return score


def choose_best_agent(current_state: Any) -> Tuple[str, Dict[str, Any]]:
    results = {}

    for agent in ["planner", "explorer", "stabilizer"]:
        best_score = -999.0
        best_class = None
        best_metrics = None
        best_state = None

        for class_name, weights in CLASSES.items():
            candidate_state = mutate_state(current_state, weights)
            metrics = compute_metrics(candidate_state)

            score = _class_score(class_name, metrics)

            if score > best_score:
                best_score = score
                best_class = class_name
                best_metrics = metrics
                best_state = candidate_state

        results[agent] = {
            "metrics": best_metrics,
            "state": best_state,
            "dominant_class": best_class,
        }

    return "PARTY", results
