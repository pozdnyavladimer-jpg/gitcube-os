from dataclasses import dataclass
from typing import Dict, List


@dataclass
class VEyeProfile:
    name: str
    role: str
    focus_octave: int
    shadow_tolerance: float
    coherence_weight: float
    anomaly_tolerance: float
    trajectory_bias: float
    healing_bias: float
    kill_bias: float

    def resonance_score(self, shadow, coherence, anomaly, trajectory):
        shadow_penalty = max(0.0, shadow - self.shadow_tolerance)
        anomaly_penalty = max(0.0, anomaly - self.anomaly_tolerance)

        return (
            coherence * self.coherence_weight
            - shadow_penalty * 1.2
            - anomaly_penalty
            + trajectory * self.trajectory_bias * 0.3
            + self.healing_bias * max(0.0, 0.7 - shadow) * 0.1
            + self.kill_bias * max(0.0, anomaly - 0.2) * 0.2
        )

    def decide(self, content, shadow, coherence, anomaly, trajectory):
        if shadow > self.shadow_tolerance + 0.25:
            return {
                "eye": self.name,
                "role": self.role,
                "decision": "REJECT",
                "resonance": -1.0,
            }

        score = self.resonance_score(shadow, coherence, anomaly, trajectory)

        if score >= 0.75:
            decision = "COMMIT"
        elif score >= 0.35:
            decision = "SOFT_COMMIT"
        else:
            decision = "REJECT"

        return {
            "eye": self.name,
            "role": self.role,
            "decision": decision,
            "resonance": round(score, 4),
        }


V_EYES: Dict[str, VEyeProfile] = {
    "TANK": VEyeProfile("TANK", "Tank", 1, 0.9, 0.35, 0.75, 0.1, 0.2, 0.05),
    "ARCHER": VEyeProfile("ARCHER", "Archer", 3, 0.55, 0.7, 0.45, 1.0, 0.1, 0.15),
    "HEALER": VEyeProfile("HEALER", "Healer", 4, 0.65, 0.9, 0.55, 0.15, 1.0, 0.05),
    "MAGE": VEyeProfile("MAGE", "Mage", 6, 0.25, 1.0, 0.25, 0.35, 0.05, 0.25),
    "ASSASSIN": VEyeProfile("ASSASSIN", "Assassin", 7, 0.15, 0.55, 0.15, 0.3, 0.0, 1.0),
}


def evaluate_party(content, shadow, coherence, anomaly, trajectory):
    results: List[dict] = []

    for eye in V_EYES.values():
        results.append(
            eye.decide(content, shadow, coherence, anomaly, trajectory)
        )

    results.sort(key=lambda x: x["resonance"], reverse=True)
    return results
