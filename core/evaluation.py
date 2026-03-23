from typing import Dict

from core.state import SystemState


def compute_metrics(state: SystemState) -> Dict[str, float]:
    v = state.to_dict()

    shadow = v["pressure"]
    coherence = 1.0 - min(
        1.0,
        abs(v["balance"] - v["structure"])
        + abs(v["balance"] - v["flow"]),
    )
    target_fit = v["balance"] + v["structure"]
    vitality = v["flow"] + v["future"]

    return {
        "shadow": round(shadow, 3),
        "coherence": round(coherence, 3),
        "target_fit": round(target_fit, 3),
        "vitality": round(vitality, 3),
    }


def evaluate_status(metrics: Dict[str, float]) -> str:
    if metrics["shadow"] <= 0.08 and metrics["coherence"] >= 0.88:
        return "ALLOW"
    if metrics["shadow"] <= 0.16 and metrics["coherence"] >= 0.75:
        return "WARN"
    return "BLOCK"
