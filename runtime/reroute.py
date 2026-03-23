from typing import Dict, Tuple
from runtime.environment_score import apply_environment_to_score


def choose_next_agent(results: Dict, rejected_agent: str, env=None) -> Tuple[str, Dict]:
    alternatives = [
        (name, data)
        for name, data in results.items()
        if name != rejected_agent
    ]

    if not alternatives:
        return rejected_agent, results[rejected_agent]

    if env is None:
        alternatives.sort(key=lambda item: item[1]["score"], reverse=True)
        return alternatives[0]

    alternatives.sort(
        key=lambda item: apply_environment_to_score(item[1]["metrics"], env),
        reverse=True,
    )
    return alternatives[0]
