from core.state import default_state
from runtime.agent_loop import choose_best_agent
from runtime.fibonacci_scaling import compare_scaling


def best_agent(scores):
    return max(scores, key=scores.get)


def demo():
    print("=== GITCUBE OS FIBONACCI DEMO ===")
    print("Goal: compare linear ranking vs fibonacci ranking")
    print("Interpretation: fibonacci is used here as a non-linear search bias")
    print("")

    state = default_state()
    best, results = choose_best_agent(state)

    raw_scores = {agent: data["score"] for agent, data in results.items()}
    comparison = compare_scaling(raw_scores)

    print("--- RAW SCORES ---")
    print(comparison["raw"])
    print("raw_best:", best_agent(comparison["raw"]))
    print("")

    print("--- LINEAR SCALING ---")
    print(comparison["linear"])
    print("linear_best:", best_agent(comparison["linear"]))
    print("")

    print("--- FIBONACCI SCALING ---")
    print(comparison["fibonacci"])
    print("fibonacci_best:", best_agent(comparison["fibonacci"]))
    print("")

    print("=== INTERPRETATION ===")
    print("Linear scaling gives a gentle preference to higher-ranked agents.")
    print("Fibonacci scaling gives a stronger non-linear preference to top-ranked agents.")
    print("This can be useful when we want faster convergence and less exploration noise.")
    print("")
    print("Important:")
    print("Fibonacci here is not physics.")
    print("It is a search and filtering heuristic.")

if __name__ == "__main__":
    demo()
