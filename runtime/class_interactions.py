from collections import Counter


def interaction_effects(class_name, history):
    if not history:
        return 0.0

    last = history[-10:]
    counts = Counter(last)
    effect = 0.0

    if class_name == "ASSASSIN":
        effect -= counts["TANK"] * 0.02

    if class_name == "HEALER":
        effect += counts["ASSASSIN"] * 0.015

    if class_name == "MAGE":
        effect += counts["ARCHER"] * 0.01

    if class_name == "MAGE" and counts["MAGE"] > 5:
        effect -= 0.03

    if class_name == "ASSASSIN" and counts["MAGE"] > 3:
        effect += 0.02

    return round(effect, 3)
