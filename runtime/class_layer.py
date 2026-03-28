from typing import Dict, Any, Tuple, List


CLASS_CONFIG = {
    "TANK": {
        "description": "stability / pressure holding / operations",
        "weights": {
            "coherence": 0.55,
            "shadow": -0.60,
            "target_fit": 0.15,
            "vitality": 0.10,
        },
    },
    "ARCHER": {
        "description": "precision / targeting / routing",
        "weights": {
            "coherence": 0.20,
            "shadow": -0.15,
            "target_fit": 0.65,
            "vitality": 0.20,
        },
    },
    "MAGE": {
        "description": "pattern synthesis / evolution / architecture",
        "weights": {
            "coherence": 0.30,
            "shadow": -0.20,
            "target_fit": 0.30,
            "vitality": 0.60,
        },
    },
    "HEALER": {
        "description": "repair / coherence / support",
        "weights": {
            "coherence": 0.70,
            "shadow": -0.45,
            "target_fit": 0.10,
            "vitality": 0.15,
        },
    },
    "ASSASSIN": {
        "description": "anomaly cutting / surgical pruning / audit",
        "weights": {
            "coherence": 0.15,
            "shadow": -0.40,
            "target_fit": 0.50,
            "vitality": 0.20,
        },
    },
}


def _base_class_score(metrics: Dict[str, float], weights: Dict[str, float]) -> float:
    return (
        metrics.get("coherence", 0.0) * weights["coherence"]
        + metrics.get("shadow", 0.0) * weights["shadow"]
        + metrics.get("target_fit", 0.0) * weights["target_fit"]
        + metrics.get("vitality", 0.0) * weights["vitality"]
    )


def _tuple_novelty_bonus(
    candidate_tuple: Tuple[int, ...],
    state_visits: Dict[Tuple[int, ...], int],
    temperature: float,
) -> float:
    visits = state_visits.get(candidate_tuple, 0)
    rarity = 1.0 / (1.0 + visits)
    return rarity * 0.06 * max(0.7, float(temperature))


def _repeat_penalty(
    candidate_tuple: Tuple[int, ...],
    prev_tuple: Tuple[int, ...] | None,
) -> float:
    if prev_tuple is None:
        return 0.0
    return 0.12 if candidate_tuple == prev_tuple else 0.0


def _role_shape_bonus(
    class_name: str,
    metrics: Dict[str, float],
) -> float:
    coherence = metrics.get("coherence", 0.0)
    shadow = metrics.get("shadow", 0.0)
    target_fit = metrics.get("target_fit", 0.0)
    vitality = metrics.get("vitality", 0.0)

    if class_name == "TANK":
        return 0.10 if shadow <= 0.14 and coherence >= 0.80 else 0.0

    if class_name == "ARCHER":
        return 0.10 if target_fit >= 0.40 else 0.0

    if class_name == "MAGE":
        return 0.10 if vitality >= 0.30 and coherence >= 0.70 else 0.0

    if class_name == "HEALER":
        return 0.10 if coherence >= 0.85 else 0.0

    if class_name == "ASSASSIN":
        return 0.10 if shadow <= 0.20 and target_fit >= 0.35 else 0.0

    return 0.0


def score_classes_for_candidate(
    metrics: Dict[str, float],
    candidate_tuple: Tuple[int, ...],
    state_visits: Dict[Tuple[int, ...], int],
    prev_tuple: Tuple[int, ...] | None,
    temperature: float,
) -> Dict[str, Dict[str, float]]:
    scored: Dict[str, Dict[str, float]] = {}

    for class_name, config in CLASS_CONFIG.items():
        weights = config["weights"]

        base = _base_class_score(metrics, weights)
        novelty = _tuple_novelty_bonus(candidate_tuple, state_visits, temperature)
        repeat_penalty = _repeat_penalty(candidate_tuple, prev_tuple)
        shape_bonus = _role_shape_bonus(class_name, metrics)

        final = base + novelty + shape_bonus - repeat_penalty

        scored[class_name] = {
            "base_score": round(base, 6),
            "novelty_bonus": round(novelty, 6),
            "shape_bonus": round(shape_bonus, 6),
            "repeat_penalty": round(repeat_penalty, 6),
            "final_score": round(final, 6),
        }

    return scored


def choose_dominant_class(class_scores: Dict[str, Dict[str, float]]) -> Tuple[str, Dict[str, float]]:
    winner = max(class_scores.items(), key=lambda kv: kv[1]["final_score"])
    return winner[0], winner[1]


def annotate_results_with_classes(
    results: Dict[str, Any],
    state_visits: Dict[Tuple[int, ...], int],
    prev_tuple: Tuple[int, ...] | None,
    temperature: float,
) -> Dict[str, Any]:
    annotated: Dict[str, Any] = {}

    for agent_name, agent_data in results.items():
        metrics = dict(agent_data["metrics"])
        candidate_tuple = agent_data["candidate_tuple"]

        class_scores = score_classes_for_candidate(
            metrics=metrics,
            candidate_tuple=candidate_tuple,
            state_visits=state_visits,
            prev_tuple=prev_tuple,
            temperature=temperature,
        )

        dominant_class, dominant_payload = choose_dominant_class(class_scores)

        annotated[agent_name] = {
            **agent_data,
            "class_scores": class_scores,
            "dominant_class": dominant_class,
            "dominant_class_score": round(dominant_payload["final_score"], 6),
            "class_description": CLASS_CONFIG[dominant_class]["description"],
        }

    return annotated


def summarize_class_votes(results: Dict[str, Any]) -> Dict[str, Any]:
    vote_count = {name: 0 for name in CLASS_CONFIG.keys()}
    accum_score = {name: 0.0 for name in CLASS_CONFIG.keys()}

    for _, data in results.items():
        cls = data["dominant_class"]
        vote_count[cls] += 1
        accum_score[cls] += data["dominant_class_score"]

    dominant_class = max(vote_count.items(), key=lambda kv: (kv[1], accum_score[kv[0]]))[0]

    return {
        "dominant_class": dominant_class,
        "votes": vote_count,
        "score_sum": {k: round(v, 6) for k, v in accum_score.items()},
    }


def recommend_profession(dominant_class: str) -> str:
    mapping = {
        "TANK": "operations_manager",
        "ARCHER": "product_manager",
        "MAGE": "architect",
        "HEALER": "people_partner",
        "ASSASSIN": "auditor",
    }
    return mapping.get(dominant_class, "generalist")


def suggest_party_companions(dominant_class: str) -> List[str]:
    mapping = {
        "TANK": ["HEALER", "ARCHER"],
        "ARCHER": ["TANK", "MAGE"],
        "MAGE": ["ARCHER", "HEALER"],
        "HEALER": ["TANK", "MAGE"],
        "ASSASSIN": ["ARCHER", "TANK"],
    }
    return mapping.get(dominant_class, ["TANK", "MAGE"])
