from typing import Dict, Tuple


def choose_next_agent(results: Dict, rejected_agent: str) -> Tuple[str, Dict]:
    """
    Pick the best alternative agent after rejection.
    Excludes the rejected agent and returns the next best by score.
    """

    alternatives = [
        (name, data)
        for name, data in results.items()
        if name != rejected_agent
    ]

    if not alternatives:
        return rejected_agent, results[rejected_agent]

    alternatives.sort(key=lambda item: item[1]["score"], reverse=True)
    return alternatives[0]
