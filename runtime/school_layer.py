from typing import Dict, List, Any
from collections import Counter


CLASS_TO_ROLE = {
    "TANK": "operations_guard",
    "ARCHER": "product_manager",
    "MAGE": "architect",
    "HEALER": "people_partner",
    "ASSASSIN": "auditor",
}


CLASS_TO_MODE = {
    "TANK": "stability",
    "ARCHER": "targeting",
    "MAGE": "evolution",
    "HEALER": "repair",
    "ASSASSIN": "surgical",
}


CLASS_COMPANIONS = {
    "TANK": ["HEALER", "ARCHER"],
    "ARCHER": ["TANK", "MAGE"],
    "MAGE": ["ARCHER", "HEALER"],
    "HEALER": ["TANK", "MAGE"],
    "ASSASSIN": ["TANK", "ARCHER"],
}


def class_fatigue_penalty(class_name: str, history: List[str], window: int = 10) -> float:
    recent = history[-window:]
    count = recent.count(class_name)
    return round(count * 0.05, 3)


def infer_school_stage(
    stability_score: float,
    blocked_moves: int,
    reject_streak: int,
    dominant_class: str,
    class_history: List[str],
) -> str:
    recent = class_history[-8:]
    diversity = len(set(recent)) if recent else 0

    if stability_score < 0.45 or blocked_moves > 10:
        return "survival"

    if reject_streak >= 4:
        return "recovery"

    if dominant_class in ("TANK", "HEALER") and diversity <= 2:
        return "stabilization"

    if dominant_class in ("ARCHER", "MAGE") and diversity >= 2:
        return "navigation"

    if dominant_class in ("MAGE", "ASSASSIN") and diversity >= 3:
        return "synthesis"

    return "balanced"


def build_school_profile(
    class_votes: Dict[str, int],
    class_score_sum: Dict[str, float],
    class_history: List[str],
    allowed_moves: int,
    blocked_moves: int,
    stability_score: float,
    reject_streak: int,
) -> Dict[str, Any]:
    dominant_class = max(class_votes, key=lambda k: (class_votes[k], class_score_sum.get(k, 0.0)))

    role = CLASS_TO_ROLE.get(dominant_class, "generalist")
    party_mode = CLASS_TO_MODE.get(dominant_class, "balanced")
    companions = CLASS_COMPANIONS.get(dominant_class, [])

    stage = infer_school_stage(
        stability_score=stability_score,
        blocked_moves=blocked_moves,
        reject_streak=reject_streak,
        dominant_class=dominant_class,
        class_history=class_history,
    )

    total_votes = sum(class_votes.values()) or 1
    distribution = {
        k: round(v / total_votes, 3) for k, v in class_votes.items()
    }

    recent = class_history[-12:]
    history_counter = Counter(recent)

    return {
        "dominant_class": dominant_class,
        "party_mode": party_mode,
        "company_role": role,
        "recommended_companions": companions,
        "school_stage": stage,
        "votes": class_votes,
        "score_sum": {k: round(v, 6) for k, v in class_score_sum.items()},
        "distribution": distribution,
        "recent_class_pressure": dict(history_counter),
        "class_history_tail": recent,
        "system_fit": {
            "allowed_moves": allowed_moves,
            "blocked_moves": blocked_moves,
            "stability_score": round(stability_score, 3),
            "reject_streak": reject_streak,
        },
    }
