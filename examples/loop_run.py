from core.state import default_state
from runtime.agent_loop import choose_best_agent
from runtime.memory import EpisodeMemory

from core.neuromodulator import NeuroModulator, NeuroState, RuntimeConfig
from runtime.symbiosis_controller import SymbiosisParams, apply_symbiosis, get_mode
from core.projector import state_to_visual_spec
from core.topological_filter import TopologicalFilter
from runtime.adaptive_bindu import adaptive_bindu_decision


def apply_neuro_bias(results, neuro_state, symbiosis_params):
    adjusted = {}

    for agent, data in results.items():
        score = data["score"]

        if agent == "explorer":
            score *= (1 + neuro_state.adrenaline * 0.8)

        elif agent == "stabilizer":
            score *= (1 + neuro_state.serotonin * 0.8)

        elif agent == "planner":
            score *= (1 + neuro_state.dopamine * 0.8)

        score *= (1 - neuro_state.cortisol * 0.4)

        adjusted[agent] = (score, data)

    best_agent = max(adjusted, key=lambda x: adjusted[x][0])
    return best_agent, adjusted[best_agent][1]


def sequence_from_candidate(agent_name, metrics):
    tokens = [agent_name.upper()]
    tokens.append("ALIGN" if metrics.get("coherence", 0) > 0.8 else "DRIFT")
    tokens.append("CLEAR" if metrics.get("shadow", 0) < 0.1 else "SHADOW")
    tokens.append("LIVE" if metrics.get("vitality", 0) > 0.3 else "WEAK")
    tokens.append("TARGET" if metrics.get("target_fit", 0) > 0.45 else "MISS")
    return tokens


def run_episode(steps=5):
    state = default_state()
    memory = EpisodeMemory()

    neuro = NeuroModulator(
        NeuroState(
            adrenaline=0.5,
            dopamine=0.5,
            cortisol=0.4,
            serotonin=0.6,
        )
    )

    runtime_cfg = RuntimeConfig(
        exploration_rate=1.0,
        memory_gain=1.0,
        penalty_weight=1.0,
        stability_bias=1.0,
    )

    symbiosis_base = SymbiosisParams(
        pressure=0.4,
        flow=0.5,
        structure=0.5,
        balance=0.5,
        law=0.4,
        future=0.5,
    )

    last_mode = "mixed"

    print("=== START EPISODE ===")

    for step in range(steps):
        print(f"\n--- step {step} ---")

        modulated = neuro.apply(runtime_cfg)
        symbiosis = apply_symbiosis(neuro.state, symbiosis_base)
        mode = get_mode(symbiosis)
        last_mode = mode

        best, results = choose_best_agent(state)
        best, best_data = apply_neuro_bias(results, neuro.state, symbiosis)

        metrics = best_data["metrics"]

        topo = TopologicalFilter()
        seq = sequence_from_candidate(best, metrics)
        topo_result = topo.process(seq)

        print("topo:", topo_result)

        bindu = adaptive_bindu_decision(metrics, topo_result)
        print("bindu:", bindu)

        if bindu["decision"] == "COMMIT":
            memory.add(
                step=step,
                agent=best,
                metrics=metrics,
                state=best_data["state"].to_dict(),
                status="accepted",
            )
            state = best_data["state"]
            print("COMMIT")

        elif bindu["decision"] == "SOFT_COMMIT":
            memory.add(
                step=step,
                agent=best,
                metrics=metrics,
                state=best_data["state"].to_dict(),
                status="soft",
            )
            state = best_data["state"]
            print("SOFT COMMIT")

        else:
            print("REJECT")

        neuro.update_from_signal(
            steps_to_commit=step,
            reroute_count=1 if bindu["decision"] == "REJECT" else 0,
            shadow_pressure=metrics.get("shadow", 0),
            coherence=metrics.get("coherence", 0),
        )

    print("\n=== FINAL STATE ===")
    final_state = state.to_dict()
    print(final_state)

    print("\n=== MEMORY SUMMARY ===")
    print(memory.summary())

    print("\n=== VISUAL STATE ===")
    visual = state_to_visual_spec(
        final_state=final_state,
        neuro=neuro.state,
        symbiosis_mode=last_mode,
    )
    print("mood:", visual.mood)
    print("palette:", visual.palette)
    print("composition:", visual.composition)
    print("texture:", visual.texture)
    print("intensity:", visual.intensity)
    print("prompt:", visual.prompt)


if __name__ == "__main__":
    run_episode(steps=5)
