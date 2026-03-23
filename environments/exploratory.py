from environments.base import EnvironmentProfile


EXPLORATORY = EnvironmentProfile(
    name="exploratory",
    shadow_weight=0.9,
    coherence_weight=0.9,
    target_fit_weight=1.0,
    vitality_weight=1.3,
)
