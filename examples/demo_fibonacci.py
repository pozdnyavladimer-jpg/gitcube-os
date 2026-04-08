from core.state import default_state
from runtime.agent_loop import choose_best_agent
from runtime.fibonacci_scaling import compare_scaling


def best_agent(scores):
    return max(scores, key=scores.get)


def demo():

    state = default_state()
    best, results = choose_best_agent(state)

    raw_scores = {agent: data["score"] for agent, data in results.items()}
    comparison = compare_scaling(raw_scores)





if __name__ == "__main__":
    demo()
