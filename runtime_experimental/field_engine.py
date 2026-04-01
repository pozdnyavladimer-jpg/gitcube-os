# runtime_experimental/field_engine.py

from typing import Dict, Any


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


class FieldEngine:
    """
    Runtime field model.

    Environment changes preference, not state meaning.
    This follows ENVIRONMENT_CANON.md:

    - balanced: near-neutral
    - harsh: stability first
    - exploratory: movement / vitality first

    Also includes:
    - day / night phase
    - richness
    - calm / crisis pressure
    """

    def __init__(self, environment: str = "balanced", cycle: int = 40):
        self.environment = environment
        self.cycle = max(2, int(cycle))

    def get_phase(self, step: int) -> str:
        half = self.cycle // 2
        return "DAY" if (step % self.cycle) < half else "NIGHT"

    def get_richness(self, step: int, vitality: float = 1.0) -> float:
        phase = self.get_phase(step)

        if self.environment == "harsh":
            base = 0.40 if phase == "DAY" else 0.28
        elif self.environment == "exploratory":
            base = 0.72 if phase == "DAY" else 0.58
        else:
            base = 0.60 if phase == "DAY" else 0.42

        # low vitality makes the field feel poorer
        vitality_drag = (1.0 - _clamp(vitality, 0.0, 1.0)) * 0.08
        richness = base - vitality_drag
        return round(_clamp(richness, 0.15, 0.95), 3)

    def get_pressure(
        self,
        state: Dict[str, float],
        blocked_moves: int = 0,
        reject_streak: int = 0,
    ) -> float:
        pressure_axis = float(state.get("pressure", 0.0))
        structure = float(state.get("structure", 0.0))
        law = float(state.get("law", 0.0))

        blocked_term = _clamp(blocked_moves / 12.0, 0.0, 1.0) * 0.18
        reject_term = _clamp(reject_streak / 6.0, 0.0, 1.0) * 0.22

        # structure and law can absorb some pressure
        damping = ((structure + law) / 2.0) * 0.14

        pressure = pressure_axis + blocked_term + reject_term - damping
        return round(_clamp(pressure, 0.0, 1.0), 3)

    def get_mode(
        self,
        vitality: float,
        pressure: float,
        stability_score: float,
    ) -> str:
        vitality = _clamp(vitality, 0.0, 1.0)
        pressure = _clamp(pressure, 0.0, 1.0)
        stability_score = _clamp(stability_score, 0.0, 1.0)

        if vitality < 0.28 or pressure > 0.72 or stability_score < 0.45:
            return "crisis"

        if vitality > 0.72 and pressure < 0.32 and stability_score > 0.70:
            return "calm"

        return "active"

    def get_metric_weights(
        self,
        vitality: float,
        pressure: float,
        stability_score: float,
    ) -> Dict[str, float]:
        """
        Weights for canonical metrics.
        Environment changes preference, not meaning.
        """
        mode = self.get_mode(vitality, pressure, stability_score)

        if self.environment == "harsh":
            weights = {
                "shadow": 1.25,
                "coherence": 1.20,
                "target_fit": 0.90,
                "vitality": 0.85,
            }
        elif self.environment == "exploratory":
            weights = {
                "shadow": 0.95,
                "coherence": 1.00,
                "target_fit": 1.00,
                "vitality": 1.25,
            }
        else:
            weights = {
                "shadow": 1.05,
                "coherence": 1.05,
                "target_fit": 1.00,
                "vitality": 1.00,
            }

        # mode-based overrides
        if mode == "crisis":
            weights["shadow"] += 0.20
            weights["coherence"] += 0.18
            weights["vitality"] -= 0.08

        elif mode == "calm":
            weights["target_fit"] += 0.10
            weights["vitality"] += 0.12

        return {k: round(v, 3) for k, v in weights.items()}

    def describe(
        self,
        *,
        step: int,
        state: Dict[str, float],
        vitality: float,
        blocked_moves: int = 0,
        reject_streak: int = 0,
        stability_score: float = 1.0,
    ) -> Dict[str, Any]:
        phase = self.get_phase(step)
        richness = self.get_richness(step, vitality=vitality)
        pressure = self.get_pressure(
            state=state,
            blocked_moves=blocked_moves,
            reject_streak=reject_streak,
        )
        mode = self.get_mode(
            vitality=vitality,
            pressure=pressure,
            stability_score=stability_score,
        )
        weights = self.get_metric_weights(
            vitality=vitality,
            pressure=pressure,
            stability_score=stability_score,
        )

        return {
            "environment": self.environment,
            "phase": phase,
            "richness": richness,
            "pressure": pressure,
            "mode": mode,
            "weights": weights,
          }
