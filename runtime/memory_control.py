def derive_memory_control(memory_summary: dict) -> dict:
    """
    Convert memory summary into adaptive control signals.

    Returns:
    - coherence_bonus
    - shadow_tolerance_penalty
    - caution_bias
    """
    if not memory_summary:
        return {
            "coherence_bonus": 0.0,
            "shadow_tolerance_penalty": 0.0,
            "caution_bias": 0.0,
        }

    steps = memory_summary.get("steps", 0) or 0
    statuses = memory_summary.get("statuses", []) or []
    accepted_count = sum(1 for s in statuses if s == "accepted")
    soft_count = sum(1 for s in statuses if s == "soft")

    if steps == 0:
        return {
            "coherence_bonus": 0.0,
            "shadow_tolerance_penalty": 0.0,
            "caution_bias": 0.0,
        }

    accepted_ratio = accepted_count / steps
    soft_ratio = soft_count / steps

    # If system often reaches accepted states, we allow slightly more confidence
    coherence_bonus = accepted_ratio * 0.03

    # Too many soft decisions mean system is uncertain -> tighten a bit
    caution_bias = soft_ratio * 0.05

    # If too many softs, reduce tolerated shadow slightly
    shadow_tolerance_penalty = soft_ratio * 0.02

    return {
        "coherence_bonus": round(coherence_bonus, 3),
        "shadow_tolerance_penalty": round(shadow_tolerance_penalty, 3),
        "caution_bias": round(caution_bias, 3),
    }
