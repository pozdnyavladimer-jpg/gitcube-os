from dataclasses import dataclass


@dataclass
class NeuroState:
    adrenaline: float = 0.5   # exploration / speed
    dopamine: float = 0.5     # reward / memory gain
    cortisol: float = 0.5     # penalty / shadow sensitivity
    serotonin: float = 0.5    # stability / coherence bias


@dataclass
class RuntimeConfig:
    exploration_rate: float = 1.0
    memory_gain: float = 1.0
    penalty_weight: float = 1.0
    stability_bias: float = 1.0


class NeuroModulator:
    def __init__(self, state: NeuroState | None = None):
        self.state = state or NeuroState()

    def apply(self, config: RuntimeConfig) -> RuntimeConfig:
        return RuntimeConfig(
            exploration_rate=config.exploration_rate * (1.0 + self.state.adrenaline),
            memory_gain=config.memory_gain * (1.0 + self.state.dopamine),
            penalty_weight=config.penalty_weight * (1.0 + self.state.cortisol),
            stability_bias=config.stability_bias * (1.0 + self.state.serotonin),
        )

    def update_from_signal(
        self,
        steps_to_commit: int,
        reroute_count: int,
        shadow_pressure: float,
        coherence: float,
    ) -> None:
        """
        Minimal adaptive rule:
        - slow commit / many reroutes -> more adrenaline
        - high shadow -> more cortisol
        - high coherence -> more serotonin
        - successful stable regime -> more dopamine
        """

        if steps_to_commit > 3 or reroute_count > 1:
            self.state.adrenaline = min(1.0, self.state.adrenaline + 0.1)
        else:
            self.state.adrenaline = max(0.0, self.state.adrenaline - 0.05)

        if shadow_pressure > 0.3:
            self.state.cortisol = min(1.0, self.state.cortisol + 0.1)
        else:
            self.state.cortisol = max(0.0, self.state.cortisol - 0.05)

        if coherence > 0.8:
            self.state.serotonin = min(1.0, self.state.serotonin + 0.08)
            self.state.dopamine = min(1.0, self.state.dopamine + 0.08)
        else:
            self.state.serotonin = max(0.0, self.state.serotonin - 0.04)
            self.state.dopamine = max(0.0, self.state.dopamine - 0.02)
