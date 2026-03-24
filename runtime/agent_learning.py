def derive_agent_bias(memory_summary: dict) -> dict:
    """
    Build agent bias from memory history.

    Returns:
    {
        "planner": float,
        "stabilizer": float,
        "explorer": float,
    }
    """
    bias = {
        "planner": 0.0,
        "stabilizer": 0.0,
        "explorer": 0.0,
    }

    if not memory_summary:
        return bias

    statuses = memory_summary.get("statuses", []) or []
    agents = memory_summary.get("agents_used", []) or []

    if not statuses or not agents:
        return bias

    # pair as much as possible
    pairs = list(zip(agents, statuses))
    if not pairs:
        return bias

    total = len(pairs)

    agent_stats = {
        "planner": {"accepted": 0, "soft": 0, "total": 0},
        "stabilizer": {"accepted": 0, "soft": 0, "total": 0},
        "explorer": {"accepted": 0, "soft": 0, "total": 0},
    }

    for agent, status in pairs:
        if agent not in agent_stats:
            continue

        agent_stats[agent]["total"] += 1

        if status == "accepted":
            agent_stats[agent]["accepted"] += 1
        elif status == "soft":
            agent_stats[agent]["soft"] += 1

    for agent, stats in agent_stats.items():
        if stats["total"] == 0:
            continue

        accepted_ratio = stats["accepted"] / stats["total"]
        soft_ratio = stats["soft"] / stats["total"]
        usage_ratio = stats["total"] / total

        # accepted helps
        bonus = accepted_ratio * 0.15

        # too much soft hurts slightly
        penalty = soft_ratio * 0.08

        # domination penalty if same agent overused
        domination_penalty = 0.0
        if usage_ratio > 0.70:
            domination_penalty = (usage_ratio - 0.70) * 0.20

        bias[agent] = round(bonus - penalty - domination_penalty, 3)

    return bias
