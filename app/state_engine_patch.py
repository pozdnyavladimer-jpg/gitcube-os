from runtime.market_engine import get_market_state, market_energy_update
from runtime.ecology import class_ecology_penalty
from runtime.class_interactions import interaction_effects


def apply_market(engine, dominant_class, decision_name):
    if not hasattr(engine.state, "vitality"):
        engine.state.vitality = 1.0

    market = get_market_state(engine.step_count)

    vitality = market_energy_update(
        dominant_class,
        decision_name,
        engine.state.vitality,
    )

    ecology_penalty = class_ecology_penalty(
        dominant_class,
        engine.class_history,
    )

    interaction = interaction_effects(
        dominant_class,
        engine.class_history,
    )

    vitality = vitality - ecology_penalty + interaction
    vitality = max(0.05, min(1.0, vitality))

    engine.state.vitality = vitality

    return {
        "vitality": round(engine.state.vitality, 3),
        "market": market,
        "ecology_penalty": round(ecology_penalty, 3),
        "interaction": round(interaction, 3),
    }
