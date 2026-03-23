from runtime.cube_agent import CubeAwareAgent


def demo():
    agent = CubeAwareAgent("cube_guard")

    scenarios = [
        ("gitcube-lab", "experimental"),
        ("geometric-state-navigator", "interpreted"),
        ("geometric-state-navigator", "canonical"),
        ("gitcube-os", "runtime"),
    ]

    print("=== CUBE AWARE AGENT DEMO ===")

    for repo_name, idea_status in scenarios:
        result = agent.inspect_repo(repo_name, idea_status)

        print()
        print(f"repo: {repo_name}")
        print(f"idea_status: {idea_status}")
        print(f"repo_type: {result['repo_context']['repo_type']}")
        print(f"cube_state: {result['cube_state']}")
        print(f"cube_validation: {result['cube_validation']}")
        print(f"recommended_action: {result['recommended_action']}")
        print(f"guarded_action: {result['guarded_action']}")


if __name__ == "__main__":
    demo()
