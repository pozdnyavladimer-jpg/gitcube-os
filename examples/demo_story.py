from runtime.memory import EpisodeMemory
from runtime.memory_control import derive_memory_control
from runtime.agent_learning import derive_agent_bias
from runtime.adaptive_bindu import adaptive_bindu_decision
from core.topological_filter import TopologicalFilter


def sequence_from_candidate(agent_name, metrics):
    tokens = [agent_name.upper()]
    tokens.append("ALIGN" if metrics.get("coherence", 0) > 0.8 else "DRIFT")
    tokens.append("CLEAR" if metrics.get("shadow", 0) < 0.1 else "SHADOW")
    tokens.append("LIVE" if metrics.get("vitality", 0) > 0.3 else "WEAK")
    tokens.append("TARGET" if metrics.get("target_fit", 0) > 0.45 else "MISS")
    return tokens


def run_case(step, agent, metrics, memory):
    topo = TopologicalFilter()
    seq = sequence_from_candidate(agent, metrics)
    topo_result = topo.process(seq)

    memory_summary = memory.summary()
    memory_control = derive_memory_control(memory_summary)
    agent_bias = derive_agent_bias(memory_summary)

    decision = adaptive_bindu_decision(metrics, topo_result, memory_control)

    print(f"\n--- step {step} ---")
    print("agent:", agent)
    print("metrics:", {k: round(v, 3) for k, v in metrics.items()})
    print("topo_sequence:", seq)
    print("topo_flags:", topo_result.get("flags", []))
    print("memory_control:", memory_control)
    print("agent_bias:", agent_bias)
    print("decision:", decision["decision"])
    print("reason:", decision["reason"])
    print("thresholds:", decision["thresholds"])

    if decision["decision"] == "COMMIT":
        status = "accepted"
    elif decision["decision"] == "SOFT_COMMIT":
        status = "soft"
    else:
        status = None

    if status is not None:
        memory.add(
            step=step,
            agent=agent,
            metrics=metrics,
            state={"demo": True, "step": step},
            status=status,
        )

    return decision


def demo():
    print("=== GITCUBE OS STORY DEMO ===")
    print("Scenario: unstable -> partial -> stable")
    print("Goal: show how constraints + memory shape decisions")

    memory = EpisodeMemory()

    # Step 1: unstable candidate
    run_case(
        step=1,
        agent="planner",
        metrics={
            "shadow": 0.14,
            "coherence": 0.79,
            "target_fit": 0.42,
            "vitality": 0.31,
        },
        memory=memory,
    )

    # Step 2: partial improvement
    run_case(
        step=2,
        agent="stabilizer",
        metrics={
            "shadow": 0.09,
            "coherence": 0.88,
            "target_fit": 0.46,
            "vitality": 0.34,
        },
        memory=memory,
    )

    # Step 3: stable candidate
    run_case(
        step=3,
        agent="stabilizer",
        metrics={
            "shadow": 0.05,
            "coherence": 0.94,
            "target_fit": 0.53,
            "vitality": 0.36,
        },
        memory=memory,
    )

    print("\n=== FINAL MEMORY SUMMARY ===")
    print(memory.summary())

    print("\n=== INTERPRETATION ===")
    print("Step 1 should tend toward REJECT or SOFT_COMMIT.")
    print("Step 2 should tend toward SOFT_COMMIT.")
    print("Step 3 should tend toward COMMIT if thresholds allow.")
    print("This demonstrates state selection through constraints, not output scoring.")


if __name__ == "__main__":
    demo()
