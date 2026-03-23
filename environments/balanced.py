from environments.base import EnvironmentProfile


BALANCED = EnvironmentProfile(
    name="balanced",
    shadow_weight=1.0,
    coherence_weight=1.0,
    target_fit_weight=1.0,
    vitality_weight=1.0,
)
