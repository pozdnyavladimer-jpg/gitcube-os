from core.state import default_state
from runtime.agent_loop import choose_best_agent
from runtime.memory import EpisodeMemory

from core.topological_filter import TopologicalFilter
from runtime.memory_control import derive_memory_control
from runtime.agent_learning import derive_agent_bias
from runtime.adaptive_bindu import adaptive_bindu_decision


def run_step(state, memory, label):
    best, results = choose_best_agent(state)

    memory_summary = memory.summary() if memory else None
    memory_control = derive_memory_control(memory_summary) if memory else {
        "coherence_bonus": 0.0,
        "shadow_tolerance_penalty": 0.0,
        "caution_bias": 0.0
    }

    agent_bias = derive_agent_bias(memory_summary) if memory else {}

    adjusted_scores = {}
    for agent, data in results.items():
        adjusted_scores[agent] = data["score"] * (1 + agent_bias.get(agent, 0.0))

    selected_agent = max(adjusted_scores, key=adjusted_scores.get)
    metrics = results[selected_agent]["metrics"]

    topo = TopologicalFilter()
    topo_sequence = [selected_agent.upper()]
    topo_result = topo.process(topo_sequence)

    decision = adaptive_bindu_decision(metrics, topo_result, memory_control)

    print(f"\n[{label}]")
    print("agent:", selected_agent)
    print("metrics:", {k: round(v, 3) for k, v in metrics.items()})
    print("decision:", decision["decision"])
    print("reason:", decision["reason"])

    if memory:
        memory.add(
            step=0,
            agent=selected_agent,
            metrics=metrics,
            state=state.to_dict(),
            status=decision["decision"]
        )


def demo():
    print("=== COMPARISON DEMO ===")

    state = default_state()

    print("\n--- WITHOUT MEMORY ---")
    for i in range(3):
        run_step(state, None, f"no-memory step {i}")

    print("\n--- WITH MEMORY ---")
    memory = EpisodeMemory()

    for i in range(3):
        run_step(state, memory, f"memory step {i}")


if __name__ == "__main__":
    demo()
