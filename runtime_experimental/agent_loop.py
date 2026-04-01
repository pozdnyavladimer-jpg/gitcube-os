# runtime_experimental/agent_loop.py

import random
from typing import Dict, Any, Tuple, Optional

from core.state import SystemState, normalize_state
from core.evaluation import compute_metrics
from runtime_experimental.role_transaction import role_transaction


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


def _base_class_score(class_name: str, metrics: Dict[str, float]) -> float:
    coherence = metrics["coherence"]
    shadow = metrics["shadow"]
    target_fit = metrics["target_fit"]
    vitality = metrics["vitality"]

    score = coherence - shadow + target_fit + vitality

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
        if vitality < 0.40:
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
        score -= 0.22
        if shadow > 0.14:
            score += 0.18
        if coherence > 0.92 and shadow < 0.08:
            score -= 0.10
        if target_fit < 0.18:
            score -= 0.05

    return score


def _field_weighted_score(
    metrics: Dict[str, float],
    field: Dict[str, Any],
) -> float:
    weights = field.get("weights", {}) if isinstance(field, dict) else {}

    shadow_w = float(weights.get("shadow", 1.0))
    coherence_w = float(weights.get("coherence", 1.0))
    target_fit_w = float(weights.get("target_fit", 1.0))
    vitality_w = float(weights.get("vitality", 1.0))

    score = (
        metrics["coherence"] * coherence_w
        - metrics["shadow"] * shadow_w
        + metrics["target_fit"] * target_fit_w
        + metrics["vitality"] * vitality_w
    )
    return score


def _agent_style_bias(agent_name: str, metrics: Dict[str, float], field: Dict[str, Any]) -> float:
    """
    planner     -> coherence / safer transitions
    explorer    -> target_fit / vitality / movement
    stabilizer  -> suppress shadow / structure preservation
    """
    shadow = metrics["shadow"]
    coherence = metrics["coherence"]
    target_fit = metrics["target_fit"]
    vitality = metrics["vitality"]

    mode = str(field.get("mode", "active"))
    phase = str(field.get("phase", "DAY"))

    bias = 0.0

    if agent_name == "planner":
        bias += coherence * 0.12
        bias -= shadow * 0.08
        if mode == "crisis":
            bias += 0.04

    elif agent_name == "explorer":
        bias += target_fit * 0.10
        bias += vitality * 0.08
        if phase == "DAY":
            bias += 0.03
        if mode == "calm":
            bias += 0.04

    elif agent_name == "stabilizer":
        bias += coherence * 0.08
        bias -= shadow * 0.12
        if mode == "crisis":
            bias += 0.08

    return round(bias, 6)


def choose_best_agent(
    current_state: Any,
    *,
    vitality: float,
    field: Dict[str, Any],
    class_history: Optional[list] = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Experimental field-aware agent selection.

    Returns:
    "PARTY", {
        "planner": {...},
        "explorer": {...},
        "stabilizer": {...},
    }
    """
    if class_history is None:
        class_history = []

    results = {}

    for agent in ["planner", "explorer", "stabilizer"]:
        best_score = -999.0
        best_class = None
        best_metrics = None
        best_state = None
        best_role_tx = None
        best_score_parts = None

        for class_name, weights in CLASSES.items():
            candidate_state = mutate_state(current_state, weights)
            metrics = compute_metrics(candidate_state)

            base_score = _base_class_score(class_name, metrics)
            field_score = _field_weighted_score(metrics, field)
            style_bias = _agent_style_bias(agent, metrics, field)

            tx = role_transaction(
                class_name=class_name,
                metrics=metrics,
                vitality=vitality,
                field=field,
                history_len=len(class_history),
            )

            score = (
                base_score * 0.40
                + field_score * 0.45
                + style_bias
                + float(tx.get("role_score", 0.0)) * 0.25
            )

            if score > best_score:
                best_score = score
                best_class = class_name
                best_metrics = metrics
                best_state = candidate_state
                best_role_tx = tx
                best_score_parts = {
                    "base_class_score": round(base_score, 6),
                    "field_score": round(field_score, 6),
                    "style_bias": round(style_bias, 6),
                    "role_score": round(float(tx.get("role_score", 0.0)), 6),
                }

        results[agent] = {
            "metrics": best_metrics,
            "state": best_state,
            "dominant_class": best_class,
            "role_transaction": best_role_tx,
            "experimental_score_parts": best_score_parts,
            "experimental_score": round(best_score, 6),
        }

    return "PARTY", results
