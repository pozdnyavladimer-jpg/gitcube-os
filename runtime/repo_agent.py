from typing import Dict
from core.repo_context import RepoContext


class RepoAwareAgent:
    def __init__(self, name: str):
        self.name = name

    def inspect(self, context: RepoContext) -> Dict[str, object]:
        return {
            "agent": self.name,
            "repo_type": context.repo_type,
            "idea_status": context.idea_status,
            "allowed_actions": context.allowed_actions,
            "next_stage": context.next_stage,
        }

    def recommend_action(self, context: RepoContext) -> str:
        if context.repo_type == "lab":
            if context.idea_status == "experimental":
                return "propose_candidate"
            return "stress_test"

        if context.repo_type == "navigator":
            if context.idea_status in ["experimental", "interpreted"]:
                return "map_to_canon"
            if context.idea_status == "canonical":
                return "approve_for_runtime"
            return "validate_thresholds"

        if context.repo_type == "os":
            if context.idea_status in ["canonical", "runtime"]:
                return "execute"
            return "reroute"

        return "hold"
