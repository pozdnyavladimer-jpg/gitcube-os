from core.state import default_state
from runtime.agent_loop import choose_best_agent


def main():
    state = default_state()


    best_name, results = choose_best_agent(state)

    for name, data in results.items():
            f"{name:10} | "
            f"score={data['score']} | "
            f"verdict={data['verdict']} | "
            f"metrics={data['metrics']}"
        )



if __name__ == "__main__":
    main()
