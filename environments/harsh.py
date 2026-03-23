from environments.base import EnvironmentProfile


HARSH = EnvironmentProfile(
    name="harsh",
    shadow_weight=1.4,
    coherence_weight=1.2,
    target_fit_weight=0.9,
    vitality_weight=0.8,
)
