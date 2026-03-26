from itertools import combinations
from runtime.v_eye_profile import V_EYES


PAIR_PRODUCTS = {
    ("MAGE", "TANK"): "materialized_design",
    ("ARCHER", "MAGE"): "predictive_design",
    ("HEALER", "MAGE"): "harmonic_structure",
    ("ASSASSIN", "MAGE"): "verified_creation",
    ("TANK", "HEALER"): "stable_repair",
    ("ASSASSIN", "TANK"): "secured_boundary",
}


def evaluate_pair(a, b, content, shadow, coherence, anomaly, trajectory):
    r1 = V_EYES[a].decide(content, shadow, coherence, anomaly, trajectory)
    r2 = V_EYES[b].decide(content, shadow, coherence, anomaly, trajectory)

    score = (r1["resonance"] + r2["resonance"]) / 2

    key = tuple(sorted((a, b)))
    product = PAIR_PRODUCTS.get(key, "fusion")

    if score > 0.8:
        decision = "COMMIT"
    elif score > 0.4:
        decision = "SOFT_COMMIT"
    else:
        decision = "REJECT"

    return {
        "pair": f"{a}+{b}",
        "score": round(score, 4),
        "decision": decision,
        "product": product,
    }


def evaluate_all_pairs(content, shadow, coherence, anomaly, trajectory):
    results = []

    for a, b in combinations(V_EYES.keys(), 2):
        results.append(
            evaluate_pair(a, b, content, shadow, coherence, anomaly, trajectory)
        )

    results.sort(key=lambda x: x["score"], reverse=True)
    return results
