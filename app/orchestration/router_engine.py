from __future__ import annotations

from typing import Dict, Any
from core.analysis.dependency_graph import build_dependency_graph, find_dependents




def _guess_target_modules(task: Dict[str, Any]) -> List[str]:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}

    out: List[str] = []

    source_module = str(payload.get("source_module", "")).strip()
    if source_module:
        out.append(source_module)

    module = str(payload.get("module", "")).strip()
    if module:
        out.append(module)

    paths = payload.get("paths", [])
    if isinstance(paths, list):
        for p in paths:
            sp = str(p).strip()
            if sp.endswith(".py"):
                mod = sp[:-3].replace("/", ".").replace("\\", ".")
                if mod:
                    out.append(mod)

    unique: List[str] = []
    seen = set()
    for item in out:
        if item and item not in seen:
            seen.add(item)
            unique.append(item)

    return unique


def get_repair_scope(task: Dict[str, Any]) -> Dict[str, Any]:
    try:
        graph = build_dependency_graph(".")
    except Exception as e:
        return {
            "ok": False,
            "reason": f"graph_build_failed:{e}",
            "targets": [],
            "dependents": {},
            "scope": [],
        }

    targets = _guess_target_modules(task)
    dependents: Dict[str, List[str]] = {}
    scope: List[str] = []

    for mod in targets:
        deps = find_dependents(mod, graph)
        dependents[mod] = deps
        if mod not in scope:
            scope.append(mod)
        for dep in deps:
            if dep not in scope:
                scope.append(dep)

    return {
        "ok": True,
        "targets": targets,
        "dependents": dependents,
        "scope": scope[:12],
        "graph_meta": {
            "node_count": graph.get("node_count", 0),
            "edge_count": graph.get("edge_count", 0),
            "parse_errors": len(graph.get("parse_errors", {})),
        },
    }


def route_task(task: Dict[str, Any]) -> str:
    payload = task.get("payload", {}) if isinstance(task.get("payload"), dict) else {}
    problem = str(payload.get("problem", task.get("problem", ""))).strip().lower()

    structural_mesh_problems = {
        "missing_init_group",
        "missing_init",
        "package_structure",
        "structural_orphans_group",
        "missing_module_group",
        "broken_module_group",
    }

    import_llm_mesh_problems = {
        "broken_import_group",
    }

    if problem in structural_mesh_problems:
        return "STRUCTURAL_MESH"

    if problem in import_llm_mesh_problems:
        return "IMPORT_LLM_MESH"

    return "ROUTE_NOT_IMPLEMENTED"


if __name__ == "__main__":
    demos = [
        {"problem": "missing_init_group"},
        {"problem": "structural_orphans_group"},
        {"problem": "broken_import_group"},
        {"problem": "unknown_problem"},
    ]

    for item in demos:
        print(item["problem"], "->", route_task(item))
