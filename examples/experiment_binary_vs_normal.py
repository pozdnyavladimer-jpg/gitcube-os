from core.state import default_state
from runtime.agent_loop import choose_best_agent
from runtime.binary_cube import to_binary_state, state_to_tuple, transition_allowed


def run_experiment(steps=20):
    state = default_state()

    prev = None
    jumps = 0
    allowed_moves = 0

    for i in range(steps):
        best, results = choose_best_agent(state)
        metrics = results[best]["metrics"]

        binary = to_binary_state(metrics)
        current = state_to_tuple(binary)

        if prev is not None:
            if transition_allowed(prev, current):
                allowed_moves += 1
            else:
                jumps += 1

        prev = current

    return {
        "steps": steps,
        "allowed_moves": allowed_moves,
        "jumps": jumps,
    }


def demo():
    print("=== EXPERIMENT: STATE STABILITY ===")

    result = run_experiment(steps=30)

    print(result)

    print("\nInterpretation:")
    print("allowed_moves = smooth evolution")
    print("jumps = chaotic transitions")


if __name__ == "__main__":
    demo()
