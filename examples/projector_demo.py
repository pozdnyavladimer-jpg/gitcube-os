from core.neuromodulator import NeuroState
from core.projector import state_to_visual_spec


def demo():
    final_state = {
        "pressure": 0.03,
        "flow": 0.18,
        "structure": 0.23,
        "balance": 0.28,
        "law": 0.13,
        "future": 0.14,
    }

    neuro = NeuroState(
        adrenaline=0.4,
        dopamine=0.9,
        cortisol=0.15,
        serotonin=1.0,
    )

    spec = state_to_visual_spec(
        final_state=final_state,
        neuro=neuro,
        symbiosis_mode="stability",
    )

    print("=== PROJECTOR DEMO ===")
    print("mood:", spec.mood)
    print("palette:", spec.palette)
    print("composition:", spec.composition)
    print("texture:", spec.texture)
    print("intensity:", spec.intensity)
    print("prompt:", spec.prompt)


if __name__ == "__main__":
    demo()
