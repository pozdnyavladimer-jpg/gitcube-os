from typing import Dict, Any

from runtime.class_layer import (
    summarize_class_votes,
    recommend_profession,
    suggest_party_companions,
)


def build_party_profile(results: Dict[str, Any]) -> Dict[str, Any]:
    summary = summarize_class_votes(results)
    dominant_class = summary["dominant_class"]

    party_mode = {
        "TANK": "survival",
        "ARCHER": "targeting",
        "MAGE": "evolution",
        "HEALER": "repair",
        "ASSASSIN": "surgical",
    }.get(dominant_class, "balanced")

    company_role = recommend_profession(dominant_class)
    companions = suggest_party_companions(dominant_class)

    return {
        "dominant_class": dominant_class,
        "party_mode": party_mode,
        "company_role": company_role,
        "recommended_companions": companions,
        "votes": summary["votes"],
        "score_sum": summary["score_sum"],
    }
