from typing import Dict
from environments.base import EnvironmentProfile


def apply_environment_to_score(metrics: Dict[str, float], env: EnvironmentProfile) -> float:
    shadow = metrics.get("shadow", 1.0)
    coherence = metrics.get("coherence", 0.0)
    target_fit = metrics.get("target_fit", 0.0)
    vitality = metrics.get("vitality", 0.0)

    score = (
        coherence * 0.4 * env.coherence_weight
        - shadow * 0.3 * env.shadow_weight
        + target_fit * 0.2 * env.target_fit_weight
        + vitality * 0.1 * env.vitality_weight
    )
    return round(score, 3)
