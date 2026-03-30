def get_market_state(step: int):
    is_day = (step % 40) < 20
    richness = 0.65 if is_day else 0.40
    return {
        "is_day": is_day,
        "richness": richness,
    }


def market_energy_update(cls, decision, vitality):
    if decision == "COMMIT":
        cost = 0.04
    elif decision == "SOFT_COMMIT":
        cost = 0.02
    elif decision == "FORCE_ESCAPE":
        cost = 0.03
    else:
        cost = 0.01

    if cls == "MAGE":
        cost *= 1.25
    elif cls == "ASSASSIN":
        cost *= 1.90
    elif cls == "ARCHER":
        cost *= 1.10
    elif cls == "TANK":
        cost *= 0.80
    elif cls == "HEALER":
        cost *= 0.85

    reward = 0.01

    if cls == "HEALER":
        reward += 0.03
    elif cls == "ARCHER":
        reward += 0.01
    elif cls == "TANK":
        reward += 0.02
    elif cls == "MAGE":
        reward += 0.015

    new_vitality = vitality - cost + reward
    return max(0.05, min(1.0, new_vitality))
