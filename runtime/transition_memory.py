from typing import Dict


def derive_transition_memory(blocked_moves: int, allowed_moves: int) -> Dict[str, float]:
    total = blocked_moves + allowed_moves

    if total == 0:
        return {
            "blocked_ratio": 0.0,
            "caution_bias": 0.0,
            "coherence_penalty": 0.0,
        }

    blocked_ratio = blocked_moves / total

    return {
        "blocked_ratio": round(blocked_ratio, 3),
        "caution_bias": round(blocked_ratio * 0.1, 3),
        "coherence_penalty": round(blocked_ratio * 0.05, 3),
    }
