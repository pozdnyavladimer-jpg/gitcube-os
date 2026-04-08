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


    for step in range(steps):

        best_agent, results = choose_best_agent(state)
        best_data = results[best_agent]
        metrics = best_data["metrics"]
        next_state = best_data["state"]


        binary = to_binary_state(metrics)
        current_tuple = state_to_tuple(binary)


        allowed = True
        if prev_tuple is not None:
            allowed = transition_allowed(prev_tuple, current_tuple)

            if allowed:
                allowed_moves += 1
            else:
                blocked_moves += 1

        transition_memory = derive_transition_memory(
            blocked_moves=blocked_moves,
            allowed_moves=allowed_moves,
        )


        decision = adaptive_bindu(
            metrics,
            force_reject=not allowed,
            transition_memory=transition_memory,
        )


        if decision["decision"] in ("COMMIT", "SOFT_COMMIT"):
            state = next_state
        else:

        prev_tuple = current_tuple

    total_checked = allowed_moves + blocked_moves
    stability_score = round((allowed_moves / total_checked), 3) if total_checked else 1.0


        {
            "allowed_moves": allowed_moves,
            "blocked_moves": blocked_moves,
            "stability_score": stability_score,
        }
    )



if __name__ == "__main__":
    run(steps=12)
