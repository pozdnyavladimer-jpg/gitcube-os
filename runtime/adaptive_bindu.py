def adaptive_bindu_decision(metrics: dict, topo_result: dict, memory_control: dict | None = None) -> dict:
    shadow = metrics.get("shadow", 1.0)
    coherence = metrics.get("coherence", 0.0)

    flags = topo_result.get("flags", [])
    memory_control = memory_control or {}

    commit_shadow_max = 0.10
    commit_coherence_min = 0.85

    soft_shadow_max = 0.15
    soft_coherence_min = 0.80

    # --- adaptive influence from topo flags ---
    if "overfit" in flags:
        commit_coherence_min += 0.05
        soft_coherence_min += 0.03

    if "low_coherence" in flags:
        commit_coherence_min += 0.08
        soft_coherence_min += 0.05

    if "resonance_loss" in flags:
        commit_shadow_max -= 0.02
        soft_shadow_max -= 0.02

    # --- memory influence ---
    coherence_bonus = memory_control.get("coherence_bonus", 0.0)
    caution_bias = memory_control.get("caution_bias", 0.0)
    shadow_tolerance_penalty = memory_control.get("shadow_tolerance_penalty", 0.0)

    commit_coherence_min += caution_bias
    soft_coherence_min += caution_bias

    commit_coherence_min -= coherence_bonus
    soft_coherence_min -= coherence_bonus

    commit_shadow_max -= shadow_tolerance_penalty
    soft_shadow_max -= shadow_tolerance_penalty

    # clamp practical bounds
    commit_shadow_max = max(0.03, min(0.20, commit_shadow_max))
    soft_shadow_max = max(0.05, min(0.25, soft_shadow_max))
    commit_coherence_min = max(0.70, min(0.95, commit_coherence_min))
    soft_coherence_min = max(0.65, min(0.90, soft_coherence_min))

    # --- hard reject region ---
    if shadow > soft_shadow_max or coherence < soft_coherence_min:
        return {
            "decision": "REJECT",
            "reason": "adaptive_reject",
            "thresholds": {
                "commit_shadow_max": round(commit_shadow_max, 3),
                "commit_coherence_min": round(commit_coherence_min, 3),
                "soft_shadow_max": round(soft_shadow_max, 3),
                "soft_coherence_min": round(soft_coherence_min, 3),
            },
            "memory_control": memory_control,
        }

    # --- commit region ---
    if shadow <= commit_shadow_max and coherence >= commit_coherence_min:
        return {
            "decision": "COMMIT",
            "reason": "adaptive_commit",
            "thresholds": {
                "commit_shadow_max": round(commit_shadow_max, 3),
                "commit_coherence_min": round(commit_coherence_min, 3),
                "soft_shadow_max": round(soft_shadow_max, 3),
                "soft_coherence_min": round(soft_coherence_min, 3),
            },
            "memory_control": memory_control,
        }

    # --- otherwise soft ---
    return {
        "decision": "SOFT_COMMIT",
        "reason": "adaptive_soft_commit",
        "thresholds": {
            "commit_shadow_max": round(commit_shadow_max, 3),
            "commit_coherence_min": round(commit_coherence_min, 3),
            "soft_shadow_max": round(soft_shadow_max, 3),
            "soft_coherence_min": round(soft_coherence_min, 3),
        },
        "memory_control": memory_control,
    }
