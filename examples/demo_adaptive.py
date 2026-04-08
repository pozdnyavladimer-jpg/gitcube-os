from core.state import default_state
from runtime.agent_loop import choose_best_agent
from runtime.memory import EpisodeMemory

from core.topological_filter import TopologicalFilter
from runtime.memory_control import derive_memory_control
from runtime.agent_learning import derive_agent_bias
from runtime.adaptive_bindu import adaptive_bindu_decision


def sequence_from_candidate(agent_name, metrics):
    tokens = [agent_name.upper()]
    tokens.append("ALIGN" if metrics.get("coherence", 0) > 0.8 else "DRIFT")
    tokens.append("CLEAR" if metrics.get("shadow", 0) < 0.1 else "SHADOW")
    tokens.append("LIVE" if metrics.get("vitality", 0) > 0.3 else "WEAK")
    tokens.append("TARGET" if metrics.get("target_fit", 0) > 0.45 else "MISS")
    return tokens


def demo():

    state = default_state()
    memory = EpisodeMemory()

    # Seed memory to simulate prior runtime history
    memory.add(
        step=0,
        agent="planner",
        metrics={"shadow": 0.10, "coherence": 0.93, "target_fit": 0.44, "vitality": 0.31},
        state=state.to_dict(),
        status="soft",
    )
    memory.add(
        step=1,
        agent="planner",
        metrics={"shadow": 0.08, "coherence": 0.89, "target_fit": 0.46, "vitality": 0.29},
        state=state.to_dict(),
        status="soft",
    )
    memory.add(
        step=2,
        agent="stabilizer",
        metrics={"shadow": 0.04, "coherence": 0.91, "target_fit": 0.52, "vitality": 0.33},
        state=state.to_dict(),
        status="accepted",
    )

    memory_summary = memory.summary()

    memory_control = derive_memory_control(memory_summary)
    agent_bias = derive_agent_bias(memory_summary)


    best, results = choose_best_agent(state)

    raw_scores = {agent: round(data["score"], 3) for agent, data in results.items()}

    # Apply simple bias manually for demo visibility
    adjusted_scores = {}
    for agent, data in results.items():
        adjusted_scores[agent] = round(data["score"] * (1 + agent_bias.get(agent, 0.0)), 3)

    selected_agent = max(adjusted_scores, key=adjusted_scores.get)
    selected_data = results[selected_agent]
    metrics = selected_data["metrics"]


    topo = TopologicalFilter()
    topo_sequence = sequence_from_candidate(selected_agent, metrics)
    topo_result = topo.process(topo_sequence)


    decision = adaptive_bindu_decision(metrics, topo_result, memory_control)




if __name__ == "__main__":
    demo()
