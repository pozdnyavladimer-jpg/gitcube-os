from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, UTC, timedelta
from typing import Dict, Any, List


GRAPH_FILE = Path("reports/graph_weights.json")
GRAPH_FILE.parent.mkdir(exist_ok=True)


def _now() -> datetime:
    return datetime.now(UTC)


def _now_iso() -> str:
    return _now().isoformat()


def _load_state() -> Dict[str, Any]:
    if not GRAPH_FILE.exists():
        return {"edges": {}}
    try:
        return json.loads(GRAPH_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"edges": {}}


def _save_state(state: Dict[str, Any]) -> None:
    GRAPH_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _norm(value: str) -> str:
    return str(value or "").strip()


def reinforce_edge(source_node: str, target_node: str, weight_delta: float = 1.0) -> Dict[str, Any]:
    source_node = _norm(source_node)
    target_node = _norm(target_node)

    if not source_node or not target_node:
        return {"ok": False, "reason": "missing_node"}

    state = _load_state()
    edges = state.setdefault("edges", {})
    bucket = edges.setdefault(source_node, {})

    node = bucket.get(target_node, {
        "weight": 0.0,
        "last_used": _now_iso(),
    })

    current_weight = float(node.get("weight", 0.0))
    new_weight = round(current_weight + float(weight_delta), 4)

    bucket[target_node] = {
        "weight": new_weight,
        "last_used": _now_iso(),
    }

    _save_state(state)
    return {
        "ok": True,
        "source_node": source_node,
        "target_node": target_node,
        "weight": new_weight,
    }


def get_heaviest_neighbors(source_node: str, limit: int = 3) -> List[str]:
    source_node = _norm(source_node)
    if not source_node:
        return []

    state = _load_state()
    edges = state.get("edges", {})
    bucket = edges.get(source_node, {})

    ranked = sorted(
        bucket.items(),
        key=lambda x: float(x[1].get("weight", 0.0)),
        reverse=True,
    )
    return [node for node, _meta in ranked[: max(1, int(limit))]]


def get_edge_weight(source_node: str, target_node: str) -> float:
    source_node = _norm(source_node)
    target_node = _norm(target_node)

    state = _load_state()
    edges = state.get("edges", {})
    return float(edges.get(source_node, {}).get(target_node, {}).get("weight", 0.0))


def apply_decay(
    decay_factor: float = 0.92,
    min_weight: float = 0.15,
    grace_hours: int = 6,
) -> Dict[str, Any]:
    state = _load_state()
    edges = state.get("edges", {})

    now = _now()
    grace_delta = timedelta(hours=int(grace_hours))

    removed_edges = 0
    decayed_edges = 0
    removed_nodes = 0

    empty_sources = []

    for source_node, targets in list(edges.items()):
        dead_targets = []

        for target_node, meta in list(targets.items()):
            try:
                weight = float(meta.get("weight", 0.0))
            except Exception:
                weight = 0.0

            try:
                last_used = datetime.fromisoformat(meta.get("last_used", _now_iso()))
            except Exception:
                last_used = now

            # не чіпаємо свіжі зв’язки
            if now - last_used < grace_delta:
                continue

            new_weight = round(weight * float(decay_factor), 4)

            if new_weight < float(min_weight):
                dead_targets.append(target_node)
            else:
                targets[target_node]["weight"] = new_weight
                decayed_edges += 1

        for target_node in dead_targets:
            del targets[target_node]
            removed_edges += 1

        if not targets:
            empty_sources.append(source_node)

    for source_node in empty_sources:
        del edges[source_node]
        removed_nodes += 1

    _save_state(state)
    return {
        "ok": True,
        "decayed_edges": decayed_edges,
        "removed_edges": removed_edges,
        "removed_nodes": removed_nodes,
    }


def list_graph() -> Dict[str, Any]:
    state = _load_state()
    return {"ok": True, "edges": state.get("edges", {})}


def clear_graph() -> Dict[str, Any]:
    _save_state({"edges": {}})
    return {"ok": True}
