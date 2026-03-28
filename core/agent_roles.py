from dataclasses import dataclass


@dataclass
class AgentScore:
    name: str
    base_score: float
    mode_bias: float
    repeat_penalty: float
    curiosity_bonus: float
    adjusted_score: float


def score_planner(metrics, memory, candidate, visit_heat):
    base = (
        0.9 * metrics["coherence"]
        + 0.5 * metrics["target_fit"]
        + 0.2 * metrics["vitality"]
        - 0.4 * metrics["shadow"]
    )
    repeat_penalty = 0.12 if visit_heat.get(candidate, 0) > 3 else 0.0
    curiosity_bonus = 0.0
    adjusted = base - repeat_penalty + curiosity_bonus
    return AgentScore("planner", base, 0.0, repeat_penalty, curiosity_bonus, adjusted)


def score_critic(metrics, memory, candidate, visit_heat):
    instability = metrics["shadow"] + memory.get("blocked_ratio", 0.0)
    base = 1.8 - instability
    repeat_penalty = 0.12 if visit_heat.get(candidate, 0) > 3 else 0.0
    curiosity_bonus = 0.0
    adjusted = base - repeat_penalty + curiosity_bonus
    return AgentScore("critic", base, 0.0, repeat_penalty, curiosity_bonus, adjusted)


def score_explorer(metrics, memory, candidate, visit_heat):
    rare = visit_heat.get(candidate, 0) == 0
    base = (
        0.6 * metrics["target_fit"]
        + 0.4 * metrics["vitality"]
        + 0.2 * (1.0 - metrics["shadow"])
    )
    repeat_penalty = 0.0 if rare else 0.08
    curiosity_bonus = 0.35 if rare else 0.12
    adjusted = base - repeat_penalty + curiosity_bonus
    return AgentScore("explorer", base, 0.0, repeat_penalty, curiosity_bonus, adjusted)


def score_stabilizer(metrics, memory, candidate, visit_heat):
    base = (
        1.0 * metrics["coherence"]
        + 0.3 * (1.0 - metrics["shadow"])
        + 0.2 * (1.0 - memory.get("caution_bias", 0.0))
    )
    repeat_penalty = 0.06 if visit_heat.get(candidate, 0) > 5 else 0.0
    curiosity_bonus = 0.0
    adjusted = base - repeat_penalty + curiosity_bonus
    return AgentScore("stabilizer", base, 0.0, repeat_penalty, curiosity_bonus, adjusted)
