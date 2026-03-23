from runtime.cube_agent import build_cube_from_repo_context
from runtime.cube_stacking import stack_cubes


def demo():
    pairs = [
        ("gitcube-lab", "experimental", "geometric-state-navigator", "interpreted"),
        ("geometric-state-navigator", "canonical", "gitcube-os", "runtime"),
        ("gitcube-lab", "experimental", "gitcube-os", "runtime"),
    ]

    print("=== REPO PAIR STACKING DEMO ===")

    for repo_a, status_a, repo_b, status_b in pairs:
        cube_a = build_cube_from_repo_context(repo_a, status_a)
        cube_b = build_cube_from_repo_context(repo_b, status_b)

        result = stack_cubes(cube_a, cube_b)

        print()
        print(f"pair: {repo_a} ({status_a})  <->  {repo_b} ({status_b})")
        print(f"compatibility_score: {result['compatibility_score']}")
        print(f"shadow_pressure: {result['shadow_pressure']}")
        print(f"is_stackable: {result['is_stackable']}")
        print(f"is_crystal_stack: {result['is_crystal_stack']}")
        print(f"face_scores: {result['face_scores']}")


if __name__ == "__main__":
    demo()
