from runtime.cube_agent import CubeAwareAgent
from runtime.action_guard import guard_action


def demo():
    agent = CubeAwareAgent("guard_agent")

    scenarios = [
        ("gitcube-lab", "experimental"),
        ("geometric-state-navigator", "interpreted"),
        ("geometric-state-navigator", "canonical"),
        ("gitcube-os", "runtime"),
    ]


    for repo_name, idea_status in scenarios:
        result = agent.inspect_repo(repo_name, idea_status)

        repo_type = result["repo_context"]["repo_type"]
        allowed_actions = result["repo_context"]["allowed_actions"]
        cube_validation = result["cube_validation"]
        requested_action = result["guarded_action"]

        guard = guard_action(
            repo_type=repo_type,
            idea_status=idea_status,
            requested_action=requested_action,
            cube_validation=cube_validation,
            allowed_actions=allowed_actions,
        )



if __name__ == "__main__":
    demo()
