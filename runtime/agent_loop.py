from typing import Dict, Tuple

from core.state import SystemState, normalize_state
from core.evaluation import compute_metrics, evaluate_status


AGENTS = {
    "planner": {
        "pressure": -0.04,
        "flow": 0.02,
        "structure": 0.10,
        "balance": 0.06,
        "law": 0.00,
        "future": 0.00,
    },
    "critic": {
        "pressure": -0.02,
        "flow": -0.04,
        "structure": 0.05,
        "balance": 0.00,
        "law": 0.10,
        "future": 0.00,
    },
    "explorer": {
        "pressure": 0.00,
        "flow": 0.12,
        "structure": -0.04,
        "balance": 0.00,
        "law": 0.00,
        "future": 0.05,
    },
    "stabilizer": {
        "pressure": -0.08,
        "flow": 0.03,
        "structure": 0.00,
        "balance": 0.10,
        "law": 0.00,
        "future": 0.00,
    },
}


def apply_delta(state: SystemState, delta: Dict[str, float]) -> SystemState:
    base = state.to_dict()
    updated = {k: base[k] + delta.get(k, 0.0) for k in base}
    return SystemState.from_dict(normalize_state(updated))


def score_state(state: SystemState) -> Tuple[float, Dict[str, float], str]:
    metrics = compute_metrics(state)
    verdict = evaluate_status(metrics)

    score = (
        metrics["coherence"] * 0.4
        - metrics["shadow"] * 0.3
        + metrics["target_fit"] * 0.2
        + metrics["vitality"] * 0.1
    )
    return round(score, 3), metrics, verdict


def choose_best_agent(state: SystemState):
    results = {}

    for name, delta in AGENTS.items():
        next_state = apply_delta(state, delta)
        score, metrics, verdict = score_state(next_state)
        results[name] = {
            "state": next_state,
            "score": score,
            "metrics": metrics,
            "verdict": verdict,
        }

    best_name = max(results.items(), key=lambda x: x[1]["score"])[0]
    return best_name, results
