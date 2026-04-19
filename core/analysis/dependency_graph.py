from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any, Dict, List, Set


REPO_ROOT = Path(".")
REPORT_PATH = Path("reports/dependency_graph.json")


def module_name_from_path(path: Path, repo_root: Path = REPO_ROOT) -> str:
    path = path.resolve()
    repo_root = repo_root.resolve()

    if path.name == "__init__.py":
        rel = path.parent.relative_to(repo_root)
    else:
        rel = path.relative_to(repo_root).with_suffix("")

    return ".".join(rel.parts)


def module_to_py_path(module: str, repo_root: Path = REPO_ROOT) -> Path:
    return repo_root / Path(module.replace(".", "/")).with_suffix(".py")


def module_to_package_init(module: str, repo_root: Path = REPO_ROOT) -> Path:
    return repo_root / Path(module.replace(".", "/")) / "__init__.py"


def module_exists(module: str, repo_root: Path = REPO_ROOT) -> bool:
    return module_to_py_path(module, repo_root).exists() or module_to_package_init(module, repo_root).exists()


def safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def resolve_relative_import(current_module: str, imported_module: str | None, level: int) -> str:
    parts = current_module.split(".")
    base_parts = parts[:-1]

    if level > 0:
        if level <= len(base_parts):
            prefix = base_parts[: len(base_parts) - level + 1]
        else:
            prefix = []
    else:
        prefix = base_parts

    suffix = []
    if imported_module:
        suffix = imported_module.split(".")

    out = prefix + suffix
    return ".".join([p for p in out if p])


def extract_imports_from_file(path: Path, repo_root: Path = REPO_ROOT) -> Dict[str, Any]:
    source = safe_read(path)
    current_module = module_name_from_path(path, repo_root)

    result: Dict[str, Any] = {
        "module": current_module,
        "imports": [],
        "missing": [],
        "parse_error": None,
    }

    if not source.strip():
        return result

    try:
        tree = ast.parse(source)
    except Exception as e:
        result["parse_error"] = str(e)
        return result

    found: Set[str] = set()
    missing: Set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = str(alias.name).strip()
                if not mod:
                    continue
                found.add(mod)
                if not module_exists(mod, repo_root):
                    missing.add(mod)

        elif isinstance(node, ast.ImportFrom):
            level = int(getattr(node, "level", 0) or 0)
            mod = getattr(node, "module", None)

            if level > 0:
                resolved = resolve_relative_import(current_module, mod, level)
                if resolved:
                    found.add(resolved)
                    if not module_exists(resolved, repo_root):
                        missing.add(resolved)
            else:
                if mod:
                    resolved = str(mod).strip()
                    found.add(resolved)
                    if not module_exists(resolved, repo_root):
                        missing.add(resolved)

    result["imports"] = sorted(found)
    result["missing"] = sorted(missing)
    return result


def list_repo_python_files(repo_root: Path = REPO_ROOT) -> List[Path]:
    files: List[Path] = []

    for path in repo_root.rglob("*.py"):
        if any(part in {".git", "__pycache__", ".venv"} for part in path.parts):
            continue
        files.append(path)

    return sorted(files)


def reverse_edges(edges: Dict[str, List[str]]) -> Dict[str, List[str]]:
    rev: Dict[str, Set[str]] = {}

    for src, targets in edges.items():
        rev.setdefault(src, set())
        for dst in targets:
            rev.setdefault(dst, set()).add(src)

    return {k: sorted(v) for k, v in rev.items()}


def find_dependents(module: str, graph: Dict[str, Any]) -> List[str]:
    rev = graph.get("reverse_edges", {})
    return sorted(rev.get(module, []))


def build_dependency_graph(repo_root: str | Path = ".") -> Dict[str, Any]:
    root = Path(repo_root)
    py_files = list_repo_python_files(root)

    nodes: List[str] = []
    edges: Dict[str, List[str]] = {}
    missing_edges: Dict[str, List[str]] = {}
    parse_errors: Dict[str, str] = {}

    for path in py_files:
        mod = module_name_from_path(path, root)
        nodes.append(mod)

        info = extract_imports_from_file(path, root)
        edges[mod] = info.get("imports", [])
        missing_edges[mod] = info.get("missing", [])

        if info.get("parse_error"):
            parse_errors[mod] = info["parse_error"]

    rev = reverse_edges(edges)

    orphans = sorted(
        mod for mod in nodes
        if not edges.get(mod) and not rev.get(mod)
    )

    graph: Dict[str, Any] = {
        "ok": True,
        "repo_root": str(root),
        "node_count": len(nodes),
        "edge_count": sum(len(v) for v in edges.values()),
        "nodes": sorted(nodes),
        "edges": edges,
        "reverse_edges": rev,
        "missing_edges": missing_edges,
        "orphans": orphans,
        "parse_errors": parse_errors,
    }
    return graph


def save_dependency_graph(graph: Dict[str, Any], report_path: str | Path = REPORT_PATH) -> Dict[str, Any]:
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"ok": True, "path": str(path)}


def build_and_save_dependency_graph(repo_root: str | Path = ".", report_path: str | Path = REPORT_PATH) -> Dict[str, Any]:
    graph = build_dependency_graph(repo_root)
    saved = save_dependency_graph(graph, report_path)
    return {
        "ok": True,
        "graph": graph,
        "saved": saved,
    }


if __name__ == "__main__":
    result = build_and_save_dependency_graph(".")
    print(json.dumps({
        "ok": result["ok"],
        "node_count": result["graph"]["node_count"],
        "edge_count": result["graph"]["edge_count"],
        "orphans": len(result["graph"]["orphans"]),
        "parse_errors": len(result["graph"]["parse_errors"]),
        "report_path": result["saved"]["path"],
    }, indent=2, ensure_ascii=False))
