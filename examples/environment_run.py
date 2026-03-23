from core.state import default_state
from runtime.agent_loop import choose_best_agent
from runtime.environment_score import apply_environment_to_score
from environments.balanced import BALANCED
from environments.harsh import HARSH
from environments.exploratory import EXPLORATORY


def run_env_demo():
    state = default_state()
    best, results = choose_best_agent(state)

    envs = [BALANCED, HARSH, EXPLORATORY]

    print("=== ENVIRONMENT DEMO ===")
    print()

    for env in envs:
        print(f"--- environment: {env.name} ---")
        scored = []

        for name, data in results.items():
            env_score = apply_environment_to_score(data["metrics"], env)
            scored.append((name, env_score, data["metrics"]))

        scored.sort(key=lambda x: x[1], reverse=True)

        for name, env_score, metrics in scored:
            print(f"{name:10} | env_score={env_score} | metrics={metrics}")

        print(f"selected_in_{env.name}: {scored[0][0]}")
        print()


if __name__ == "__main__":
    run_env_demo()
