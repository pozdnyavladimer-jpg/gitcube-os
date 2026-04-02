def build_lab_field_patch(step: int, vitality: float, history=None):
    return {
        "weights": {
            "coherence": 1.0,
            "shadow": 1.0,
            "target_fit": 1.0
        },
        "phase": "DAY" if step % 2 == 0 else "NIGHT",
        "mode": "active" if vitality > 0.3 else "recovery"
    }
