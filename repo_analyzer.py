import os
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

TEXT_EXTENSIONS = {
    ".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml",
    ".js", ".ts", ".tsx", ".jsx", ".css", ".html", ".sh"
}


def safe_read(path: str, max_chars: int = 4000) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read(max_chars)
    except Exception:
        return ""


def has_readme(root: str) -> bool:
    for name in os.listdir(root):
        if name.lower().startswith("readme"):
            return True
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
        payload = obj.get("payload", {}) or {}
        problem = str(payload.get("problem", "")).strip().lower()
        path = str(payload.get("path", "")).strip()
        priority = str(payload.get("priority", "")).strip().lower()
        origin = str(obj.get("origin", "")).strip().lower()

        if not problem:
            continue

        has_path = "path" if path else "no_path"
        raw = f"{problem}|{has_path}|{priority}|{origin}"
        keys.add(normalize_meta_key(raw))
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
    priority = str(payload.get("priority", "")).strip().lower()
    has_path = "path" if path else "no_path"
    raw = f"{problem}|{has_path}|{priority}|{str(origin).strip().lower()}"
    return normalize_meta_key(raw)


def make_task(title: str, payload: dict, intensity: float, novelty: float, resonance_vector: dict):
    return {
        "type": "task",
        "title": title,
        "origin": "repo_analyzer_v3",
        "status": "open",
        "kind": "task",
        "intensity": intensity,
        "novelty": novelty,
        "payload": payload,
        "resonance_vector": resonance_vector,
        "meta_key": build_meta_key(payload, "repo_analyzer_v3"),
    }


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
    meta_key = build_meta_key(payload, "repo_analyzer_v3")

    if key in titles_cache:
        return False, "duplicate_title"

    if meta_key in meta_keys_cache:
        return False, "duplicate_meta_key_local"

    if is_github_enabled():
        existing_issue = find_open_issue_by_meta_key(meta_key)
        if existing_issue:
            return False, f"duplicate_meta_key_issue:{existing_issue.get('url', '')}"

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


def analyze_repo(root: str = "."):
    titles_cache = existing_titles()
    meta_keys_cache = existing_meta_keys()
    created = 0
    suppressed = 0

    py_files = []
    md_files = []
    big_files = []
    empty_dirs = []
    missing_init_dirs = []

    debug_print_files = []
    todo_files = []
    pass_files = []
    bare_except_files = []

    scanned = 0

    for current_root, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        rel_root = os.path.relpath(current_root, root)
        if rel_root == ".":
            rel_root = ""

        visible_files = [f for f in files if not f.startswith(".")]
        visible_dirs = [d for d in dirs if not d.startswith(".")]

        if rel_root and not visible_files and not visible_dirs:
            empty_dirs.append(rel_root)

        py_in_dir = [f for f in files if f.endswith(".py")]
        if py_in_dir and "__init__.py" not in files:
            missing_init_dirs.append(rel_root or ".")

        for file_name in files:
            if file_name.startswith("."):
                continue

            full_path = os.path.join(current_root, file_name)
            rel_path = os.path.relpath(full_path, root)

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

    if not has_readme(root):
        rv = build_resonance_vector(
            pressure=0.82, flow=0.20, structure=0.18,
            balance=0.35, law=0.45, future=0.88,
        )
        ok, reason = add_task_if_new(
            "Add root README",
            {"problem": "missing_root_readme", "path": "README.md", "priority": "high"},
            0.92,
            0.80,
            rv,
            titles_cache,
            meta_keys_cache,
        )
        if ok:
            created += 1
        else:
            suppressed += 1

    if not os.path.exists(os.path.join(root, "START_HERE.md")):
        rv = build_resonance_vector(
            pressure=0.76, flow=0.22, structure=0.24,
            balance=0.40, law=0.48, future=0.82,
        )
        ok, reason = add_task_if_new(
            "Add START_HERE guide",
            {"problem": "missing_start_here", "path": "START_HERE.md", "priority": "high"},
            0.88,
            0.78,
            rv,
            titles_cache,
            meta_keys_cache,
        )
        if ok:
            created += 1
        else:
            suppressed += 1

    if missing_init_dirs:
        rv = build_resonance_vector(
            pressure=0.71, flow=0.18, structure=0.22,
            balance=0.34, law=0.26, future=0.73,
        )
        ok, reason = add_task_if_new(
            "Review Python package structure",
            {
                "problem": "missing_init_group",
                "paths": missing_init_dirs[:20],
                "count": len(missing_init_dirs),
                "priority": "high",
            },
            0.86,
            0.74,
            rv,
            titles_cache,
            meta_keys_cache,
        )
        if ok:
            created += 1
        else:
            suppressed += 1

    if big_files:
        rv = build_resonance_vector(
            pressure=0.63, flow=0.28, structure=0.42,
            balance=0.46, law=0.52, future=0.67,
        )
        ok, reason = add_task_if_new(
            "Review large files across repo",
            {
                "problem": "large_files_group",
                "files": [{"path": p, "size": s} for p, s in big_files[:20]],
                "count": len(big_files),
                "priority": "medium",
            },
            0.78,
            0.70,
            rv,
            titles_cache,
            meta_keys_cache,
        )
        if ok:
            created += 1
        else:
            suppressed += 1

    if empty_dirs:
        rv = build_resonance_vector(
            pressure=0.35, flow=0.12, structure=0.30,
            balance=0.55, law=0.60, future=0.41,
        )
        ok, reason = add_task_if_new(
            "Review empty directories",
            {
                "problem": "empty_directories_group",
                "paths": empty_dirs[:20],
                "count": len(empty_dirs),
                "priority": "low",
            },
            0.62,
            0.60,
            rv,
            titles_cache,
            meta_keys_cache,
        )
        if ok:
            created += 1
        else:
            suppressed += 1

    if len(py_files) > 0 and len(md_files) == 0:
        rv = build_resonance_vector(
            pressure=0.61, flow=0.18, structure=0.26,
            balance=0.43, law=0.47, future=0.77,
        )
        ok, reason = add_task_if_new(
            "Add project documentation",
            {
                "problem": "python_without_docs",
                "py_count": len(py_files),
                "priority": "medium",
            },
            0.76,
            0.72,
            rv,
            titles_cache,
            meta_keys_cache,
        )
        if ok:
            created += 1
        else:
            suppressed += 1

    if todo_files:
        rv = build_resonance_vector(
            pressure=0.74, flow=0.36, structure=0.33,
            balance=0.38, law=0.42, future=0.71,
        )
        ok, reason = add_task_if_new(
            "Resolve TODO markers across repo",
            {
                "problem": "todo_group",
                "paths": todo_files[:30],
                "count": len(todo_files),
                "priority": "medium",
            },
            0.79,
            0.73,
            rv,
            titles_cache,
            meta_keys_cache,
        )
        if ok:
            created += 1
        else:
            suppressed += 1

    if debug_print_files:
        rv = build_resonance_vector(
            pressure=0.58, flow=0.72, structure=0.66,
            balance=0.60, law=0.63, future=0.54,
        )
        ok, reason = add_task_if_new(
            "Refactor debug prints across repo",
            {
                "problem": "debug_prints_group",
                "paths": debug_print_files[:30],
                "count": len(debug_print_files),
                "priority": "medium",
            },
            0.74,
            0.67,
            rv,
            titles_cache,
            meta_keys_cache,
        )
        if ok:
            created += 1
        else:
            suppressed += 1

    if pass_files:
        rv = build_resonance_vector(
            pressure=0.67, flow=0.30, structure=0.24,
            balance=0.36, law=0.28, future=0.76,
        )
        ok, reason = add_task_if_new(
            "Review pass blocks across repo",
            {
                "problem": "pass_blocks_group",
                "paths": pass_files[:30],
                "count": len(pass_files),
                "priority": "medium",
            },
            0.77,
            0.71,
            rv,
            titles_cache,
            meta_keys_cache,
        )
        if ok:
            created += 1
        else:
            suppressed += 1

    if bare_except_files:
        rv = build_resonance_vector(
            pressure=0.72, flow=0.26, structure=0.31,
            balance=0.33, law=0.18, future=0.68,
        )
        ok, reason = add_task_if_new(
            "Review bare except blocks across repo",
            {
                "problem": "bare_except_group",
                "paths": bare_except_files[:30],
                "count": len(bare_except_files),
                "priority": "medium",
            },
            0.81,
            0.75,
            rv,
            titles_cache,
            meta_keys_cache,
        )
        if ok:
            created += 1
        else:
            suppressed += 1

    print("ANALYZER_DONE")
    print("FILES_SCANNED:", scanned)
    print("DEBUG_PRINT_FILES:", len(debug_print_files))
    print("TODO_FILES:", len(todo_files))
    print("PASS_BLOCK_FILES:", len(pass_files))
    print("BARE_EXCEPT_FILES:", len(bare_except_files))
    print("TASKS_CREATED:", created)
    print("TASKS_SUPPRESSED:", suppressed)


if __name__ == "__main__":
    analyze_repo(".")
