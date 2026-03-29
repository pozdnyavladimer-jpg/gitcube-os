import random
from typing import Dict, Any, Tuple


CLASSES = {
    "TANK": {"coherence": 0.6, "shadow": -0.6, "target_fit": 0.1, "vitality": 0.1},
    "ARCHER": {"coherence": 0.2, "shadow": -0.2, "target_fit": 0.8, "vitality": 0.2},
    "MAGE": {"coherence": 0.3, "shadow": -0.2, "target_fit": 0.3, "vitality": 0.7},
    "HEALER": {"coherence": 0.8, "shadow": -0.5, "target_fit": 0.1, "vitality": 0.2},
    "ASSASSIN": {"coherence": 0.2, "shadow": -0.4, "target_fit": 0.6, "vitality": 0.3},
}


def _generate_metrics(weights):
    return {
        "coherence": round(min(1.0, max(0.1, 0.5 + weights["coherence"] * random.uniform(0.1, 0.4))), 4),
        "shadow": round(min(1.0, max(0.0, 0.3 + weights["shadow"] * random.uniform(0.1, 0.3))), 4),
        "target_fit": round(min(1.0, max(0.1, 0.4 + weights["target_fit"] * random.uniform(0.1, 0.5))), 4),
        "vitality": round(min(1.0, max(0.1, 0.4 + weights["vitality"] * random.uniform(0.1, 0.5))), 4),
    }


def _score_class(metrics, weights):
    return (
        metrics["coherence"] * weights["coherence"]
        + metrics["shadow"] * weights["shadow"]
        + metrics["target_fit"] * weights["target_fit"]
        + metrics["vitality"] * weights["vitality"]
    )


def choose_best_agent(current_state: Any) -> Tuple[str, Dict[str, Any]]:
    results = {}

    for agent in ["planner", "explorer", "stabilizer"]:
        best_class = None
        best_score = -999
        best_metrics = None

        for class_name, weights in CLASSES.items():
            metrics = _generate_metrics(weights)
            score = _score_class(metrics, weights)

            if score > best_score:
                best_score = score
                best_class = class_name
                best_metrics = metrics

        candidate = (
            random.randint(0, 1),
            random.randint(0, 1),
            random.randint(0, 1),
        )

        results[agent] = {
            "metrics": best_metrics,
            "state": current_state,
            "candidate_tuple": candidate,
            "dominant_class": best_class,  # 🔥 КЛЮЧОВЕ
        }

    return "PARTY", results
