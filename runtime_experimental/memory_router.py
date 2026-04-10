import re
from typing import Dict, Any, Tuple

from router import score_agents, select_support, pair_bonus, build_reason
from runtime_experimental.object_store import load_objects

AGENTS = ("TANK", "MAGE", "ARCHER", "HEALER", "ASSASSIN")
SUCCESS_STATUSES = {"done", "published"}
FAIL_STATUSES = {"failed"}


def _clamp(x: float, low: float = -0.20, high: float = 0.20) -> float:
    return max(low, min(high, float(x)))


def _extract_primary_agent(obj: Dict[str, Any]) -> str:
    text = str(obj.get("execution_reason", "") or "")
    m = re.search(r"primary=([A-Z]+)", text)
    if m:
        return m.group(1)
    return ""


def _task_problem(task: Dict[str, Any]) -> str:
    payload = task.get("payload", {}) or {}
    return str(payload.get("problem", "") or "").strip().lower()


def _task_has_path(task: Dict[str, Any]) -> bool:
    payload = task.get("payload", {}) or {}
    return bool(str(payload.get("path", "") or "").strip())


def build_memory_bias(task: Dict[str, Any]) -> Dict[str, float]:
    current_problem = _task_problem(task)
    current_has_path = _task_has_path(task)

    bias = {agent: 0.0 for agent in AGENTS}

    for obj in load_objects():
        if obj.get("type") != "task":
            continue

        agent = _extract_primary_agent(obj)
        if agent not in AGENTS:
            continue

        status = str(obj.get("status", "") or "").strip().lower()
        obj_problem = _task_problem(obj)
        obj_has_path = _task_has_path(obj)

        same_problem = bool(current_problem) and obj_problem == current_problem
        same_path_mode = obj_has_path == current_has_path

        if status in SUCCESS_STATUSES:
            bias[agent] += 0.02
            if same_problem:
                bias[agent] += 0.08
            if same_path_mode:
                bias[agent] += 0.04

        elif status in FAIL_STATUSES:
            bias[agent] -= 0.02
            if same_problem:
                bias[agent] -= 0.08
            if same_path_mode:
                bias[agent] -= 0.04

    for agent in AGENTS:
        bias[agent] = round(_clamp(bias[agent]), 6)

    return bias


def select_pair_with_memory(task: Dict[str, Any]) -> Tuple[str, str, Dict[str, float], str, Dict[str, float]]:
    base_scores = score_agents(task)
    memory_bias = build_memory_bias(task)

    merged_scores = {}
    for agent in AGENTS:
        merged_scores[agent] = round(float(base_scores.get(agent, 0.0)) + float(memory_bias.get(agent, 0.0)), 6)

    primary = max(merged_scores, key=merged_scores.get)
    support, support_total = select_support(primary, merged_scores)
    bonus = pair_bonus(primary, support)
    reason = build_reason(task, primary, support, bonus)

    if any(abs(v) > 0.0001 for v in memory_bias.values()):
        reason += ",memory_bias"

    merged_scores["_pair_bonus"] = round(bonus, 6)
    merged_scores["_support_total"] = round(support_total, 6)

    return primary, support, merged_scores, reason, memory_bias
