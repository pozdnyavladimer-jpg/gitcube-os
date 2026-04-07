import os
from typing import Dict, Any, List

from v_bridge import VBridge
from core.state import default_state, normalize_state, SystemState
from runtime_experimental.field_engine import FieldEngine
from runtime_experimental.agent_loop import choose_best_agent
from runtime_experimental.vitality_engine import update_vitality
from runtime_experimental.lab_bridge import build_lab_field_patch
from runtime_experimental.navigator_bridge import (
    load_navigator_feedback,
    build_feedback_patch,
)
from runtime_experimental.agents_logic import choose_coordination_effect
from runtime_experimental.explorer_sensor import (
    load_external_signal,
    build_explorer_patch,
    build_task_object,
)
from runtime_experimental.object_store import add_object, get_open_tasks, load_objects

BUS_PATH = os.environ.get("V_RESONANCE_PATH", "v_resonance.json")


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


def apply_tank_build(state_vector: Dict[str, float]) -> Dict[str, float]:
    patched = dict(state_vector)
    patched["structure"] = float(patched.get("structure", 0.0)) + 0.05
    patched["balance"] = float(patched.get("balance", 0.0)) + 0.03
    patched["flow"] = float(patched.get("flow", 0.0)) + 0.01
    return normalize_state(patched)


def apply_mage_repair(state_vector: Dict[str, float]) -> Dict[str, float]:
    patched = dict(state_vector)
    patched["structure"] = float(patched.get("structure", 0.0)) + 0.04
    patched["law"] = float(patched.get("law", 0.0)) + 0.03
    patched["flow"] = float(patched.get("flow", 0.0)) + 0.01
    patched["future"] = max(0.0, float(patched.get("future", 0.0)) - 0.02)
    patched["pressure"] = max(0.0, float(patched.get("pressure", 0.0)) - 0.01)
    return normalize_state(patched)


def apply_explorer_input(
    state_vector: Dict[str, float],
    explorer_patch: Dict[str, Any],
) -> Dict[str, float]:
    patched = dict(state_vector)
    patched["pressure"] = float(patched.get("pressure", 0.0)) + float(explorer_patch.get("pressure_delta", 0.0))
    patched["future"] = float(patched.get("future", 0.0)) + float(explorer_patch.get("future_delta", 0.0))
    return normalize_state(patched)


def apply_epigenetic_clamp(
    state_vector: Dict[str, float],
    structure_floor: float,
    law_floor: float,
) -> Dict[str, float]:
    clamped = dict(state_vector)
    clamped["structure"] = max(float(clamped.get("structure", 0.0)), float(structure_floor))
    clamped["law"] = max(float(clamped.get("law", 0.0)), float(law_floor))
    return normalize_state(clamped)


def update_floors(
    *,
    state_vector: Dict[str, float],
    coordination: Dict[str, Any],
    structure_floor: float,
    law_floor: float,
) -> Dict[str, float]:
    new_structure_floor = float(structure_floor)
    new_law_floor = float(law_floor)

    role = coordination.get("role")
    action = coordination.get("action")

    if role == "TANK" and action == "BUILD_STRUCTURE":
        new_structure_floor = max(new_structure_floor, float(state_vector.get("structure", 0.0)) * 0.90)

    if role == "MAGE" and coordination.get("repair_state"):
        new_law_floor = max(new_law_floor, float(state_vector.get("law", 0.0)) * 0.85)
        new_structure_floor = max(new_structure_floor, float(state_vector.get("structure", 0.0)) * 0.85)

    return {
        "structure_floor": round(new_structure_floor, 3),
        "law_floor": round(new_law_floor, 3),
    }


def build_signal_payload(
    *,
    field: Dict[str, Any],
    winner_agent: str,
    dominant_class: str,
    decision: str,
    vitality: float,
    coordination: Dict[str, Any],
    explorer_patch: Dict[str, Any],
    open_task_count: int,
    latest_task_id: str,
) -> Dict[str, Any]:
    if decision == "COMMIT":
        actor_action = "BUILD"
    elif decision == "SOFT_COMMIT":
        actor_action = "STABILIZE"
    else:
        actor_action = "WAIT"

    return {
        "source": "CORE",
        "target": "ACTOR",
        "action": actor_action,
        "decision": decision,
        "winner_agent": winner_agent,
        "dominant_class": dominant_class,
        "phase": field.get("phase", "DAY"),
        "mode": field.get("mode", "active"),
        "bond": "NONE",
        "reason": f"{dominant_class}_{decision}".lower(),
        "vitality": round(float(vitality), 3),
        "navigator_action": field.get("navigator_action", "STABLE"),
        "coordination_role": coordination.get("role", "NONE"),
        "coordination_action": coordination.get("action", "STABLE"),
        "coordination_reason": coordination.get("reason", "none"),
        "explorer_kind": explorer_patch.get("kind", "none"),
        "explorer_pressure_delta": explorer_patch.get("pressure_delta", 0.0),
        "explorer_future_delta": explorer_patch.get("future_delta", 0.0),
        "open_task_count": int(open_task_count),
        "latest_task_id": latest_task_id,
    }


def _tail_list(value: Any, max_len: int) -> List[Any]:
    if not isinstance(value, list):
        return []
    return value[-max_len:]


def _find_latest_task() -> Dict[str, Any] | None:
    data = load_objects()
    tasks = [o for o in data if o.get("type") == "task"]
    if not tasks:
        return None

    def task_num(obj: Dict[str, Any]) -> int:
        obj_id = str(obj.get("id", "task_0"))
        tail = obj_id.split("_")[-1]
        return int(tail) if tail.isdigit() else 0

    tasks.sort(key=task_num)
    return tasks[-1]


def main():
    bridge = VBridge(BUS_PATH)
    bus = bridge.read_state()

    flower = dict(bus.get("flower", {}))
    meta = dict(bus.get("meta", {}))

    state = default_state()
    vitality = float(meta.get("vitality", 0.42))
    step = int(meta.get("step", 0))

    class_history = _tail_list(meta.get("class_history", []), 20)
    action_history = _tail_list(meta.get("action_history", []), 10)
    vitality_history = _tail_list(meta.get("vitality_history", []), 10)

    structure_floor = float(meta.get("structure_floor", 0.15))
    law_floor = float(meta.get("law_floor", 0.10))

    current_state_vector = {
        "pressure": float(flower.get("pressure", state.pressure)),
        "flow": float(flower.get("flow", state.flow)),
        "structure": float(flower.get("structure", state.structure)),
        "balance": float(flower.get("balance", state.balance)),
        "law": float(flower.get("law", state.law)),
        "future": float(flower.get("future", state.future)),
    }

    external_signal = load_external_signal()
    explorer_patch = build_explorer_patch(external_signal)
    current_state_vector = apply_explorer_input(current_state_vector, explorer_patch)
    state = SystemState.from_dict(current_state_vector)

    latest_task_id = ""

    if explorer_patch.get("kind") in ("task", "issue", "opportunity", "warning"):
        latest_existing = _find_latest_task()

        parent_id = None
        related_to = []
        graph_depth = 0

        if latest_existing is not None:
            parent_id = str(latest_existing.get("id"))
            related_to = [parent_id]
            graph_depth = int(latest_existing.get("graph_depth", 0)) + 1

        task_obj = build_task_object(external_signal)

        payload_title = str(task_obj.get("payload", {}).get("title", "")).strip()
        if payload_title:
            task_obj["title"] = payload_title
        else:
            task_obj["title"] = f"Task step {step + 1}"

        task_obj["parent_id"] = parent_id
        task_obj["related_to"] = related_to
        task_obj["graph_depth"] = graph_depth

        created = add_object(task_obj)
        latest_task_id = str(created.get("id", ""))

    open_task_count = len(get_open_tasks())

    field_engine = FieldEngine()
    field = field_engine.build_field(
        step=step,
        vitality=vitality,
        class_history=class_history,
    )

    lab_patch = build_lab_field_patch(
        step=step,
        vitality=vitality,
        history=class_history,
    )
    field = merge_field(field, lab_patch)

    navigator_feedback = load_navigator_feedback()
    navigator_patch = build_feedback_patch(navigator_feedback)
    field = merge_field(field, navigator_patch)

    if explorer_patch.get("mode"):
        field["mode"] = explorer_patch["mode"]

    coordination = choose_coordination_effect(
        state=current_state_vector,
        action_history=action_history,
        vitality_history=vitality_history,
    )

    if coordination.get("new_mode"):
        field["mode"] = coordination["new_mode"]

    tank_build_applied = False
    mage_repair_applied = False

    if coordination.get("role") == "TANK" and coordination.get("build_state"):
        current_state_vector = apply_tank_build(current_state_vector)
        state = SystemState.from_dict(current_state_vector)
        tank_build_applied = True

    if coordination.get("role") == "MAGE" and coordination.get("repair_state"):
        current_state_vector = apply_mage_repair(current_state_vector)
        state = SystemState.from_dict(current_state_vector)
        mage_repair_applied = True

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

    committed_state_vector = {
        "pressure": float(state.pressure),
        "flow": float(state.flow),
        "structure": float(state.structure),
        "balance": float(state.balance),
        "law": float(state.law),
        "future": float(state.future),
    }

    floors = update_floors(
        state_vector=committed_state_vector,
        coordination=coordination,
        structure_floor=structure_floor,
        law_floor=law_floor,
    )

    committed_state_vector = apply_epigenetic_clamp(
        committed_state_vector,
        floors["structure_floor"],
        floors["law_floor"],
    )

    state = SystemState.from_dict(committed_state_vector)

    flower_patch = {
        "pressure": round(float(state.pressure), 3),
        "flow": round(float(state.flow), 3),
        "structure": round(float(state.structure), 3),
        "balance": round(float(state.balance), 3),
        "law": round(float(state.law), 3),
        "future": round(float(state.future), 3),
    }

    new_action = coordination.get("action") or field.get("navigator_action", "STABLE")

    updated_action_history = (action_history + [new_action])[-10:]
    updated_class_history = (class_history + [dominant_class])[-20:]
    updated_vitality_history = (vitality_history + [round(float(vitality), 3)])[-10:]

    meta_patch = {
        "step": step + 1,
        "phase": field.get("phase", "DAY"),
        "mode": field.get("mode", "active"),
        "vitality": round(float(vitality), 3),
        "structure_floor": floors["structure_floor"],
        "law_floor": floors["law_floor"],
        "class_history": updated_class_history,
        "action_history": updated_action_history,
        "vitality_history": updated_vitality_history,
        "external_signal_kind": explorer_patch.get("kind", "none"),
        "object_count": len(load_objects()),
    }

    signal_patch = build_signal_payload(
        field=field,
        winner_agent=winner_agent,
        dominant_class=dominant_class,
        decision=decision,
        vitality=vitality,
        coordination=coordination,
        explorer_patch=explorer_patch,
        open_task_count=open_task_count,
        latest_task_id=latest_task_id,
    )

    bridge.update("flower", flower_patch, updated_by="CORE")
    bridge.update("meta", meta_patch, updated_by="CORE")
    bridge.update("signal", signal_patch, updated_by="CORE")

    created_task = _find_latest_task()
    created_parent = created_task.get("parent_id") if created_task else None
    created_depth = created_task.get("graph_depth") if created_task else 0
    created_title = created_task.get("title") if created_task else ""

    print("=== OS SYNC ===")
    print("step:", step)
    print("winner_agent:", winner_agent)
    print("dominant_class:", dominant_class)
    print("decision:", decision)
    print("phase:", field.get("phase", "DAY"))
    print("mode:", field.get("mode", "active"))
    print("explorer_kind:", explorer_patch.get("kind", "none"))
    print("explorer_pressure_delta:", explorer_patch.get("pressure_delta", 0.0))
    print("explorer_future_delta:", explorer_patch.get("future_delta", 0.0))
    print("coordination_role:", coordination.get("role", "NONE"))
    print("coordination_action:", coordination.get("action", "STABLE"))
    print("coordination_reason:", coordination.get("reason", "none"))
    print("tank_build_applied:", tank_build_applied)
    print("mage_repair_applied:", mage_repair_applied)
    print("structure:", flower_patch["structure"])
    print("law:", flower_patch["law"])
    print("structure_floor:", floors["structure_floor"])
    print("law_floor:", floors["law_floor"])
    print("open_task_count:", open_task_count)
    print("latest_task_id:", latest_task_id)
    print("task_title:", created_title)
    print("parent_id:", created_parent)
    print("graph_depth:", created_depth)
    print("vitality:", round(float(vitality), 3))


if __name__ == "__main__":
    main()
