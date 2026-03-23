from dataclasses import asdict
from typing import Dict

from core.cube_validator import CubeState, validate_cube
from core.repo_context import detect_repo_context
from runtime.repo_agent import RepoAwareAgent


def build_cube_from_repo_context(repo_name: str, idea_status: str) -> CubeState:
    """
    Minimal heuristic mapping from repo/lifecycle state to CubeState.
    Values are in 0..1 range.
    """

    repo = repo_name.lower().strip()
    status = idea_status.lower().strip()

    if "lab" in repo:
        return CubeState(
            pressure=0.45,   # experiments create instability
            flow=0.85,       # high movement
            structure=0.45,  # raw structure
            balance=0.40,    # low coherence
            law=0.30,        # low canonical compliance
            future=0.90,     # strong future / mutation
        )

    if "navigator" in repo:
        if status == "canonical":
            return CubeState(
                pressure=0.18,
                flow=0.55,
                structure=0.88,
                balance=0.84,
                law=0.92,
                future=0.35,
            )

        return CubeState(
            pressure=0.25,
            flow=0.60,
            structure=0.75,
            balance=0.72,
            law=0.80,
            future=0.45,
        )

    if "os" in repo:
        return CubeState(
            pressure=0.20,
            flow=0.65,
            structure=0.86,
            balance=0.82,
            law=0.90,
            future=0.30,
        )

    return CubeState(
        pressure=0.50,
        flow=0.50,
        structure=0.50,
        balance=0.50,
        law=0.50,
        future=0.50,
    )


class CubeAwareAgent:
    def __init__(self, name: str):
        self.name = name
        self.repo_agent = RepoAwareAgent(name)

    def inspect_repo(self, repo_name: str, idea_status: str) -> Dict[str, object]:
        context = detect_repo_context(repo_name, idea_status)
        cube = build_cube_from_repo_context(repo_name, idea_status)
        cube_result = validate_cube(cube)
        action = self.repo_agent.recommend_action(context)

        guarded_action = action
        if context.repo_type == "os" and not cube_result.is_stable:
            guarded_action = "reroute"

        return {
            "agent": self.name,
            "repo_context": asdict(context),
            "cube_state": asdict(cube),
            "cube_validation": asdict(cube_result),
            "recommended_action": action,
            "guarded_action": guarded_action,
        }
