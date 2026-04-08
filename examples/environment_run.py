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


    for env in envs:
        scored = []

        for name, data in results.items():
            env_score = apply_environment_to_score(data["metrics"], env)
            scored.append((name, env_score, data["metrics"]))

        scored.sort(key=lambda x: x[1], reverse=True)

        for name, env_score, metrics in scored:



if __name__ == "__main__":
    run_env_demo()
