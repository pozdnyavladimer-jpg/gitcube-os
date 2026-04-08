from core.repo_context import detect_repo_context
from runtime.repo_agent import RepoAwareAgent


def demo():
    agent = RepoAwareAgent("organism_agent")

    scenarios = [
        ("gitcube-lab", "experimental"),
        ("geometric-state-navigator", "interpreted"),
        ("geometric-state-navigator", "canonical"),
        ("gitcube-os", "runtime"),
    ]


    for repo_name, idea_status in scenarios:
        context = detect_repo_context(repo_name, idea_status)
        inspected = agent.inspect(context)
        action = agent.recommend_action(context)



if __name__ == "__main__":
    demo()
