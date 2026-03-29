import random

def get_market_state(step: int):
    is_day = (step % 40) < 20
    tone = (step % 13) + 1

    base_richness = 0.75 if is_day else 0.40
    tone_bonus = (tone / 13.0) * 0.15

    richness = max(0.15, min(1.0, base_richness + tone_bonus - 0.05))

    return {
        "richness": round(richness, 3),
        "is_day": is_day,
        "tone": tone,
    }


def energy_cost(cls, decision, is_day, iris_mask, masks):
    base = {
        "COMMIT": 0.045,
        "SOFT_COMMIT": 0.025,
        "REJECT": 0.010,
    }[decision]

    if cls == "ASSASSIN":
        base *= 2.2
    elif cls == "MAGE":
        base *= 1.2 if is_day else 1.45
    elif cls == "ARCHER":
        base *= 1.0 if is_day else 1.2
    elif cls == "HEALER":
        base *= 0.85
    elif cls == "TANK":
        base *= 0.8 if not is_day else 0.95

    base *= masks[iris_mask]["energy_mult"][cls]
    return base


def market_reward(cls, decision, richness, is_day):
    if decision == "REJECT":
        return 0.0

    reward = 0.005 + 0.015 * richness

    if is_day and cls in ("MAGE", "ARCHER"):
        reward += 0.015 * richness

    if not is_day and cls in ("TANK", "HEALER"):
        reward += 0.018 * (1.0 - abs(0.45 - richness))

    if cls == "ASSASSIN":
        reward += 0.01 if richness < 0.35 else -0.01

    return max(0.0, reward)


def recovery_gain(cls, decision, iris_mask, masks):
    rec = 0.0

    if cls == "HEALER" and decision != "REJECT":
        rec = 0.03
    elif cls == "TANK" and decision == "SOFT_COMMIT":
        rec = 0.01
    elif cls == "MAGE" and decision == "REJECT":
        rec = 0.005

    rec *= masks[iris_mask]["recovery_mult"][cls]
    return rec


def stability_delta(cls, decision, iris_mask, is_day, vitality, reject_streak, masks):
    risk_mult = masks[iris_mask]["risk_mult"]

    if decision == "REJECT":
        base = -0.05 * risk_mult
    elif cls == "TANK":
        base = 0.03 / risk_mult
    elif cls == "HEALER":
        base = 0.028 / risk_mult
    elif cls == "MAGE":
        base = 0.018 / risk_mult
    elif cls == "ARCHER":
        base = 0.017 / risk_mult
    elif cls == "ASSASSIN":
        base = -0.01 * risk_mult
    else:
        base = 0.0

    if vitality < 0.2:
        base -= 0.03
    if cls == "ASSASSIN" and decision == "COMMIT":
        base -= 0.02
    if reject_streak >= 3:
        base -= 0.04

    return base
