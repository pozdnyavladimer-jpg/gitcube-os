def update_memory(memory, allowed, rejected, coherence, shadow):
    total = memory.get("total_steps", 0) + 1
    blocked = memory.get("blocked_steps", 0) + (1 if rejected else 0)

    memory["total_steps"] = total
    memory["blocked_steps"] = blocked
    memory["blocked_ratio"] = blocked / total

    # чим більше reject streak, тим обережніша система
    memory["caution_bias"] = min(1.0, memory.get("caution_bias", 0.0) * 0.9 + (0.05 if rejected else -0.03))
    memory["caution_bias"] = max(0.0, memory["caution_bias"])

    # penalty якщо coherence падає
    memory["coherence_penalty"] = max(0.0, 0.5 - coherence) if coherence < 0.5 else 0.0

    # маленький shadow trace
    memory["last_shadow"] = shadow
    memory["last_coherence"] = coherence

    return memory
