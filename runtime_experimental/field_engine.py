class FieldEngine:
    def build_field(self, step: int, vitality: float, class_history=None):
        return {
            "phase": "DAY" if step % 2 == 0 else "NIGHT",
            "mode": "active" if vitality > 0.3 else "recovery",
            "weights": {
                "coherence": 1.0,
                "shadow": 1.0,
                "target_fit": 1.0
            }
        }
