from collections import Counter
from typing import List, Tuple, Dict, Any


StateTuple = Tuple[int, int, int]


class PerelmanGuard:
    """
    Guard against loop traps:
    - detect repeated states
    - force escape into a less-visited candidate
    """

    def __init__(self, loop_threshold: int = 12):
        self.loop_threshold = loop_threshold

    def detect_loop(self, history: List[StateTuple]) -> Tuple[bool, StateTuple | None, int]:
        if not history:
            return False, None, 0

        counts = Counter(history)

        for state, count in counts.items():
            if count >= self.loop_threshold:
                return True, state, count

        return False, None, 0

    def force_escape(
        self,
        current: StateTuple,
        candidates: List[Dict[str, Any]],
    ) -> StateTuple:
        """
        Pick the least-visited candidate different from current.
        If all are same, return current.
        """
        if not candidates:
            return current

        sorted_candidates = sorted(
            candidates,
            key=lambda x: (x["visits"], x["state"] == current)
        )

        for item in sorted_candidates:
            if item["state"] != current:
                return item["state"]

        return current
