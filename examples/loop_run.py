from core.state import default_state
from runtime.agent_loop import choose_best_agent


def run_episode(steps=5):
    state = default_state()

    print("=== START EPISODE ===")

    for step in range(steps):
        print(f"\n--- step {step} ---")

        best, results = choose_best_agent(state)

        print(f"selected: {best}")
        print(f"metrics: {results[best]['metrics']}")

        state = results[best]["state"]

    print("\n=== FINAL STATE ===")
    print(state.to_dict())


if __name__ == "__main__":
    run_episode(steps=5)
