from core.state import default_state
from runtime.agent_loop import choose_best_agent
from runtime.memory import EpisodeMemory
from runtime.bindu import bindu_decision

from core.neuromodulator import NeuroModulator, NeuroState, RuntimeConfig
from runtime.symbiosis_controller import SymbiosisParams, apply_symbiosis, get_mode
from core.projector import state_to_visual_spec


def apply_neuro_bias(results, neuro_state, symbiosis_params):
    """
    Neuro + symbiosis influence on agent selection.
    """
    adjusted = {}

    for agent, data in results.items():
        score = data["score"]

        if agent == "explorer":
            score *= (1 + neuro_state.adrenaline * 0.8)
            score *= (1 + symbiosis_params.future * 0.3)

        elif agent == "stabilizer":
            score *= (1 + neuro_state.serotonin * 0.8)
            score *= (1 + symbiosis_params.balance * 0.3)

        elif agent == "planner":
            score *= (1 + neuro_state.dopamine * 0.8)
            score *= (1 + symbiosis_params.structure * 0.2)

        # global caution
        score *= (1 - neuro_state.cortisol * 0.4)

        adjusted[agent] = (score, data)

    best_agent = max(adjusted, key=lambda x: adjusted[x][0])
    best_data = adjusted[best_agent][1]

    return best_agent, best_data


def run_episode(steps=5):
    state = default_state()
    memory = EpisodeMemory()

    # --- NEURO INIT ---
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

    # --- SYMBIOSIS BASE ---
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
        bindu = bindu_decision(metrics)

        print(f"selected (driven): {best}")
        print(f"metrics: {metrics}")
        print(f"bindu: {bindu}")
        print(f"neuro_state: {neuro.state}")
        print(f"modulated_config: {modulated}")
        print(f"symbiosis_params: {symbiosis}")
        print(f"symbiosis_mode: {mode}")

        if bindu["decision"] == "COMMIT":
            memory.add(
                step=step,
                agent=best,
                metrics=metrics,
                state=best_data["state"].to_dict(),
                status="accepted",
            )
            state = best_data["state"]

        elif bindu["decision"] == "SOFT_COMMIT":
            memory.add(
                step=step,
                agent=best,
                metrics=metrics,
                state=best_data["state"].to_dict(),
                status="soft",
            )
            state = best_data["state"]

        else:
            print("REJECTED -> state not updated")

        shadow = metrics.get("shadow", 0.0)
        coherence = metrics.get("coherence", 0.0)

        reroute_count = 1 if bindu["decision"] == "REJECT" else 0

        neuro.update_from_signal(
            steps_to_commit=step,
            reroute_count=reroute_count,
            shadow_pressure=shadow,
            coherence=coherence,
        )

        print(f"updated_neuro: {neuro.state}")

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
