from runtime.cube_agent import build_cube_from_repo_context
from runtime.cube_stacking import stack_cubes


def demo():
    pairs = [
        ("gitcube-lab", "experimental", "geometric-state-navigator", "interpreted"),
        ("geometric-state-navigator", "canonical", "gitcube-os", "runtime"),
        ("gitcube-lab", "experimental", "gitcube-os", "runtime"),
    ]


    for repo_a, status_a, repo_b, status_b in pairs:
        cube_a = build_cube_from_repo_context(repo_a, status_a)
        cube_b = build_cube_from_repo_context(repo_b, status_b)

        result = stack_cubes(cube_a, cube_b)



if __name__ == "__main__":
    demo()
