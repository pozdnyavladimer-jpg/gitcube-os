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

    state = default_state()

    prev_tuple = None

    for step in range(3):

        best_agent, results = choose_best_agent(state)
        metrics = results[best_agent]["metrics"]

        binary_state = to_binary_state(metrics)
        current_tuple = state_to_tuple(binary_state)
        decision = binary_decision(binary_state)


        if prev_tuple is not None:
            allowed = transition_allowed(prev_tuple, current_tuple)
            if not allowed:


        prev_tuple = current_tuple



if __name__ == "__main__":
    demo()
