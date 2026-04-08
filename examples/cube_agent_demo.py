from runtime.cube_agent import CubeAwareAgent


def demo():
    agent = CubeAwareAgent("cube_guard")

    scenarios = [
        ("gitcube-lab", "experimental"),
        ("geometric-state-navigator", "interpreted"),
        ("geometric-state-navigator", "canonical"),
        ("gitcube-os", "runtime"),
    ]


    for repo_name, idea_status in scenarios:
        result = agent.inspect_repo(repo_name, idea_status)



if __name__ == "__main__":
    demo()
