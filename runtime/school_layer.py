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


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def class_fatigue_penalty(class_name: str, history: List[str], window: int = 12) -> float:
    """
    Плавна втома класу.
    ASSASSIN втомлюється значно швидше, бо це рідкісний інструмент.
    """
    if not class_name:
        return 0.0

    recent = history[-window:]
    count = recent.count(class_name)

    if count <= 1:
        return 0.0

    base_multiplier = {
        "TANK": 0.04,
        "ARCHER": 0.05,
        "MAGE": 0.06,
        "HEALER": 0.05,
        "ASSASSIN": 0.16,
    }.get(class_name, 0.05)

    penalty = (count - 1) * base_multiplier
    return round(_clamp(penalty, 0.0, 0.75), 3)


def class_dominance_penalty(class_name: str, history: List[str], window: int = 10) -> float:
    """
    Додатковий штраф, якщо один клас займає надто велику частку історії.
    Особливо важливо для ASSASSIN.
    """
    if not class_name:
        return 0.0

    recent = history[-window:]
    if not recent:
        return 0.0

    ratio = recent.count(class_name) / max(1, len(recent))

    if ratio < 0.5:
        return 0.0

    multiplier = {
        "TANK": 0.10,
        "ARCHER": 0.10,
        "MAGE": 0.12,
        "HEALER": 0.10,
        "ASSASSIN": 0.25,
    }.get(class_name, 0.1)

    penalty = (ratio - 0.5) * multiplier * 4.0
    return round(_clamp(penalty, 0.0, 0.65), 3)


def environment_pressure_bonus(
    class_name: str,
    stability_score: float,
    blocked_moves: int,
    reject_streak: int,
    allowed_moves: int,
) -> float:
    """
    Плавна атмосфера:
    - TANK потрібен при нестабільності
    - HEALER потрібен при reject / recovery
    - MAGE і ARCHER ростуть у спокої
    - ASSASSIN вмикається тільки при справжній кризі
    """

    bonus = 0.0

    instability = _clamp(1.0 - stability_score, 0.0, 1.0)
    blocked_pressure = _clamp(blocked_moves / 8.0, 0.0, 1.0)
    reject_pressure = _clamp(reject_streak / 5.0, 0.0, 1.0)
    system_maturity = _clamp(allowed_moves / 20.0, 0.0, 1.0)
    calmness = _clamp(stability_score - 0.55, 0.0, 0.45)

    if class_name == "TANK":
        bonus += instability * 0.34
        bonus += blocked_pressure * 0.12

    elif class_name == "HEALER":
        bonus += reject_pressure * 0.38
        bonus += instability * 0.10

    elif class_name == "MAGE":
        bonus += calmness * 0.35
        bonus += system_maturity * 0.08

    elif class_name == "ARCHER":
        bonus += calmness * 0.22
        bonus += system_maturity * 0.10

    elif class_name == "ASSASSIN":
        crisis = max(blocked_pressure, reject_pressure)

        # Якщо кризи немає — ассасин небажаний
        if crisis < 0.25:
            bonus -= 0.28
        else:
            bonus += crisis * 0.18

        # У спокійному середовищі шкодить
        bonus -= calmness * 0.14
        bonus -= system_maturity * 0.06

    return round(_clamp(bonus, -0.45, 0.45), 3)


def counter_class_bonus(class_name: str, history: List[str], window: int = 10) -> float:
    """
    Контр-реакція на перекіс історії.
    Якщо домінує ASSASSIN -> трохи підсилюємо TANK / HEALER.
    Якщо домінує TANK -> трохи підсилюємо MAGE / ARCHER.
    Якщо домінує MAGE -> трохи ARCHER.
    """
    recent = history[-window:]
    if not recent:
        return 0.0

    counts = Counter(recent)
    dominant, dom_count = counts.most_common(1)[0]
    ratio = dom_count / max(1, len(recent))

    if ratio < 0.6:
        return 0.0

    bonus = 0.0

    if dominant == "ASSASSIN":
        if class_name == "TANK":
            bonus += 0.16
        elif class_name == "HEALER":
            bonus += 0.18

    elif dominant == "TANK":
        if class_name == "MAGE":
            bonus += 0.12
        elif class_name == "ARCHER":
            bonus += 0.08

    elif dominant == "MAGE":
        if class_name == "ARCHER":
            bonus += 0.12
        elif class_name == "HEALER":
            bonus += 0.06

    elif dominant == "HEALER":
        if class_name == "ARCHER":
            bonus += 0.10
        elif class_name == "MAGE":
            bonus += 0.10

    return round(_clamp(bonus, 0.0, 0.22), 3)


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

    if reject_streak >= 3:
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
    dominant_class = max(
        class_votes,
        key=lambda k: (class_votes[k], class_score_sum.get(k, 0.0))
    )

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
