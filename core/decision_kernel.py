from typing import Dict, Any


class DecisionKernel:
    """
    Central decision layer:
    - receives already-scored candidate results
    - applies repeat penalty + curiosity bonus
    - returns the best agent and candidate
    """

    def __init__(self):
        pass

    def decide(
        self,
        results: Dict[str, Any],
        temperature: float,
        state_visits: Dict,
    ) -> Dict[str, Any]:
        total_visits = sum(state_visits.values()) + 1

        best_agent = None
        best_score = float("-inf")
        best_data = None

        for agent_name, data in results.items():
            metrics = data["metrics"]
            candidate = data["candidate_tuple"]

            repeat_count = state_visits.get(candidate, 0)
            repeat_penalty = round(repeat_count * 0.03, 3)

            rarity = 1.0 - (repeat_count / total_visits)
            curiosity_bonus = round(rarity * 0.15 * temperature, 3)

            score = (
                metrics.get("coherence", 0.0)
                - metrics.get("shadow", 0.0)
                + metrics.get("target_fit", 0.0)
                + metrics.get("vitality", 0.0)
                - repeat_penalty
                + curiosity_bonus
            )

            score = round(score, 6)

            if score > best_score:
                best_score = score
                best_agent = agent_name
                best_data = data

        return {
            "agent": best_agent,
            "data": best_data,
            "score": best_score,
        }
