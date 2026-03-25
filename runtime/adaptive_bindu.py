from typing import Dict, Any, Optional


def adaptive_bindu(
    metrics: Dict[str, float],
    force_reject: bool = False,
    transition_memory: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    shadow = metrics.get("shadow", 0.0)
    coherence = metrics.get("coherence", 0.0)

    caution_bias = 0.0
    coherence_penalty = 0.0

    if transition_memory:
        caution_bias = transition_memory.get("caution_bias", 0.0)
        coherence_penalty = transition_memory.get("coherence_penalty", 0.0)

    thresholds = {
        "commit_shadow_max": round(0.10 - caution_bias, 3),
        "commit_coherence_min": round(0.90 + coherence_penalty, 3),
        "soft_shadow_max": round(0.15 - (caution_bias / 2), 3),
        "soft_coherence_min": round(0.83 + (coherence_penalty / 2), 3),
    }

    if force_reject:
        return {
            "decision": "REJECT",
            "reason": "blocked_transition",
            "thresholds": thresholds,
            "transition_memory": transition_memory or {},
        }

    if shadow <= thresholds["commit_shadow_max"] and coherence >= thresholds["commit_coherence_min"]:
        return {
            "decision": "COMMIT",
            "reason": "adaptive_commit",
            "thresholds": thresholds,
            "transition_memory": transition_memory or {},
        }

    if shadow <= thresholds["soft_shadow_max"] and coherence >= thresholds["soft_coherence_min"]:
        return {
            "decision": "SOFT_COMMIT",
            "reason": "adaptive_soft_commit",
            "thresholds": thresholds,
            "transition_memory": transition_memory or {},
        }

    return {
        "decision": "REJECT",
        "reason": "adaptive_reject",
        "thresholds": thresholds,
        "transition_memory": transition_memory or {},
    }
