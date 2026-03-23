from typing import Dict


def bindu_decision(metrics: Dict[str, float]) -> Dict[str, str]:
    """
    Minimal canonical Bindu runtime decision.
    """

    shadow = metrics.get("shadow", 1.0)
    coherence = metrics.get("coherence", 0.0)
    target_fit = metrics.get("target_fit", 0.0)
    vitality = metrics.get("vitality", 0.0)

    # COMMIT
    if coherence >= 0.85 and shadow <= 0.10:
        return {
            "decision": "COMMIT",
            "reason": "stable_state",
        }

    # SOFT COMMIT
    if coherence >= 0.80 and shadow <= 0.15:
        return {
            "decision": "SOFT_COMMIT",
            "reason": "transitional_state",
        }

    # Optional extended checks
    if vitality < 0.20:
        return {
            "decision": "REJECT",
            "reason": "low_vitality",
        }

    if target_fit < 0.30:
        return {
            "decision": "REJECT",
            "reason": "low_target_fit",
        }

    # Hard reject
    if shadow > 0.15:
        return {
            "decision": "REJECT",
            "reason": "high_shadow",
        }

    if coherence < 0.80:
        return {
            "decision": "REJECT",
            "reason": "low_coherence",
        }

    return {
        "decision": "REJECT",
        "reason": "unknown",
    }
