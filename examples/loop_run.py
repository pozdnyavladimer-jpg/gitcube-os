from core.state import default_state
from runtime.agent_loop import choose_best_agent
from runtime.memory import EpisodeMemory
from runtime.bindu import bindu_decision

from core.neuromodulator import NeuroModulator, NeuroState, RuntimeConfig


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

    print("=== START EPISODE ===")

    for step in range(steps):
        print(f"\n--- step {step} ---")

        best, results = choose_best_agent(state)
        best_data = results[best]
        metrics = best_data["metrics"]

        bindu = bindu_decision(metrics)

        print(f"selected: {best}")
        print(f"metrics: {metrics}")
        print(f"bindu: {bindu}")

        # --- APPLY NEURO ---
        modulated = neuro.apply(runtime_cfg)
        print(f"neuro_state: {neuro.state}")
        print(f"modulated_config: {modulated}")

        # --- DECISION ---
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

        # --- UPDATE NEURO ---
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
    print(state.to_dict())

    print("\n=== MEMORY SUMMARY ===")
    print(memory.summary())


if __name__ == "__main__":
    run_episode(steps=5)
