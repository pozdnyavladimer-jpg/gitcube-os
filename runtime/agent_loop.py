import random
from typing import Dict, Any, Tuple

from core.state import SystemState, normalize_state
from core.evaluation import compute_metrics


CLASSES = {
    "TANK": {"pressure": -0.1, "structure": 0.2, "balance": 0.2},
    "ARCHER": {"balance": 0.2, "structure": 0.1, "future": 0.2},
    "MAGE": {"flow": 0.2, "future": 0.2, "pressure": 0.05},
    "HEALER": {"balance": 0.25, "flow": 0.1, "pressure": -0.15},
    "ASSASSIN": {"pressure": -0.2, "structure": -0.1, "future": 0.15},
}


def mutate_state(state: SystemState, weights: Dict[str, float]) -> SystemState:
    base = state.to_dict()

    new_values = {}

    for k, v in base.items():
        delta = weights.get(k, 0.0) * random.uniform(0.5, 1.5)
        new_values[k] = v + delta

    normalized = normalize_state(new_values)
    return SystemState.from_dict(normalized)


def choose_best_agent(current_state: Any) -> Tuple[str, Dict[str, Any]]:
    results = {}

    for agent in ["planner", "explorer", "stabilizer"]:
        best_score = -999
        best_class = None
        best_metrics = None
        best_state = None

        for class_name, weights in CLASSES.items():
            candidate_state = mutate_state(current_state, weights)
            metrics = compute_metrics(candidate_state)

            score = (
                metrics["coherence"]
                - metrics["shadow"]
                + metrics["target_fit"]
                + metrics["vitality"]
            )

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
