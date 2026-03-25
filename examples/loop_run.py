from core.state import default_state
from runtime.agent_loop import choose_best_agent
from runtime.adaptive_bindu import adaptive_bindu
from runtime.binary_cube import (
    to_binary_state,
    state_to_tuple,
    transition_allowed,
)
from runtime.transition_memory import derive_transition_memory


def run(steps: int = 12):
    state = default_state()
    prev_tuple = None

    allowed_moves = 0
    blocked_moves = 0

    print("\n=== GITCUBE OS LOOP (WITH BINARY CONSTRAINT + TRANSITION MEMORY) ===\n")

    for step in range(steps):
        print(f"--- step {step} ---")

        best_agent, results = choose_best_agent(state)
        best_data = results[best_agent]
        metrics = best_data["metrics"]
        next_state = best_data["state"]

        print("agent:", best_agent)
        print("metrics:", {k: round(v, 3) for k, v in metrics.items()})

        binary = to_binary_state(metrics)
        current_tuple = state_to_tuple(binary)

        print("binary_state:", binary)
        print("cube_position:", current_tuple)

        allowed = True
        if prev_tuple is not None:
            allowed = transition_allowed(prev_tuple, current_tuple)
            print("transition_allowed:", allowed)

            if allowed:
                allowed_moves += 1
            else:
                blocked_moves += 1
                print("BLOCKED: non-local transition detected")

        transition_memory = derive_transition_memory(
            blocked_moves=blocked_moves,
            allowed_moves=allowed_moves,
        )

        print("transition_memory:", transition_memory)

        decision = adaptive_bindu(
            metrics,
            force_reject=not allowed,
            transition_memory=transition_memory,
        )

        print("bindu:", decision)

        if decision["decision"] in ("COMMIT", "SOFT_COMMIT"):
            state = next_state
            print(decision["decision"])
        else:
            print("REJECT")

        prev_tuple = current_tuple
        print()

    total_checked = allowed_moves + blocked_moves
    stability_score = round((allowed_moves / total_checked), 3) if total_checked else 1.0

    print("=== FINAL STATE ===")
    print(state.to_dict())

    print("\n=== TRANSITION SUMMARY ===")
    print(
        {
            "allowed_moves": allowed_moves,
            "blocked_moves": blocked_moves,
            "stability_score": stability_score,
        }
    )

    print("\n=== DONE ===")


if __name__ == "__main__":
    run(steps=12)
