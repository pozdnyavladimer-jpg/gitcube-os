from core.state import default_state
from runtime.agent_loop import choose_best_agent
from runtime.adaptive_bindu import adaptive_bindu
from runtime.binary_cube import (
    to_binary_state,
    state_to_tuple,
    transition_allowed,
)


def run(steps: int = 12):
    state = default_state()
    prev_tuple = None

    allowed_moves = 0
    blocked_moves = 0

    print("\n=== GITCUBE OS LOOP (WITH BINARY CONSTRAINT) ===\n")

    for step in range(steps):
        print(f"--- step {step} ---")

        # 1. choose best agent
        best_agent, results = choose_best_agent(state)
        best_data = results[best_agent]
        metrics = best_data["metrics"]
        next_state = best_data["state"]

        print("agent:", best_agent)
        print("metrics:", {k: round(v, 3) for k, v in metrics.items()})

        # 2. convert to binary cube state
        binary = to_binary_state(metrics)
        current_tuple = state_to_tuple(binary)

        print("binary_state:", binary)
        print("cube_position:", current_tuple)

        # 3. transition check
        allowed = True
        if prev_tuple is not None:
            allowed = transition_allowed(prev_tuple, current_tuple)
            print("transition_allowed:", allowed)

            if allowed:
                allowed_moves += 1
            else:
                blocked_moves += 1
                print("BLOCKED: non-local transition detected")

        # 4. bindu decision
        decision = adaptive_bindu(
            metrics,
            force_reject=not allowed,
        )

        print("bindu:", decision)

        # 5. apply state only if allowed by decision
        if decision["decision"] in ("COMMIT", "SOFT_COMMIT"):
            state = next_state
            print(decision["decision"])
        else:
            print("REJECT")

        # 6. update previous cube state
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
