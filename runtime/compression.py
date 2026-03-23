from typing import Dict
from runtime.memory import EpisodeMemory


def compress_memory(memory: EpisodeMemory) -> Dict[str, object]:
    if memory.is_empty():
        return {
            "steps": 0,
            "accepted_count": 0,
            "soft_count": 0,
            "dominant_agent": None,
            "final_metrics": None,
            "final_state": None,
        }

    accepted_count = 0
    soft_count = 0
    agent_counts = {}

    for entry in memory.entries:
        if entry.status == "accepted":
            accepted_count += 1
        elif entry.status == "soft":
            soft_count += 1

        agent_counts[entry.agent] = agent_counts.get(entry.agent, 0) + 1

    dominant_agent = max(agent_counts.items(), key=lambda x: x[1])[0]
    last = memory.entries[-1]

    return {
        "steps": len(memory.entries),
        "accepted_count": accepted_count,
        "soft_count": soft_count,
        "dominant_agent": dominant_agent,
        "final_metrics": last.metrics,
        "final_state": last.state,
    }
