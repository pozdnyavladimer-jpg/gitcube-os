import json
import math
import os
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Tuple

from runtime_experimental.object_store import load_objects, update_object

BUS_PATH = os.environ.get("V_RESONANCE_PATH", "v_resonance.json")
CLOCK_STATE_PATH = "v_clock_state.json"

STRUCTURAL_PROBLEMS = {
    "missing_init",
    "missing_init_group",
    "python_without_docs",
    "package_structure",
    "missing_root_readme",
    "missing_start_here",
}

DEFAULT_PRIME_DIRECTIVE = {
    "pressure": 0.35,
    "flow": 0.45,
    "structure": 0.95,
    "balance": 0.70,
    "law": 0.90,
    "future": 0.85,
}

FOCUS_LIMIT = 3
STRUCTURAL_TRIGGER_THRESHOLD = 3.0
SLEEP_SECONDS = 60


def clamp01(x: Any) -> float:
    try:
        return max(0.0, min(1.0, float(x)))
    except Exception:
        return 0.0


def load_json(path: str, default: Any):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path: str, data: Any):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def read_bus() -> Dict[str, Any]:
    return load_json(BUS_PATH, {})


def get_prime_directive(bus: Dict[str, Any]) -> Dict[str, float]:
    meta = bus.get("meta", {}) if isinstance(bus.get("meta"), dict) else {}
    directive = meta.get("prime_directive", DEFAULT_PRIME_DIRECTIVE)
    if not isinstance(directive, dict):
        directive = DEFAULT_PRIME_DIRECTIVE

    return {
        "pressure": clamp01(directive.get("pressure", DEFAULT_PRIME_DIRECTIVE["pressure"])),
        "flow": clamp01(directive.get("flow", DEFAULT_PRIME_DIRECTIVE["flow"])),
        "structure": clamp01(directive.get("structure", DEFAULT_PRIME_DIRECTIVE["structure"])),
        "balance": clamp01(directive.get("balance", DEFAULT_PRIME_DIRECTIVE["balance"])),
        "law": clamp01(directive.get("law", DEFAULT_PRIME_DIRECTIVE["law"])),
        "future": clamp01(directive.get("future", DEFAULT_PRIME_DIRECTIVE["future"])),
    }


def task_vector(task: Dict[str, Any]) -> Dict[str, float]:
    rv = task.get("resonance_vector", {}) if isinstance(task.get("resonance_vector"), dict) else {}
    return {
        "pressure": clamp01(rv.get("pressure", 0.0)),
        "flow": clamp01(rv.get("flow", 0.0)),
        "structure": clamp01(rv.get("structure", 0.0)),
        "balance": clamp01(rv.get("balance", 0.0)),
        "law": clamp01(rv.get("law", 0.0)),
        "future": clamp01(rv.get("future", 0.0)),
    }


def cosine_similarity(a: Dict[str, float], b: Dict[str, float]) -> float:
    keys = ("pressure", "flow", "structure", "balance", "law", "future")
    dot = sum(float(a[k]) * float(b[k]) for k in keys)
    na = math.sqrt(sum(float(a[k]) ** 2 for k in keys))
    nb = math.sqrt(sum(float(b[k]) ** 2 for k in keys))
    if na <= 1e-9 or nb <= 1e-9:
        return 0.0
    return max(0.0, min(1.0, dot / (na * nb)))


def get_open_tasks() -> List[Dict[str, Any]]:
    out = []
    for obj in load_objects():
        if str(obj.get("type", "")).strip().lower() != "task":
            continue
        if str(obj.get("status", "")).strip().lower() != "open":
            continue
        out.append(obj)
    return out


def get_problem(task: Dict[str, Any]) -> str:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
    return str(payload.get("problem", "")).strip().lower()


def is_structural(task: Dict[str, Any]) -> bool:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
    hint = str(payload.get("executor_hint", "")).strip().upper()
    return get_problem(task) in STRUCTURAL_PROBLEMS or hint == "MAGE"


@dataclass
class ClockTaskState:
    alignment: float = 0.0
    admission_score: float = 0.0
    deferred_energy: float = 0.0
    blocked_steps: int = 0
    active_steps: int = 0
    structural_triggered: bool = False


def load_clock_state() -> Dict[str, Dict[str, Any]]:
    raw = load_json(CLOCK_STATE_PATH, {})
    return raw if isinstance(raw, dict) else {}


def save_clock_state(state: Dict[str, Dict[str, Any]]):
    save_json(CLOCK_STATE_PATH, state)


class InhibitoryField:
    def __init__(self, focus_limit: int = 3):
        self.focus_limit = max(1, int(focus_limit))

    def rank(self, tasks: List[Dict[str, Any]], directive: Dict[str, float], state_map: Dict[str, Dict[str, Any]]):
        rows = []

        for task in tasks:
            task_id = str(task.get("id"))
            vec = task_vector(task)
            alignment = cosine_similarity(vec, directive)
            intensity = float(task.get("intensity", 0.0))
            novelty = float(task.get("novelty", 0.0))

            structural_bonus = 0.20 if is_structural(task) else 0.0
            admission_score = (0.55 * alignment) + (0.25 * intensity) + (0.10 * novelty) + structural_bonus

            prev = ClockTaskState(**state_map.get(task_id, {})) if isinstance(state_map.get(task_id, {}), dict) else ClockTaskState()
            prev.alignment = round(alignment, 6)
            prev.admission_score = round(admission_score, 6)

            rows.append((task, prev))

        rows.sort(key=lambda x: x[1].admission_score, reverse=True)

        active = rows[: self.focus_limit]
        suppressed = rows[self.focus_limit :]

        for _, st in active:
            st.active_steps += 1
            st.blocked_steps = 0
            st.deferred_energy = max(0.0, st.deferred_energy - 0.25)

        for task, st in suppressed:
            base_gain = 0.15
            if is_structural(task):
                base_gain += 0.20
            base_gain += 0.25 * st.alignment
            st.deferred_energy += base_gain
            st.blocked_steps += 1

        return active, suppressed


def structural_triggers(suppressed_rows: List[Tuple[Dict[str, Any], ClockTaskState]]) -> List[Tuple[Dict[str, Any], ClockTaskState]]:
    out = []

    for task, st in suppressed_rows:
        if not is_structural(task):
            continue
        if st.deferred_energy >= STRUCTURAL_TRIGGER_THRESHOLD and st.blocked_steps >= 2:
            st.structural_triggered = True
            out.append((task, st))

    return out


def write_back_state(all_rows: List[Tuple[Dict[str, Any], ClockTaskState]]):
    state_map: Dict[str, Dict[str, Any]] = {}

    for task, st in all_rows:
        state_map[str(task.get("id"))] = asdict(st)

    save_clock_state(state_map)


def promote_triggered_tasks(triggered: List[Tuple[Dict[str, Any], ClockTaskState]]):
    promoted = []

    for task, st in triggered:
        task_id = str(task.get("id"))
        payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
        payload["executor_hint"] = "MAGE"

        rv = task.get("resonance_vector", {}) if isinstance(task.get("resonance_vector"), dict) else {}
        rv["future"] = round(min(1.0, float(rv.get("future", 0.0)) + 0.20), 3)
        rv["structure"] = round(max(0.0, float(rv.get("structure", 0.0)) - 0.05), 3)
        rv["law"] = round(max(0.0, float(rv.get("law", 0.0)) - 0.05), 3)

        update_object(task_id, {
            "payload": payload,
            "resonance_vector": rv,
            "clock_trigger": "STRUCTURAL_PHASE_SHIFT",
            "clock_trigger_at": int(time.time()),
        })

        st.deferred_energy = 0.0
        st.blocked_steps = 0
        st.structural_triggered = False
        promoted.append(task_id)

    return promoted


def write_clock_patch(
    directive: Dict[str, float],
    active_rows: List[Tuple[Dict[str, Any], ClockTaskState]],
    suppressed_rows: List[Tuple[Dict[str, Any], ClockTaskState]],
    promoted_ids: List[str],
):
    bus = read_bus()
    meta = bus.get("meta", {}) if isinstance(bus.get("meta"), dict) else {}
    clock_patch = {
        "tick_at": int(time.time()),
        "focus_limit": FOCUS_LIMIT,
        "prime_directive": directive,
        "active_task_ids": [str(t.get("id")) for t, _ in active_rows],
        "suppressed_task_ids": [str(t.get("id")) for t, _ in suppressed_rows],
        "promoted_task_ids": promoted_ids,
    }
    meta["v_clock"] = clock_patch
    bus["meta"] = meta
    save_json(BUS_PATH, bus)


def print_rows(label: str, rows: List[Tuple[Dict[str, Any], ClockTaskState]]):
    print(label)
    if not rows:
        print("  - none")
        return
    for task, st in rows:
        print(
            "  -",
            task.get("id"),
            "|",
            task.get("title"),
            "| align=",
            round(st.alignment, 3),
            "| score=",
            round(st.admission_score, 3),
            "| deferred=",
            round(st.deferred_energy, 3),
            "| blocked=",
            st.blocked_steps,
        )


def tick():
    bus = read_bus()
    directive = get_prime_directive(bus)
    tasks = get_open_tasks()
    state_map = load_clock_state()

    print("=== V_CLOCK TICK ===")
    print("OPEN_TASKS:", len(tasks))
    print("PRIME_DIRECTIVE:", directive)

    if not tasks:
        write_clock_patch(directive, [], [], [])
        save_clock_state({})
        print("NO_OPEN_TASKS")
        return

    field = InhibitoryField(focus_limit=FOCUS_LIMIT)
    active_rows, suppressed_rows = field.rank(tasks, directive, state_map)
    triggered = structural_triggers(suppressed_rows)
    promoted_ids = promote_triggered_tasks(triggered)

    all_rows = active_rows + suppressed_rows
    write_back_state(all_rows)
    write_clock_patch(directive, active_rows, suppressed_rows, promoted_ids)

    print_rows("ACTIVE_TASKS:", active_rows)
    print_rows("SUPPRESSED_TASKS:", suppressed_rows)

    if promoted_ids:
        print("STRUCTURAL_TRIGGERED:", promoted_ids)
    else:
        print("STRUCTURAL_TRIGGERED: []")

    print("=== V_CLOCK DONE ===")


def loop():
    while True:
        tick()
        time.sleep(SLEEP_SECONDS)


if __name__ == "__main__":
    mode = os.environ.get("V_CLOCK_MODE", "tick").strip().lower()
    if mode == "loop":
        loop()
    else:
        tick()
