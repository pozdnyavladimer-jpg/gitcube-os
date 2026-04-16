from collections import defaultdict
import ast
import os
from typing import Dict, List, Set, Tuple

from runtime_experimental.object_store import add_object, load_objects
from runtime_experimental.github_bridge import (
    is_github_enabled,
    find_open_issue_by_meta_key,
    normalize_meta_key,
)

IGNORE_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    "reports",
    ".mypy_cache",
    ".pytest_cache",
}

SAFE_MAGE_DIRS = {
    "examples",
    "tests",
    "environments",
    "runtime_experimental",
    "app",
    "core",
    "docs",
}

STRUCTURAL_PROBLEMS = {
    "missing_init",
    "missing_init_group",
    "python_without_docs",
    "package_structure",
    "missing_root_readme",
    "missing_start_here",
    "broken_import_group",
    "empty_directories_group",
    "structural_orphans_group",
}

META_PROBLEMS = {
    "routing_failure",
    "no_target_path",
    "global_block",
}


def safe_read(path: str, max_chars: int = 200000) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read(max_chars)
    except Exception:
        return ""


def has_readme(root: str) -> bool:
    try:
        for name in os.listdir(root):
            if name.lower().startswith("readme"):
                return True
    except Exception:
        return False
    return False


def existing_titles() -> set[str]:
    titles = set()
    for obj in load_objects():
        title = str(obj.get("title", "")).strip().lower()
        if title:
            titles.add(title)
    return titles


def existing_meta_keys() -> set[str]:
    keys = set()
    for obj in load_objects():
        meta_key = str(obj.get("meta_key", "")).strip().lower()
        if meta_key:
            keys.add(meta_key)
    return keys


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def build_resonance_vector(
    *,
    pressure: float,
    flow: float,
    structure: float,
    balance: float,
    law: float,
    future: float,
):
    return {
        "pressure": round(clamp01(pressure), 3),
        "flow": round(clamp01(flow), 3),
        "structure": round(clamp01(structure), 3),
        "balance": round(clamp01(balance), 3),
        "law": round(clamp01(law), 3),
        "future": round(clamp01(future), 3),
    }


def build_meta_key(payload: dict, origin: str) -> str:
    problem = str(payload.get("problem", "generic_problem")).strip().lower()
    path = str(payload.get("path", "")).strip()

    paths = payload.get("paths", [])
    if not isinstance(paths, list):
        paths = []

    first_path = str(paths[0]).strip() if paths else ""
    effective_path = path or first_path

    priority = str(payload.get("priority", "")).strip().lower()
    has_path = "path" if effective_path else "no_path"

    raw = f"{problem}|{has_path}|{priority}|{str(origin).strip().lower()}|{effective_path}"
    return normalize_meta_key(raw)


def make_task(title: str, payload: dict, intensity: float, novelty: float, resonance_vector: dict):
    meta_key = build_meta_key(payload, "repo_analyzer_v7")
    return {
        "type": "task",
        "title": title,
        "origin": "repo_analyzer_v7",
        "status": "open",
        "kind": "task",
        "intensity": intensity,
        "novelty": novelty,
        "payload": payload,
        "resonance_vector": resonance_vector,
        "meta_key": meta_key,
    }


def should_absorb(problem: str, payload: dict, issue_exists: bool) -> bool:
    problem = str(problem or "").strip().lower()

    if not issue_exists:
        return False

    if problem in META_PROBLEMS:
        return True

    if problem in STRUCTURAL_PROBLEMS:
        return False

    return False


def add_task_if_new(
    title: str,
    payload: dict,
    intensity: float,
    novelty: float,
    resonance_vector: dict,
    titles_cache: set[str],
    meta_keys_cache: set[str],
):
    key = title.strip().lower()
    meta_key = build_meta_key(payload, "repo_analyzer_v7")
    problem = str(payload.get("problem", "")).strip().lower()

    if key in titles_cache:
        return False, "duplicate_title"

    if meta_key in meta_keys_cache:
        return False, "duplicate_meta_key_local"

    if is_github_enabled():
        existing_issue = find_open_issue_by_meta_key(meta_key)
        issue_exists = bool(existing_issue)

        if should_absorb(problem, payload, issue_exists):
            return False, f"absorbed_by_issue:{existing_issue.get('url', '')}"

    add_object(make_task(title, payload, intensity, novelty, resonance_vector))
    titles_cache.add(key)
    meta_keys_cache.add(meta_key)
    return True, "created"


def has_debug_prints(content: str) -> bool:
    return "print(" in content


def has_todo(content: str) -> bool:
    return "TODO" in content or "todo" in content


def has_pass_only(content: str) -> bool:
    lines = [x.strip() for x in content.splitlines() if x.strip()]
    return any(line == "pass" for line in lines)


def has_bare_except(content: str) -> bool:
    return "except:" in content


def rel_module_name(root: str, file_path: str) -> str:
    rel_path = os.path.relpath(file_path, root)
    if rel_path.endswith(".py"):
        rel_path = rel_path[:-3]
    parts = [p for p in rel_path.split(os.sep) if p]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def build_module_index(root: str, py_files: List[str]) -> tuple[Set[str], Dict[str, str]]:
    module_names: Set[str] = set()
    module_to_path: Dict[str, str] = {}

    for rel_path in py_files:
        full = os.path.join(root, rel_path)
        mod = rel_module_name(root, full)
        if mod:
            module_names.add(mod)
            module_to_path[mod] = rel_path

    return module_names, module_to_path


def top_level_package_of(rel_path: str) -> str:
    parts = [p for p in rel_path.split("/") if p]
    return parts[0] if parts else ""


def parse_import_targets(content: str) -> List[str]:
    targets: List[str] = []
    try:
        tree = ast.parse(content)
    except Exception:
        return targets

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = str(alias.name).strip()
                if name:
                    targets.append(name)
        elif isinstance(node, ast.ImportFrom):
            mod = str(node.module or "").strip()
            if mod:
                targets.append(mod)

    return targets


def likely_local_import(target: str, known_modules: Set[str], known_top_levels: Set[str]) -> bool:
    if not target:
        return False
    head = target.split(".", 1)[0]
    return target in known_modules or head in known_top_levels


def import_resolves_locally(target: str, known_modules: Set[str]) -> bool:
    if target in known_modules:
        return True
    parts = target.split(".")
    while len(parts) > 1:
        parts = parts[:-1]
        candidate = ".".join(parts)
        if candidate in known_modules:
            return True
    return False


def analyze_repo(root: str = "."):
    titles_cache = existing_titles()
    meta_keys_cache = existing_meta_keys()

    created = 0
    suppressed = 0
    scanned = 0

    py_files: List[str] = []
    md_files: List[str] = []
    big_files: List[Tuple[str, int]] = []
    empty_dirs: List[str] = []

    mage_missing_init_dirs: List[str] = []
    general_missing_init_dirs: List[str] = []

    debug_print_files: List[str] = []
    todo_files: List[str] = []
    pass_files: List[str] = []
    bare_except_files: List[str] = []

    visible_dirs_with_py: Dict[str, List[str]] = {}
    root_level_py: List[str] = []

    for current_root, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        rel_root = os.path.relpath(current_root, root)
        if rel_root == ".":
            rel_root = ""

        visible_files = [f for f in files if not f.startswith(".")]
        visible_dirs = [d for d in dirs if not d.startswith(".")]

        if rel_root and not visible_files and not visible_dirs:
            empty_dirs.append(rel_root)

        py_in_dir = [f for f in files if f.endswith(".py") and not f.startswith(".")]
        if py_in_dir:
            visible_dirs_with_py[rel_root or "."] = py_in_dir
            if rel_root == "":
                root_level_py.extend([os.path.join(rel_root, f).lstrip("./") for f in py_in_dir])
            if "__init__.py" not in files:
                top_dir = rel_root.split("/", 1)[0] if rel_root else ""
                if top_dir in SAFE_MAGE_DIRS:
                    mage_missing_init_dirs.append(rel_root or ".")
                else:
                    general_missing_init_dirs.append(rel_root or ".")

        for file_name in files:
            if file_name.startswith("."):
                continue

            full_path = os.path.join(current_root, file_name)
            rel_path = os.path.relpath(full_path, root).replace("\\", "/")

            scanned += 1

            try:
                size = os.path.getsize(full_path)
            except Exception:
                size = 0

            if size > 50000:
                big_files.append((rel_path, size))

            if file_name.endswith(".py"):
                py_files.append(rel_path)
                content = safe_read(full_path)

                if has_debug_prints(content):
                    debug_print_files.append(rel_path)

                if has_todo(content):
                    todo_files.append(rel_path)

                if has_pass_only(content):
                    pass_files.append(rel_path)

                if has_bare_except(content):
                    bare_except_files.append(rel_path)

            if file_name.lower().endswith(".md"):
                md_files.append(rel_path)

    module_names, module_to_path = build_module_index(root, py_files)
    known_top_levels = {m.split(".", 1)[0] for m in module_names if m}

    broken_imports: List[Dict[str, str]] = []
    structural_orphans: List[str] = []

    for rel_path in py_files:
        full_path = os.path.join(root, rel_path)
        content = safe_read(full_path)

        top_dir = top_level_package_of(rel_path)
        is_root_level = "/" not in rel_path

        if is_root_level and rel_path not in {
            "repo_analyzer.py",
            "router.py",
            "run.py",
            "run_loop.py",
            "status.py",
            "v_bridge.py",
            "v_clock.py",
            "viewer.py",
            "actor_executor.py",
            "setup_vcore.sh",
            "run.sh",
            "run_loop.sh",
        }:
            structural_orphans.append(rel_path)

        if top_dir and top_dir not in SAFE_MAGE_DIRS and rel_path.endswith(".py"):
            dir_name = os.path.dirname(rel_path)
            if dir_name and not os.path.exists(os.path.join(root, dir_name, "__init__.py")):
                if rel_path not in structural_orphans:
                    structural_orphans.append(rel_path)

        imports = parse_import_targets(content)
        for target in imports:
            if likely_local_import(target, module_names, known_top_levels):
                if not import_resolves_locally(target, module_names):
                    broken_imports.append({
                        "file": rel_path,
                        "import": target,
                    })

    if mage_missing_init_dirs:
        rv = build_resonance_vector(
            pressure=0.68,
            flow=0.24,
            structure=0.12,
            balance=0.34,
            law=0.20,
            future=0.84,
        )
        ok, reason = add_task_if_new(
            "MAGE: Repair safe package markers",
            {
                "problem": "missing_init_group",
                "paths": mage_missing_init_dirs[:30],
                "count": len(mage_missing_init_dirs),
                "priority": "high",
                "executor_hint": "MAGE",
            },
            0.86,
            0.76,
            rv,
            titles_cache,
            meta_keys_cache,
        )
        created += int(ok)
        suppressed += int(not ok)

    if general_missing_init_dirs:
        rv = build_resonance_vector(
            pressure=0.73,
            flow=0.18,
            structure=0.14,
            balance=0.34,
            law=0.22,
            future=0.76,
        )
        ok, reason = add_task_if_new(
            "Review Python package structure",
            {
                "problem": "package_structure",
                "paths": general_missing_init_dirs[:30],
                "count": len(general_missing_init_dirs),
                "priority": "high",
                "executor_hint": "MAGE",
            },
            0.88,
            0.74,
            rv,
            titles_cache,
            meta_keys_cache,
        )
        created += int(ok)
        suppressed += int(not ok)

    if broken_imports:
        broken_paths = sorted({x["file"] for x in broken_imports})
        rv = build_resonance_vector(
            pressure=0.82,
            flow=0.22,
            structure=0.16,
            balance=0.31,
            law=0.24,
            future=0.71,
        )
        ok, reason = add_task_if_new(
            "Repair broken imports across repo",
            {
                "problem": "broken_import_group",
                "paths": broken_paths[:30],
                "count": len(broken_imports),
                "examples": broken_imports[:10],
                "priority": "high",
                "executor_hint": "MAGE",
            },
            0.90,
            0.78,
            rv,
            titles_cache,
            meta_keys_cache,
        )
        created += int(ok)
        suppressed += int(not ok)

    if structural_orphans:
        rv = build_resonance_vector(
            pressure=0.66,
            flow=0.18,
            structure=0.22,
            balance=0.37,
            law=0.26,
            future=0.74,
        )
        ok, reason = add_task_if_new(
            "Repair structural orphans across repo",
            {
                "problem": "structural_orphans_group",
                "paths": sorted(structural_orphans)[:30],
                "count": len(structural_orphans),
                "priority": "high",
                "executor_hint": "MAGE",
            },
            0.82,
            0.73,
            rv,
            titles_cache,
            meta_keys_cache,
        )
        created += int(ok)
        suppressed += int(not ok)

    if not has_readme(root):
        rv = build_resonance_vector(
            pressure=0.82,
            flow=0.20,
            structure=0.18,
            balance=0.35,
            law=0.45,
            future=0.88,
        )
        ok, reason = add_task_if_new(
            "Add root README",
            {
                "problem": "missing_root_readme",
                "path": "README.md",
                "priority": "high",
                "executor_hint": "MAGE",
            },
            0.92,
            0.80,
            rv,
            titles_cache,
            meta_keys_cache,
        )
        created += int(ok)
        suppressed += int(not ok)

    if not os.path.exists(os.path.join(root, "START_HERE.md")):
        rv = build_resonance_vector(
            pressure=0.76,
            flow=0.22,
            structure=0.24,
            balance=0.40,
            law=0.48,
            future=0.82,
        )
        ok, reason = add_task_if_new(
            "Add START_HERE guide",
            {
                "problem": "missing_start_here",
                "path": "START_HERE.md",
                "priority": "high",
                "executor_hint": "MAGE",
            },
            0.88,
            0.78,
            rv,
            titles_cache,
            meta_keys_cache,
        )
        created += int(ok)
        suppressed += int(not ok)

    if empty_dirs:
        rv = build_resonance_vector(
            pressure=0.38,
            flow=0.10,
            structure=0.25,
            balance=0.55,
            law=0.56,
            future=0.42,
        )
        ok, reason = add_task_if_new(
            "Review empty directories",
            {
                "problem": "empty_directories_group",
                "paths": sorted(empty_dirs)[:30],
                "count": len(empty_dirs),
                "priority": "medium",
                "executor_hint": "MAGE",
            },
            0.64,
            0.61,
            rv,
            titles_cache,
            meta_keys_cache,
        )
        created += int(ok)
        suppressed += int(not ok)

    if big_files:
        rv = build_resonance_vector(
            pressure=0.63,
            flow=0.28,
            structure=0.42,
            balance=0.46,
            law=0.52,
            future=0.67,
        )
        ok, reason = add_task_if_new(
            "Review large files across repo",
            {
                "problem": "large_files_group",
                "files": [{"path": p, "size": s} for p, s in big_files[:20]],
                "paths": [p for p, _ in big_files[:20]],
                "count": len(big_files),
                "priority": "medium",
            },
            0.78,
            0.70,
            rv,
            titles_cache,
            meta_keys_cache,
        )
        created += int(ok)
        suppressed += int(not ok)

    if len(py_files) > 0 and len(md_files) == 0:
        rv = build_resonance_vector(
            pressure=0.61,
            flow=0.18,
            structure=0.26,
            balance=0.43,
            law=0.47,
            future=0.77,
        )
        ok, reason = add_task_if_new(
            "MAGE: Add project documentation bootstrap",
            {
                "problem": "python_without_docs",
                "py_count": len(py_files),
                "path": "README.md",
                "priority": "medium",
                "executor_hint": "MAGE",
            },
            0.76,
            0.72,
            rv,
            titles_cache,
            meta_keys_cache,
        )
        created += int(ok)
        suppressed += int(not ok)

    if todo_files:
        rv = build_resonance_vector(
            pressure=0.74,
            flow=0.36,
            structure=0.33,
            balance=0.38,
            law=0.42,
            future=0.71,
        )
        ok, reason = add_task_if_new(
            "Resolve TODO markers across repo",
            {
                "problem": "todo_group",
                "paths": sorted(todo_files)[:30],
                "count": len(todo_files),
                "priority": "medium",
            },
            0.79,
            0.73,
            rv,
            titles_cache,
            meta_keys_cache,
        )
        created += int(ok)
        suppressed += int(not ok)

    if debug_print_files:
        rv = build_resonance_vector(
            pressure=0.58,
            flow=0.72,
            structure=0.66,
            balance=0.60,
            law=0.63,
            future=0.54,
        )
        ok, reason = add_task_if_new(
            "Refactor debug prints across repo",
            {
                "problem": "debug_prints_group",
                "paths": sorted(debug_print_files)[:30],
                "count": len(debug_print_files),
                "priority": "medium",
            },
            0.74,
            0.67,
            rv,
            titles_cache,
            meta_keys_cache,
        )
        created += int(ok)
        suppressed += int(not ok)

    if pass_files:
        rv = build_resonance_vector(
            pressure=0.67,
            flow=0.30,
            structure=0.24,
            balance=0.36,
            law=0.28,
            future=0.76,
        )
        ok, reason = add_task_if_new(
            "Review pass blocks across repo",
            {
                "problem": "pass_blocks_group",
"paths": sorted(pass_files)[:30],
                "count": len(pass_files),
                "priority": "medium",
            },
            0.81,
            0.75,
            rv,
            titles_cache,
            meta_keys_cache,
        )
        created += int(ok)
        suppressed += int(not ok)


    # =========================
    # TOPOLOGY LAYER v2.1
    # =========================
# FIXME broken import:     from collections import defaultdict

    graph_out = defaultdict(set)
    graph_in = defaultdict(set)

    for rel_path in py_files:
        full_path = os.path.join(root, rel_path)
        content = safe_read(full_path)
        module = rel_module_name(root, full_path)
        if not module:
            continue

        imports = parse_import_targets(content)
        for target in imports:
            if likely_local_import(target, module_names, known_top_levels):
                if import_resolves_locally(target, module_names):
                    graph_out[module].add(target)
                    graph_in[target].add(module)

    isolated_modules = []
    for m in sorted(module_names):
        if not graph_out[m] and not graph_in[m]:
            isolated_modules.append(m)

    if isolated_modules:
        rv = build_resonance_vector(
            pressure=0.55,
            flow=0.12,
            structure=0.22,
            balance=0.40,
            law=0.38,
            future=0.70,
        )
        ok, reason = add_task_if_new(
            "Detect isolated modules",
            {
                "problem": "isolated_module_group",
                "paths": sorted(isolated_modules)[:20],
                "count": len(isolated_modules),
                "priority": "medium",
                "executor_hint": "MAGE",
                "topology_context": {
                    "cluster_id": "isolated",
                    "module_names": sorted(isolated_modules)[:20],
                    "neighbors": {},
                    "in_degree": {m: 0 for m in sorted(isolated_modules)[:20]},
                    "out_degree": {m: 0 for m in sorted(isolated_modules)[:20]},
                },
            },
            0.72,
            0.68,
            rv,
            titles_cache,
            meta_keys_cache,
        )
        created += int(ok)
        suppressed += int(not ok)

    overcoupled = []
    for m in sorted(module_names):
        in_deg = len(graph_in[m])
        out_deg = len(graph_out[m])
        if in_deg + out_deg >= 10:
            overcoupled.append({
                "module": m,
                "in_degree": in_deg,
                "out_degree": out_deg,
                "neighbors": sorted(graph_out[m])[:10],
            })

    if overcoupled:
        rv = build_resonance_vector(
            pressure=0.78,
            flow=0.32,
            structure=0.41,
            balance=0.35,
            law=0.44,
            future=0.66,
        )
        ok, reason = add_task_if_new(
            "Detect overcoupled modules",
            {
                "problem": "overcoupled_module_group",
                "paths": [x["module"] for x in overcoupled[:15]],
                "count": len(overcoupled),
                "examples": overcoupled[:10],
                "priority": "high",
                "executor_hint": "MAGE",
                "topology_context": {
                    "cluster_id": "overcoupled",
                    "module_names": [x["module"] for x in overcoupled[:15]],
                    "neighbors": {x["module"]: x["neighbors"] for x in overcoupled[:10]},
                    "in_degree": {x["module"]: x["in_degree"] for x in overcoupled[:10]},
                    "out_degree": {x["module"]: x["out_degree"] for x in overcoupled[:10]},
                },
            },
            0.84,
            0.76,
            rv,
            titles_cache,
            meta_keys_cache,
        )
        created += int(ok)
        suppressed += int(not ok)

    # =========================
    # BRIDGE LAYER v2.2
    # =========================

    def module_cluster_name(module: str) -> str:
        if module.startswith("core."):
            return "core"
        if module.startswith("app."):
            return "app"
        if module.startswith("runtime_experimental."):
            return "runtime_experimental"
        if module.startswith("examples."):
            return "examples"
        if module.startswith("tests."):
            return "tests"
        if module.startswith("environments."):
            return "environments"
        if module.startswith("docs."):
            return "docs"
        if "." not in module:
            return module
        return module.split(".", 1)[0]

    cluster_members = {}
    for m in sorted(module_names):
        c = module_cluster_name(m)
        cluster_members.setdefault(c, []).append(m)

    missing_bridges = []

    preferred_targets = ["core", "app", "runtime_experimental"]

    for module in sorted(isolated_modules):
        source_cluster = module_cluster_name(module)

        target_cluster = None
        for candidate in preferred_targets:
            if candidate != source_cluster and candidate in cluster_members:
                target_cluster = candidate
                break

        if not target_cluster:
            continue

        target_examples = cluster_members.get(target_cluster, [])[:5]

        missing_bridges.append({
            "module": module,
            "from_cluster": source_cluster,
            "to_cluster": target_cluster,
            "suggested_neighbors": target_examples,
        })

    if missing_bridges:
        rv = build_resonance_vector(
            pressure=0.64,
            flow=0.22,
            structure=0.31,
            balance=0.39,
            law=0.36,
            future=0.74,
        )

        ok, reason = add_task_if_new(
            "Detect missing bridges across clusters",
            {
                "problem": "missing_bridge_group",
                "paths": [x["module"] for x in missing_bridges[:20]],
                "count": len(missing_bridges),
                "examples": missing_bridges[:10],
                "priority": "high",
                "executor_hint": "MAGE",
                "topology_context": {
                    "cluster_id": "bridges",
                    "module_names": [x["module"] for x in missing_bridges[:20]],
                    "neighbors": {x["module"]: x["suggested_neighbors"] for x in missing_bridges[:10]},
                    "bridges": missing_bridges[:10],
                },
            },
            0.80,
            0.77,
            rv,
            titles_cache,
            meta_keys_cache,
        )
        created += int(ok)
        suppressed += int(not ok)
    print("ANALYZER_DONE")
    print("FILES_SCANNED:", scanned)
    print("PY_FILES:", len(py_files))
    print("BROKEN_IMPORTS:", len(broken_imports))
    print("MISSING_INIT_DIRS_SAFE:", len(mage_missing_init_dirs))
    print("MISSING_INIT_DIRS_GENERAL:", len(general_missing_init_dirs))
    print("STRUCTURAL_ORPHANS:", len(structural_orphans))
    print("EMPTY_DIRS:", len(empty_dirs))
    print("DEBUG_PRINT_FILES:", len(debug_print_files))
    print("TODO_FILES:", len(todo_files))
    print("PASS_BLOCK_FILES:", len(pass_files))
    print("BARE_EXCEPT_FILES:", len(pass_files))
    print("TASKS_CREATED:", created)
    print("TASKS_SUPPRESSED:", suppressed)


if __name__ == "__main__":
    analyze_repo(".")


def refresh_tasks_from_analyzer(root: str = "."):
    return analyze_repo(root)
