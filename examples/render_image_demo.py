from core.neuromodulator import NeuroState
from core.projector import state_to_visual_spec
from runtime.render_adapter import build_render_request
from runtime.sd_client import generate_image


def demo():
    final_state = {
        "pressure": 0.4,
        "flow": 0.5,
        "structure": 0.5,
        "balance": 0.5,
        "law": 0.4,
        "future": 0.5,
    }

    neuro = NeuroState(
        adrenaline=0.7,
        dopamine=0.5,
        cortisol=0.2,
        serotonin=0.8,
    )

    spec = state_to_visual_spec(
        final_state=final_state,
        neuro=neuro,
        symbiosis_mode="stability",
    )

    req = build_render_request(spec, mode="image")
    generate_image(req, output_path="generated.png")


if __name__ == "__main__":
    demo()
