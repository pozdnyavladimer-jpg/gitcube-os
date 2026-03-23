from dataclasses import dataclass


@dataclass
class EnvironmentProfile:
    name: str
    shadow_weight: float = 1.0
    coherence_weight: float = 1.0
    target_fit_weight: float = 1.0
    vitality_weight: float = 1.0
