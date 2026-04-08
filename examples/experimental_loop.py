# examples/experimental_loop.py

from collections import Counter
from typing import Dict, Any, List

from core.state import default_state
from runtime_experimental.field_engine import FieldEngine
from runtime_experimental.agent_loop import choose_best_agent
from runtime_experimental.vitality_engine import update_vitality

# optional bridge (Lab → CORE)
try:
    from runtime_experimental.lab_bridge import build_lab_field_patch
except ImportError:
    build_lab_field_patch = None


# =========================
# DECISION LOGIC
# =========================
def decide(metrics: Dict[str, float], role_tx: Dict[str, Any]) -> str:
    override = role_tx.get("decision_override")
    if override:
        return str(override)

    shadow = float(metrics.get("shadow", 0.0))
    coherence = float(metrics.get("coherence", 0.0))
    target_fit = float(metrics.get("target_fit", 0.0))
    vitality = float(metrics.get("vitality", 0.0))

    score = coherence + target_fit + vitality - shadow

    if shadow <= 0.10 and coherence >= 0.88 and score >= 1.45:
        return "COMMIT"

    if shadow <= 0.16 and coherence >= 0.78:
        return "SOFT_COMMIT"

    return "REJECT"


# =========================
# FIELD MERGE
# =========================
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


# =========================
# EMERGENCY BRAKE
# =========================
def apply_emergency_brake(field: Dict[str, Any], vitality: float) -> Dict[str, Any]:
    """
    Якщо система "падає" — прибираємо тиск
    """
    if vitality < 0.20:
        field = dict(field)
        field["pressure"] = 0.0
        field["mode"] = "RECOVERY"
        field["weights"] = {
            **field.get("weights", {}),
            "balance": 0.5,
            "flow": 0.2,
        }
    return field


# =========================
# MAIN LOOP
# =========================
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

        f"{'step':<4} {'agent':<10} {'class':<10} {'decision':<12} "
        f"{'v':<6} {'mode':<10} {'score':<8}"
    )

    for step in range(steps):

        # ---- BASE FIELD ----
        field = field_engine.build_field(
            step=step,
            vitality=vitality,
            class_history=class_history,
        )

        # ---- LAB PATCH ----
        if use_lab_patch and build_lab_field_patch:
            try:
                patch = build_lab_field_patch(
                    step=step,
                    vitality=vitality,
                    history=class_history,
                )
                field = merge_field(field, patch)
            except Exception:
                pass

        # ---- EMERGENCY BRAKE ----
        field = apply_emergency_brake(field, vitality)

        # ---- AGENTS ----
        _, agent_results = choose_best_agent(
            state,
            vitality=vitality,
            field=field,
            class_history=class_history,
        )

        winner_agent = max(
            agent_results,
            key=lambda name: agent_results[name]["experiment_score"],
        )
        winner = agent_results[winner_agent]

        dominant_class = str(winner["dominant_class"])
        metrics = dict(winner["metrics"])
        role_tx = dict(winner.get("role_transaction", {}))
        score = float(winner.get("experiment_score", 0.0))

        # ---- DECISION ----
        decision = decide(metrics, role_tx)

        # ---- UPDATE VITALITY ----
        vitality = update_vitality(
            class_name=dominant_class,
            decision=decision,
            vitality=vitality,
            field=field,
            role_tx=role_tx,
        )

        # ---- STATE UPDATE ----
        if decision in ("COMMIT", "SOFT_COMMIT"):
            state = winner["state"]

        class_history.append(dominant_class)

        # ---- LOG ----
        row = {
            "step": step,
            "agent": winner_agent,
            "class": dominant_class,
            "decision": decision,
            "vitality": round(vitality, 3),
            "mode": field.get("mode"),
            "metrics": metrics,
            "score": round(score, 6),
        }
        logs.append(row)

        # ---- PRINT ----
        if step % 5 == 0:
                f"{step:<4} {winner_agent:<10} {dominant_class:<10} "
                f"{decision:<12} {round(vitality,3):<6} "
                f"{str(field.get('mode','FLOW')):<10} {round(score,3):<8}"
            )


    return logs


# =========================
# SUMMARY
# =========================
def print_summary(logs: List[Dict[str, Any]]) -> None:
    class_counts = Counter([x["class"] for x in logs])
    decision_counts = Counter([x["decision"] for x in logs])
    agent_counts = Counter([x["agent"] for x in logs])


    if logs:


# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    logs = run_experiment(
        steps=100,
        start_vitality=0.42,
        use_lab_patch=True,
    )
    print_summary(logs)
