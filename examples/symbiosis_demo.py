from core.neuromodulator import NeuroState
from runtime.symbiosis_controller import SymbiosisParams, apply_symbiosis, get_mode


def demo():
    neuro = NeuroState(
        adrenaline=0.7,
        dopamine=0.5,
        cortisol=0.2,
        serotonin=0.8,
    )

    base = SymbiosisParams(
        pressure=0.4,
        flow=0.5,
        structure=0.5,
        balance=0.5,
        law=0.4,
        future=0.5,
    )

    result = apply_symbiosis(neuro, base)
    mode = get_mode(result)



if __name__ == "__main__":
    demo()
