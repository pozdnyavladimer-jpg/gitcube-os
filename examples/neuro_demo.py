from core.neuromodulator import NeuroModulator, NeuroState, RuntimeConfig


def demo():
    neuro = NeuroModulator(
        NeuroState(
            adrenaline=0.5,
            dopamine=0.4,
            cortisol=0.3,
            serotonin=0.6,
        )
    )

    base = RuntimeConfig(
        exploration_rate=1.0,
        memory_gain=1.0,
        penalty_weight=1.0,
        stability_bias=1.0,
    )


    applied = neuro.apply(base)

    neuro.update_from_signal(
        steps_to_commit=5,
        reroute_count=2,
        shadow_pressure=0.35,
        coherence=0.78,
    )


    applied2 = neuro.apply(base)


if __name__ == "__main__":
    demo()
