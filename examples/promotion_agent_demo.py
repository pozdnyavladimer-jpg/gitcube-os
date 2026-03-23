from runtime.cube_agent import CubeAwareAgent
from runtime.promotion_agent import evaluate_promotion


def demo():
    agent = CubeAwareAgent("promotion_guard")

    scenarios = [
        ("gitcube-lab", "experimental"),
        ("geometric-state-navigator", "interpreted"),
        ("geometric-state-navigator", "canonical"),
        ("gitcube-os", "runtime"),
    ]

    print("=== PROMOTION AGENT DEMO ===")

    for repo_name, idea_status in scenarios:
        result = agent.inspect_repo(repo_name, idea_status)

        repo_type = result["repo_context"]["repo_type"]
        cube_validation = result["cube_validation"]

        promotion = evaluate_promotion(
            repo_type=repo_type,
            idea_status=idea_status,
            cube_validation=cube_validation,
        )

        print()
        print(f"repo: {repo_name}")
        print(f"idea_status: {idea_status}")
        print(f"cube_validation: {cube_validation}")
        print(f"promotion_decision: {promotion}")


if __name__ == "__main__":
    demo()
