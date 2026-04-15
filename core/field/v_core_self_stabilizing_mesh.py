from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List
import os


@dataclass
class MeshNode:
    path: str
    tension: float = 0.0
    ideal_target: str = ""
    neighbors: List[str] = field(default_factory=list)


def _normalize_paths(paths: Any) -> List[str]:
    if not isinstance(paths, list):
        return []
    out: List[str] = []
    for p in paths:
        s = str(p).strip().rstrip("/")
        if s:
            out.append(s)
    return out


def build_mesh_from_task(task: Dict[str, Any]) -> List[MeshNode]:
    problem = str(task.get("problem", "")).strip().lower()
    paths = _normalize_paths(task.get("paths", []))
    nodes: List[MeshNode] = []

    for path in paths:
        ideal_target = path
        if problem == "missing_init_group":
            if path.endswith(".py"):
                parent = os.path.dirname(path) or "."
                ideal_target = os.path.join(parent, "__init__.py")
            else:
                ideal_target = os.path.join(path, "__init__.py")

        nodes.append(MeshNode(path=path, ideal_target=ideal_target))

    for i, node in enumerate(nodes):
        if i > 0:
            node.neighbors.append(nodes[i - 1].path)
        if i < len(nodes) - 1:
            node.neighbors.append(nodes[i + 1].path)

    return nodes


def compute_tension(nodes: List[MeshNode], problem: str) -> None:
    for node in nodes:
        if problem == "missing_init_group":
            if not os.path.exists(node.ideal_target):
                node.tension = 0.8
            else:
                node.tension = 0.05
        else:
            node.tension = 0.2


def healer_relaxation(nodes: List[MeshNode]) -> None:
    for node in nodes:
        if node.tension > 0.5:
            node.tension *= 0.7
        elif node.tension > 0.1:
            node.tension *= 0.9


def stabilize_task_mesh(task: Dict[str, Any], steps: int = 3) -> Dict[str, Any]:
    problem = str(task.get("problem", "")).strip().lower()
    nodes = build_mesh_from_task(task)

    if not nodes:
        return {
            "ok": False,
            "avg_tension": 1.0,
            "hotspots": [],
            "recommended_targets": [],
            "stabilization_score": 0.0,
        }

    compute_tension(nodes, problem)

    for _ in range(steps):
        healer_relaxation(nodes)

    tensions = [n.tension for n in nodes]
    avg_tension = sum(tensions) / max(1, len(tensions))

    hotspots = [
        {
            "path": n.path,
            "ideal_target": n.ideal_target,
            "tension": round(n.tension, 3),
        }
        for n in nodes
        if n.tension > 0.12
    ]

    recommended_targets = [n.ideal_target for n in nodes]

    return {
        "ok": avg_tension < 0.6,
        "avg_tension": round(avg_tension, 3),
        "hotspots": sorted(hotspots, key=lambda x: x["tension"], reverse=True),
        "recommended_targets": recommended_targets,
        "stabilization_score": round(max(0.0, 1.0 - avg_tension), 3),
    }


if __name__ == "__main__":
    demo_task = {
        "problem": "missing_init_group",
        "paths": ["core", "tests", "runtime_experimental"],
    }
    print(stabilize_task_mesh(demo_task))
