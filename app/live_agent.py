from typing import Dict, Any, List, Tuple
from collections import Counter

from app.state_engine import StateEngine
from app.view_model import build_view_model


class LiveAgent:
    def __init__(self, mode: str = "balanced"):
        self.engine = StateEngine(mode=mode)
        self.history: List[Dict[str, Any]] = []

    def reset(self):
        mode = self.engine.mode
        self.engine = StateEngine(mode=mode)
        self.history = []

    def set_mode(self, mode: str):
        self.engine.set_mode(mode)

    def step(self) -> Dict[str, Any]:
        result = self.engine.step()
        view = build_view_model(result)

        self.history.append(
            {
                "step": result["step"],
                "agent": result["agent"],
                "mode": result["mode"],
                "current": tuple(view["current"]),
                "decision": result["decision"]["decision"],
                "allowed": result["transition_allowed"],
                "summary": result["summary"],
            }
        )

        return {
            "result": result,
            "view": view,
            "history": self.history,
            "allowed_history": self.allowed_segments(),
            "blocked_history": self.blocked_segments(),
            "visit_counts": self.visit_counts(),
        }

    def run(self, steps: int = 10) -> Dict[str, Any]:
        packet = None
        for _ in range(steps):
            packet = self.step()
        return packet

    def trajectory(self) -> List[Tuple[int, int, int]]:
        return [item["current"] for item in self.history]

    def allowed_segments(self) -> List[Tuple[Tuple[int, int, int], Tuple[int, int, int]]]:
        segments = []
        if len(self.history) < 2:
            return segments

        for i in range(1, len(self.history)):
            prev_node = self.history[i - 1]["current"]
            curr_node = self.history[i]["current"]
            if self.history[i]["allowed"]:
                segments.append((prev_node, curr_node))
        return segments

    def blocked_segments(self) -> List[Tuple[Tuple[int, int, int], Tuple[int, int, int]]]:
        segments = []
        if len(self.history) < 2:
            return segments

        for i in range(1, len(self.history)):
            prev_node = self.history[i - 1]["current"]
            curr_node = self.history[i]["current"]
            if not self.history[i]["allowed"]:
                segments.append((prev_node, curr_node))
        return segments

    def visit_counts(self) -> Dict[Tuple[int, int, int], int]:
        counts = Counter(item["current"] for item in self.history)
        return dict(counts)
