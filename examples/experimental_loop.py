# examples/experimental_loop.py

from collections import Counter
from typing import Dict, Any, List

from core.state import default_state
from runtime_experimental.field_engine import FieldEngine
from runtime_experimental.agent_loop import choose_best_agent
from runtime_experimental.vitality_engine import update_vitality
from runtime_experimental.lab_bridge import build_lab_field_patch


def decide(metrics: Dict[str, float], role_tx: Dict[str, Any]) -> str:
    """
    Minimal experimental gate.
    role_transaction may override the base decision.
    """
    override = role_tx.get("decision_override")
    if override:
        return str(override)

    shadow = float(metrics.get("shadow", 0.0))
    coherence = float(metrics.get("coherence", 0.0))
    target_fit = float(metrics.get("target_fit", 0.0))
    vitality = float(metrics.get("vitality", 0.0))

    commit_score = coherence + target_fit + vitality - shadow

    if shadow <= 0.10 and coherence >= 0.88 and commit_score >= 1.45:
        return "COMMIT"

    if shadow <= 0.16 and coherence >= 0.78:
        return "SOFT_COMMIT"

    return "REJECT"


def merge_field(base_field: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base_field)

    out["weights"] = {
        **base_field.get("weights", {}),
        **patch.get("weights", {}),
    }

    for k, v in patch.items():
        if k == "weights":
            continue
        out[k] = v

    return out


def run_experiment(
    steps: int = 100,
    start_vitality: float = 0.42,
    use_lab_patch: bool = True,
) -> List[Dict[str, Any]]:
    state = default_state()
    vitality = float(start_vitality)

    field_engine = FieldEngine()
    class_history: List[str] = []
    logs: List[Dict[str, Any]] = []

    print(
        f"{'step':<4} {'agent':<10} {'class':<10} {'decision':<12} "
        f"{'v':<6} {'phase':<6} {'mode':<8} {'score':<8}"
    )
    print("-" * 82)

    for step in range(steps):
        field = field_engine.build_field(step=step, vitality=vitality, class_history=class_history)

        if use_lab_patch:
            patch = build_lab_field_patch(
                step=step,
                vitality=vitality,
                history=class_history,
            )
            field = merge_field(field, patch)

        _, agent_results = choose_best_agent(
            state,
            vitality=vitality,
            field=field,
            class_history=class_history,
        )

        winner_agent = max(
            agent_results,
            key=lambda name: agent_results[name]["experimental_score"],
        )
        winner = agent_results[winner_agent]

        dominant_class = str(winner["dominant_class"])
        metrics = dict(winner["metrics"])
        role_tx = dict(winner.get("role_transaction", {}))
        score = float(winner.get("experimental_score", 0.0))

        decision = decide(metrics, role_tx)

        vitality = update_vitality(
            class_name=dominant_class,
            decision=decision,
            vitality=vitality,
            field=field,
            role_tx=role_tx,
        )

        if decision in ("COMMIT", "SOFT_COMMIT"):
            state = winner["state"]

        class_history.append(dominant_class)

        row = {
            "step": step,
            "winner_agent": winner_agent,
            "dominant_class": dominant_class,
            "decision": decision,
            "vitality": round(vitality, 3),
            "field_phase": field.get("phase"),
            "field_mode": field.get("mode"),
            "field": field,
            "metrics": metrics,
            "role_transaction": role_tx,
            "score": round(score, 6),
            "score_parts": winner.get("experimental_score_parts", {}),
            "state": state.to_dict(),
        }
        logs.append(row)

        if step % 5 == 0:
            print(
                f"{step:<4} {winner_agent:<10} {dominant_class:<10} {decision:<12} "
                f"{round(vitality, 3):<6} {str(field.get('phase', 'DAY')):<6} "
                f"{str(field.get('mode', 'active')):<8} {round(score, 3):<8}"
            )

    print("-" * 82)
    print("done")

    return logs


def print_summary(logs: List[Dict[str, Any]]) -> None:
    class_counts = Counter([x["dominant_class"] for x in logs])
    decision_counts = Counter([x["decision"] for x in logs])
    agent_counts = Counter([x["winner_agent"] for x in logs])

    print("Class counts:", dict(class_counts))
    print("Decision counts:", dict(decision_counts))
    print("Agent winner counts:", dict(agent_counts))

    if logs:
        print("Final vitality:", logs[-1]["vitality"])
        print("Final field mode:", logs[-1]["field_mode"])
        print("Final phase:", logs[-1]["field_phase"])


if __name__ == "__main__":
    logs = run_experiment(
        steps=100,
        start_vitality=0.42,
        use_lab_patch=True,
    )
    print_summary(logs)
