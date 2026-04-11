import json
import math
import os
import re
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Tuple, Optional

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

AGENTS = ("TANK", "MAGE", "ARCHER", "HEALER", "ASSASSIN")

FOCUS_LIMIT = 3
STRUCTURAL_TRIGGER_THRESHOLD = 3.0
SLEEP_SECONDS = 60

BIAS_ALPHA = 0.05
BIAS_DECAY = 0.98
BIAS_MIN = -1.5
BIAS_MAX = 1.5


def clamp01(x: Any) -> float:
    try:
        return max(0.0, min(1.0, float(x)))
    except Exception:
        return 0.0


def clamp_bias(x: Any) -> float:
    try:
        v = float(x)
    except Exception:
        v = 0.0
    return max(BIAS_MIN, min(BIAS_MAX, v))


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
    data = load_json(BUS_PATH, {})
    return data if isinstance(data, dict) else {}


def write_bus(bus: Dict[str, Any]):
    save_json(BUS_PATH, bus)


def get_meta(bus: Dict[str, Any]) -> Dict[str, Any]:
    meta = bus.get("meta")
    if not isinstance(meta, dict):
        meta = {}
        bus["meta"] = meta
    return meta


def get_prime_directive(bus: Dict[str, Any]) -> Dict[str, float]:
    meta = get_meta(bus)
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


def get_memory_bias(bus: Dict[str, Any]) -> Dict[str, float]:
    meta = get_meta(bus)
    raw = meta.get("memory_bias", {})
    if not isinstance(raw, dict):
        raw = {}

    out: Dict[str, float] = {}
    for agent in AGENTS:
        out[agent] = clamp_bias(raw.get(agent, 0.0))
    return out


def set_memory_bias(bus: Dict[str, Any], bias: Dict[str, float]):
    meta = get_meta(bus)
    meta["memory_bias"] = {k: round(clamp_bias(v), 6) for k, v in bias.items()}


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


def get_all_tasks() -> List[Dict[str, Any]]:
    out = []
    for obj in load_objects():
        if str(obj.get("type", "")).strip().lower() == "task":
            out.append(obj)
    return out


def get_open_tasks() -> List[Dict[str, Any]]:
    return [t for t in get_all_tasks() if str(t.get("status", "")).strip().lower() == "open"]


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

    def rank(
        self,
        tasks: List[Dict[str, Any]],
        directive: Dict[str, float],
        state_map: Dict[str, Dict[str, Any]],
        memory_bias: Dict[str, float],
    ):
        rows = []

        for task in tasks:
            task_id = str(task.get("id"))
            vec = task_vector(task)
            alignment = cosine_similarity(vec, directive)
            intensity = float(task.get("intensity", 0.0) or 0.0)
            novelty = float(task.get("novelty", 0.0) or 0.0)

            structural_bonus = 0.20 if is_structural(task) else 0.0
            mage_bias = memory_bias.get("MAGE", 0.0) if is_structural(task) else 0.0

            admission_score = (
                (0.55 * alignment)
                + (0.25 * intensity)
                + (0.10 * novelty)
                + structural_bonus
                + (0.10 * mage_bias)
            )

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


def structural_triggers(
    suppressed_rows: List[Tuple[Dict[str, Any], ClockTaskState]]
) -> List[Tuple[Dict[str, Any], ClockTaskState]]:
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


def parse_agent_from_reason(reason: str, key: str) -> Optional[str]:
    if not reason:
        return None
    m = re.search(rf"{key}=([A-Za-z_]+)", reason)
    if not m:
        return None
    name = str(m.group(1)).strip().upper()
    return name if name in AGENTS else None


def infer_primary_agent(task: Dict[str, Any]) -> Optional[str]:
    reason = str(task.get("execution_reason", "") or "")
    direct = str(task.get("primary_agent", "") or "").strip().upper()
    if direct in AGENTS:
        return direct

    parsed = parse_agent_from_reason(reason, "primary")
    if parsed:
        return parsed

    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
    hint = str(payload.get("executor_hint", "") or "").strip().upper()
    if hint in AGENTS:
        return hint

    return None


def infer_support_agent(task: Dict[str, Any]) -> Optional[str]:
    reason = str(task.get("execution_reason", "") or "")
    direct = str(task.get("support_agent", "") or "").strip().upper()
    if direct in AGENTS:
        return direct

    parsed = parse_agent_from_reason(reason, "support")
    if parsed:
        return parsed

    return None


def task_alignment_for_feedback(task: Dict[str, Any], clock_state: Dict[str, Dict[str, Any]], directive: Dict[str, float]) -> float:
    row = clock_state.get(str(task.get("id")), {})
    if isinstance(row, dict) and "alignment" in row:
        try:
            return clamp01(row.get("alignment", 0.0))
        except Exception:
            pass
    return cosine_similarity(task_vector(task), directive)


def compute_reward(task: Dict[str, Any], alignment: float) -> float:
    status = str(task.get("status", "")).strip().lower()
    reason = str(task.get("execution_reason", "") or "")
    structural = is_structural(task)

    reward = 0.0

    if status == "published":
        reward += 1.0
    elif status == "done":
        reward += 0.7
    elif status == "failed":
        reward -= 0.6
    elif status == "absorbed":
        reward += 0.0
    elif status == "skipped":
        reward -= 0.1
    else:
        reward += 0.0

    if structural:
        reward += 0.35

    if alignment >= 0.70:
        reward += 0.25
    elif alignment <= 0.25:
        reward -= 0.10

    if "no_changes" in reason:
        reward -= 0.35

    if "tank_force_publish" in reason:
        reward = 0.0

    return reward


def apply_bias_update(
    bias: Dict[str, float],
    agent: str,
    reward: float,
    alignment: float,
):
    if agent not in AGENTS:
        return
    delta = BIAS_ALPHA * reward * max(0.0, alignment)
    bias[agent] = clamp_bias(bias.get(agent, 0.0) + delta)


def decay_bias(bias: Dict[str, float]):
    for k in list(bias.keys()):
        bias[k] = clamp_bias(float(bias.get(k, 0.0)) * BIAS_DECAY)


def process_feedback(
    bus: Dict[str, Any],
    clock_state: Dict[str, Dict[str, Any]],
    directive: Dict[str, float],
) -> List[Dict[str, Any]]:
    meta = get_meta(bus)
    feedback_meta = meta.get("feedback", {})
    if not isinstance(feedback_meta, dict):
        feedback_meta = {}
        meta["feedback"] = feedback_meta

    processed_ids = feedback_meta.get("processed_task_ids", [])
    if not isinstance(processed_ids, list):
        processed_ids = []

    processed_set = {str(x) for x in processed_ids}
    bias = get_memory_bias(bus)

    events: List[Dict[str, Any]] = []
    tasks = get_all_tasks()

    for task in tasks:
        tid = str(task.get("id"))
        status = str(task.get("status", "")).strip().lower()

        if tid in processed_set:
            continue
        if status not in {"published", "done", "failed", "absorbed", "skipped"}:
            continue

        alignment = task_alignment_for_feedback(task, clock_state, directive)
        reward = compute_reward(task, alignment)
        primary = infer_primary_agent(task)
        support = infer_support_agent(task)
        reason = str(task.get("execution_reason", "") or "")

        # tank-owned escalation should not reward non-tank as structural success
        if "tank_force_publish" in reason:
            if primary and primary != "TANK":
                pass
            apply_bias_update(bias, "TANK", 0.40, max(alignment, 0.50))
        else:
            if primary:
                apply_bias_update(bias, primary, reward, alignment)
            if support and support != primary:
                apply_bias_update(bias, support, reward * 0.35, alignment)

        event = {
            "task_id": tid,
            "status": status,
            "primary": primary,
            "support": support,
            "alignment": round(alignment, 6),
            "reward": round(reward, 6),
            "structural": bool(is_structural(task)),
            "title": str(task.get("title", "")),
        }
        events.append(event)
        processed_set.add(tid)

    decay_bias(bias)
    set_memory_bias(bus, bias)

    feedback_meta["processed_task_ids"] = sorted(processed_set)
    feedback_meta["last_events"] = events[-20:]
    feedback_meta["last_updated_at"] = int(time.time())
    meta["feedback"] = feedback_meta

    return events


def write_clock_patch(
    bus: Dict[str, Any],
    directive: Dict[str, float],
    active_rows: List[Tuple[Dict[str, Any], ClockTaskState]],
    suppressed_rows: List[Tuple[Dict[str, Any], ClockTaskState]],
    promoted_ids: List[str],
):
    meta = get_meta(bus)
    clock_patch = {
        "tick_at": int(time.time()),
        "focus_limit": FOCUS_LIMIT,
        "prime_directive": directive,
        "active_task_ids": [str(t.get("id")) for t, _ in active_rows],
        "suppressed_task_ids": [str(t.get("id")) for t, _ in suppressed_rows],
        "promoted_task_ids": promoted_ids,
    }
    meta["v_clock"] = clock_patch


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


def print_feedback(events: List[Dict[str, Any]], bias: Dict[str, float]):
    print("FEEDBACK_EVENTS:")
    if not events:
        print("  - none")
    else:
        for e in events[-10:]:
            print(
                "  -",
                e["task_id"],
                "|",
                e["status"],
                "| primary=",
                e.get("primary"),
                "| support=",
                e.get("support"),
                "| reward=",
                e.get("reward"),
                "| align=",
                e.get("alignment"),
                "| structural=",
                e.get("structural"),
            )

    print("MEMORY_BIAS:")
    for agent in AGENTS:
        print("  -", agent, "=", round(bias.get(agent, 0.0), 4))


def tick():
    bus = read_bus()
    directive = get_prime_directive(bus)
    tasks = get_open_tasks()
    clock_state = load_clock_state()

    feedback_events = process_feedback(bus, clock_state, directive)
    memory_bias = get_memory_bias(bus)

    print("=== V_CLOCK TICK ===")
    print("OPEN_TASKS:", len(tasks))
    print("PRIME_DIRECTIVE:", directive)

    if not tasks:
        write_clock_patch(bus, directive, [], [], [])
        save_clock_state({})
        write_bus(bus)
        print_feedback(feedback_events, memory_bias)
        print("NO_OPEN_TASKS")
        print("=== V_CLOCK DONE ===")
        return

    field = InhibitoryField(focus_limit=FOCUS_LIMIT)
    active_rows, suppressed_rows = field.rank(tasks, directive, clock_state, memory_bias)
    triggered = structural_triggers(suppressed_rows)
    promoted_ids = promote_triggered_tasks(triggered)

    all_rows = active_rows + suppressed_rows
    write_back_state(all_rows)
    write_clock_patch(bus, directive, active_rows, suppressed_rows, promoted_ids)
    write_bus(bus)

    print_rows("ACTIVE_TASKS:", active_rows)
    print_rows("SUPPRESSED_TASKS:", suppressed_rows)

    if promoted_ids:
        print("STRUCTURAL_TRIGGERED:", promoted_ids)
    else:
        print("STRUCTURAL_TRIGGERED: []")

    print_feedback(feedback_events, memory_bias)
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
