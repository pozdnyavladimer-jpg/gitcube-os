from core.state import default_state
from runtime.agent_loop import choose_best_agent
from runtime.binary_cube import (
    to_binary_state,
    state_to_tuple,
    binary_decision,
    transition_allowed,
    describe_state,
)


def demo():
    print("=== GITCUBE OS BINARY CUBE DEMO ===")
    print("Idea: represent system state as a 3D binary cube")
    print("Each axis = constraint")
    print("State transitions must be local (cube-like)")
    print("")

    state = default_state()

    prev_tuple = None

    for step in range(3):
        print(f"--- step {step} ---")

        best_agent, results = choose_best_agent(state)
        metrics = results[best_agent]["metrics"]

        binary_state = to_binary_state(metrics)
        current_tuple = state_to_tuple(binary_state)
        decision = binary_decision(binary_state)

        print("agent:", best_agent)
        print("metrics:", {k: round(v, 3) for k, v in metrics.items()})
        print("binary_state:", describe_state(binary_state))
        print("cube_position:", current_tuple)

        if prev_tuple is not None:
            allowed = transition_allowed(prev_tuple, current_tuple)
            print("transition_allowed:", allowed)
            if not allowed:
                print("WARNING: jump in state space (non-local move)")

        print("decision:", decision)
        print("")

        prev_tuple = current_tuple

    print("=== INTERPRETATION ===")
    print("The system is not just scoring outputs.")
    print("It navigates a discrete state space (cube).")
    print("Valid behavior = local transitions between states.")
    print("This introduces structure and prevents chaotic jumps.")


if __name__ == "__main__":
    demo()
