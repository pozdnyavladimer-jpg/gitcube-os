# runtime_experimental/vitality_engine.py

from typing import Dict


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def base_decision_cost(decision: str) -> float:
    if decision == "COMMIT":
        return 0.045
    if decision == "SOFT_COMMIT":
        return 0.022
    if decision == "FORCE_ESCAPE":
        return 0.030
    if decision == "TUNNEL_COMMIT":
        return 0.060
    return 0.010


def class_cost_multiplier(class_name: str) -> float:
    return {
        "TANK": 0.82,
        "ARCHER": 1.00,
        "MAGE": 1.18,
        "HEALER": 0.88,
        "ASSASSIN": 1.65,
    }.get(class_name, 1.0)


def class_reward(class_name: str, decision: str) -> float:
    reward = 0.0

    if class_name == "HEALER" and decision in ("COMMIT", "SOFT_COMMIT"):
        reward += 0.07
    elif class_name == "MAGE" and decision == "COMMIT":
        reward += 0.035
    elif class_name == "TANK" and decision in ("COMMIT", "SOFT_COMMIT"):
        reward += 0.018
    elif class_name == "ARCHER" and decision == "COMMIT":
        reward += 0.015

    return reward


def higgs_cost(
    state_dict: Dict[str, float],
    class_name: str = "",
    cluster_size: int = 1,
) -> float:
    """
    Structural maintenance tax.
    Higher structure/law means more cost to remain coherent.
    """
    structure = float(state_dict.get("structure", 0.0))
    law = float(state_dict.get("law", 0.0))
    balance = float(state_dict.get("balance", 0.0))

    mass = ((structure * 0.5) + (law * 0.3) + (balance * 0.2))
    base = mass * 0.018

    if class_name == "TANK":
        base *= 1.10
    elif class_name == "MAGE":
        base *= 0.95
    elif class_name == "HEALER":
        base *= 0.92

    if cluster_size > 1:
        base *= (1.0 + min(0.5, (cluster_size - 1) * 0.08))

    return round(_clamp(base, 0.0, 0.06), 3)


def update_vitality(
    *,
    vitality: float,
    class_name: str,
    decision: str,
    field: Dict[str, float],
    state_dict: Dict[str, float],
    extra_delta: float = 0.0,
    cluster_size: int = 1,
) -> Dict[str, float]:
    """
    Full vitality update:
    - decision cost
    - class multiplier
    - class reward
    - field richness bonus
    - higgs structural tax
    - extra external delta
    """
    vitality = float(vitality)
    richness = float(field.get("richness", 0.5))

    cost = base_decision_cost(decision) * class_cost_multiplier(class_name)
    reward = class_reward(class_name, decision)
    field_bonus = richness * 0.020
    h_cost = higgs_cost(state_dict, class_name=class_name, cluster_size=cluster_size)

    new_vitality = vitality - cost + reward + field_bonus - h_cost + float(extra_delta)
    new_vitality = _clamp(new_vitality, 0.05, 1.0)

    return {
        "vitality": round(new_vitality, 3),
        "decision_cost": round(cost, 3),
        "class_reward": round(reward, 3),
        "field_bonus": round(field_bonus, 3),
        "higgs_cost": round(h_cost, 3),
        "extra_delta": round(float(extra_delta), 3),
    }
