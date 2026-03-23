from core.state import default_state
from runtime.agent_loop import choose_best_agent
from runtime.memory import EpisodeMemory


def run_episode(steps=5):
    state = default_state()
    memory = EpisodeMemory()

    print("=== START EPISODE ===")

    for step in range(steps):
        print(f"\n--- step {step} ---")

        best, results = choose_best_agent(state)
        best_data = results[best]

        print(f"selected: {best}")
        print(f"metrics: {best_data['metrics']}")

        memory.add(
            step=step,
            agent=best,
            metrics=best_data["metrics"],
            state=best_data["state"].to_dict(),
        )

        state = best_data["state"]

    print("\n=== FINAL STATE ===")
    print(state.to_dict())

    print("\n=== MEMORY SUMMARY ===")
    print(memory.summary())


if __name__ == "__main__":
    run_episode(steps=5)
