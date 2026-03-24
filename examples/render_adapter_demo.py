from core.neuromodulator import NeuroState
from core.projector import state_to_visual_spec
from runtime.render_adapter import build_render_request, render_request_to_dict


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

    req = build_render_request(spec, mode="image")

    print("=== RENDER ADAPTER DEMO ===")
    print(render_request_to_dict(req))


if __name__ == "__main__":
    demo()
