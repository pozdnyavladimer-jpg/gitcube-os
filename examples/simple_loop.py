from core.state import default_state
from runtime.agent_loop import choose_best_agent


def main():
    state = default_state()

    print("=== INITIAL STATE ===")
    print(state.to_dict())
    print()

    best_name, results = choose_best_agent(state)

    print("=== AGENT RESULTS ===")
    for name, data in results.items():
        print(
            f"{name:10} | "
            f"score={data['score']} | "
            f"verdict={data['verdict']} | "
            f"metrics={data['metrics']}"
        )

    print()
    print("=== SELECTED AGENT ===")
    print(best_name)
    print(results[best_name]["state"].to_dict())


if __name__ == "__main__":
    main()
