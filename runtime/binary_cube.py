from typing import Dict, Tuple


def to_binary_state(metrics: Dict[str, float]) -> Dict[str, int]:
    """
    Convert continuous metrics into binary state.
    """
    return {
        "shadow": int(metrics.get("shadow", 0.0) < 0.1),
        "coherence": int(metrics.get("coherence", 0.0) > 0.9),
        "fit": int(metrics.get("target_fit", 0.0) > 0.4),
    }


def state_to_tuple(state: Dict[str, int]) -> Tuple[int, int, int]:
    return (state["shadow"], state["coherence"], state["fit"])


def binary_score(state: Dict[str, int]) -> int:
    return sum(state.values())


def binary_decision(state: Dict[str, int]) -> str:
    score = binary_score(state)

    if score == 3:
        return "COMMIT"
    elif score == 2:
        return "SOFT_COMMIT"
    return "REJECT"


def hamming_distance(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> int:
    return sum(x != y for x, y in zip(a, b))


def transition_allowed(prev_state: Tuple[int, int, int], new_state: Tuple[int, int, int]) -> bool:
    """
    Allow only local transitions in binary cube.
    """
    return hamming_distance(prev_state, new_state) <= 1


def describe_state(state: Dict[str, int]) -> str:
    return f"(shadow={state['shadow']}, coherence={state['coherence']}, fit={state['fit']})"
