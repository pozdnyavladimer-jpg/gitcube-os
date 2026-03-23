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

    print("=== REPO AWARENESS DEMO ===")

    for repo_name, idea_status in scenarios:
        context = detect_repo_context(repo_name, idea_status)
        inspected = agent.inspect(context)
        action = agent.recommend_action(context)

        print()
        print(f"repo: {repo_name}")
        print(f"context: {inspected}")
        print(f"recommended_action: {action}")


if __name__ == "__main__":
    demo()
