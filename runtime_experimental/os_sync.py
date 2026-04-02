import os
from typing import Dict, Any

from v_bridge import VBridge
from core.state import default_state
from runtime_experimental.field_engine import FieldEngine
from runtime_experimental.agent_loop import choose_best_agent
from runtime_experimental.vitality_engine import update_vitality
from runtime_experimental.lab_bridge import build_lab_field_patch


BUS_PATH = os.environ.get("V_RESONANCE_PATH", "v_resonance.json")


def merge_field(base_field: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base_field)
    out["weights"] = {
        **base_field.get("weights", {}),
        **patch.get("weights", {}),
    }

    for key, value in patch.items():
        if key == "weights":
            continue
        out[key] = value

    return out


def decide(metrics: Dict[str, float], role_tx: Dict[str, Any]) -> str:
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


def build_signal_payload(
    *,
    field: Dict[str, Any],
    winner_agent: str,
    dominant_class: str,
    decision: str,
    vitality: float,
) -> Dict[str, Any]:
    target = "ACTOR"

    if decision == "COMMIT":
        action = "BUILD"
    elif decision == "SOFT_COMMIT":
        action = "STABILIZE"
    else:
        action = "WAIT"

    return {
        "source": "CORE",
        "target": target,
        "action": action,
        "decision": decision,
        "winner_agent": winner_agent,
        "dominant_class": dominant_class,
        "phase": field.get("phase", "DAY"),
        "mode": field.get("mode", "active"),
        "bond": "NONE",
        "reason": f"{dominant_class}_{decision}".lower(),
        "vitality": round(float(vitality), 3),
    }


def main() -> None:
    bridge = VBridge(BUS_PATH)
    bus = bridge.read_state()

    meta = bus.get("meta", {})

    state = default_state()
    vitality = float(meta.get("vitality", 0.42))
    step = int(meta.get("step", 0))
    class_history = []

    field_engine = FieldEngine()
    field = field_engine.build_field(
        step=step,
        vitality=vitality,
        class_history=class_history,
    )

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

    decision = decide(metrics, role_tx)

    vitality = update_vitality(
        class_name=dominant_class,
        decision=decision,
        vitality=vitality,
        field=field,
        state=state.to_dict(),
        role_tx=role_tx,
    )

    if decision in ("COMMIT", "SOFT_COMMIT"):
        state = winner["state"]

    flower_patch = {
        "pressure": round(float(state.pressure), 3),
        "flow": round(float(state.flow), 3),
        "structure": round(float(state.structure), 3),
        "balance": round(float(state.balance), 3),
        "law": round(float(state.law), 3),
        "future": round(float(state.future), 3),
    }

    meta_patch = {
        "step": step + 1,
        "phase": field.get("phase", "DAY"),
        "mode": field.get("mode", "active"),
        "vitality": round(float(vitality), 3),
    }

    signal_patch = build_signal_payload(
        field=field,
        winner_agent=winner_agent,
        dominant_class=dominant_class,
        decision=decision,
        vitality=vitality,
    )

    bridge.update("flower", flower_patch, updated_by="CORE")
    bridge.update("meta", meta_patch, updated_by="CORE")
    bridge.update("signal", signal_patch, updated_by="CORE")

    print("CORE STEP:", step)
    print("winner_agent:", winner_agent)
    print("dominant_class:", dominant_class)
    print("decision:", decision)
    print("phase:", field.get("phase", "DAY"))
    print("mode:", field.get("mode", "active"))
    print("vitality:", round(float(vitality), 3))


if __name__ == "__main__":
    main()
