from dataclasses import dataclass
from typing import List


@dataclass
class RepoContext:
    repo_name: str
    repo_type: str
    idea_status: str
    allowed_actions: List[str]
    next_stage: str


def detect_repo_context(repo_name: str, idea_status: str = "experimental") -> RepoContext:
    repo_name = repo_name.strip().lower()

    if "lab" in repo_name:
        return RepoContext(
            repo_name=repo_name,
            repo_type="lab",
            idea_status=idea_status,
            allowed_actions=[
                "experiment",
                "mutate",
                "stress_test",
                "propose_candidate",
            ],
            next_stage="navigator",
        )

    if "navigator" in repo_name or "geometric-state-navigator" in repo_name:
        return RepoContext(
            repo_name=repo_name,
            repo_type="navigator",
            idea_status=idea_status,
            allowed_actions=[
                "interpret",
                "map_to_canon",
                "validate_thresholds",
                "approve_for_runtime",
            ],
            next_stage="os",
        )

    if "os" in repo_name:
        return RepoContext(
            repo_name=repo_name,
            repo_type="os",
            idea_status=idea_status,
            allowed_actions=[
                "execute",
                "bindu_gate",
                "write_memory",
                "reroute",
            ],
            next_stage="feedback",
        )

    return RepoContext(
        repo_name=repo_name,
        repo_type="unknown",
        idea_status=idea_status,
        allowed_actions=[],
        next_stage="unknown",
    )
