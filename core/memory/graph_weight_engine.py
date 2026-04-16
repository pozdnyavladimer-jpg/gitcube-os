from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List


GRAPH_FILE = Path("reports/graph_weights.json")
GRAPH_FILE.parent.mkdir(exist_ok=True)


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


def reinforce_edge(source_node: str, target_node: str, weight_delta: int = 1) -> Dict[str, Any]:
    source_node = _norm(source_node)
    target_node = _norm(target_node)

    if not source_node or not target_node:
        return {"ok": False, "reason": "missing_node"}

    state = _load_state()
    edges = state.setdefault("edges", {})
    bucket = edges.setdefault(source_node, {})

    current = int(bucket.get(target_node, 0))
    bucket[target_node] = current + int(weight_delta)

    _save_state(state)
    return {
        "ok": True,
        "source_node": source_node,
        "target_node": target_node,
        "weight": bucket[target_node],
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
        key=lambda x: int(x[1]),
        reverse=True,
    )
    return [node for node, _weight in ranked[: max(1, int(limit))]]


def get_edge_weight(source_node: str, target_node: str) -> int:
    source_node = _norm(source_node)
    target_node = _norm(target_node)

    state = _load_state()
    edges = state.get("edges", {})
    return int(edges.get(source_node, {}).get(target_node, 0))


def list_graph() -> Dict[str, Any]:
    state = _load_state()
    return {"ok": True, "edges": state.get("edges", {})}


def clear_graph() -> Dict[str, Any]:
    _save_state({"edges": {}})
    return {"ok": True}
