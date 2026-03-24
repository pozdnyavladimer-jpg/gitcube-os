from typing import Dict, List


def fibonacci_sequence(n: int) -> List[int]:
    if n <= 0:
        return []
    if n == 1:
        return [1]

    seq = [1, 1]
    while len(seq) < n:
        seq.append(seq[-1] + seq[-2])
    return seq[:n]


def normalize_weights(values: List[float]) -> List[float]:
    total = sum(values)
    if total == 0:
        return [0.0 for _ in values]
    return [v / total for v in values]


def linear_rank_weights(n: int) -> List[float]:
    """
    Simple linear weights:
    n=4 -> [1, 2, 3, 4] normalized
    """
    vals = [float(i) for i in range(1, n + 1)]
    return normalize_weights(vals)


def fibonacci_rank_weights(n: int) -> List[float]:
    """
    Fibonacci weights:
    n=4 -> [1, 1, 2, 3] normalized
    """
    vals = [float(x) for x in fibonacci_sequence(n)]
    return normalize_weights(vals)


def apply_rank_scaling(scores: Dict[str, float], mode: str = "linear") -> Dict[str, float]:
    """
    Sort agents by score, then apply rank-based scaling.

    This is useful as an experiment:
    - linear: gentle preference for top-ranked candidates
    - fibonacci: stronger non-linear compression toward top candidates
    """
    items = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    n = len(items)

    if mode == "fibonacci":
        weights = fibonacci_rank_weights(n)
    else:
        weights = linear_rank_weights(n)

    scaled = {}
    for (agent, score), weight in zip(items, weights):
        scaled[agent] = round(score * (1.0 + weight), 6)

    return scaled


def compare_scaling(scores: Dict[str, float]) -> Dict[str, Dict[str, float]]:
    return {
        "raw": {k: round(v, 6) for k, v in scores.items()},
        "linear": apply_rank_scaling(scores, mode="linear"),
        "fibonacci": apply_rank_scaling(scores, mode="fibonacci"),
    }
