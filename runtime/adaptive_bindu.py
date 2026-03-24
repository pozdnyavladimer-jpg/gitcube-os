def adaptive_bindu_decision(metrics: dict, topo_result: dict) -> dict:
    shadow = metrics.get("shadow", 1.0)
    coherence = metrics.get("coherence", 0.0)

    flags = topo_result.get("flags", [])

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
    }
