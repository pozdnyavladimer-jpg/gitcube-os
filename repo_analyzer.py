import os
from runtime_experimental.object_store import add_object, load_objects

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


def make_task(title: str, payload: dict, intensity: float, novelty: float):
    return {
        "type": "task",
        "title": title,
        "origin": "repo_analyzer_v2",
        "status": "open",
        "kind": "task",
        "intensity": intensity,
        "novelty": novelty,
        "payload": payload,
    }


def add_task_if_new(title: str, payload: dict, intensity: float, novelty: float, titles_cache: set[str]):
    key = title.strip().lower()
    if key in titles_cache:
        return False

    add_object(make_task(title, payload, intensity, novelty))
    titles_cache.add(key)
    return True


def analyze_repo(root: str = "."):
    titles_cache = existing_titles()
    created = 0

    py_files = []
    md_files = []
    big_files = []
    empty_dirs = []
    missing_init_dirs = []
    todo_files = []
    debug_print_files = []

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

            try:
                size = os.path.getsize(full_path)
            except Exception:
                size = 0

            if size > 50000:
                big_files.append((rel_path, size))

            if file_name.endswith(".py"):
                py_files.append(rel_path)
                content = safe_read(full_path)

                if "TODO" in content:
                    todo_files.append(rel_path)

                    debug_print_files.append(rel_path)

            if file_name.lower().endswith(".md"):
                md_files.append(rel_path)

    if not has_readme(root):
        if add_task_if_new(
            "Add root README",
            {"problem": "missing_root_readme", "path": "README.md", "priority": "high"},
            0.92,
            0.80,
            titles_cache,
        ):
            created += 1

    if not os.path.exists(os.path.join(root, "START_HERE.md")):
        if add_task_if_new(
            "Add START_HERE guide",
            {"problem": "missing_start_here", "path": "START_HERE.md", "priority": "high"},
            0.88,
            0.78,
            titles_cache,
        ):
            created += 1

    if missing_init_dirs:
        if add_task_if_new(
            "Review Python package structure",
            {
                "problem": "missing_init_group",
                "paths": missing_init_dirs[:20],
                "count": len(missing_init_dirs),
                "priority": "high",
            },
            0.86,
            0.74,
            titles_cache,
        ):
            created += 1

    if big_files:
        if add_task_if_new(
            "Review large files across repo",
            {
                "problem": "large_files_group",
                "files": [{"path": p, "size": s} for p, s in big_files[:20]],
                "count": len(big_files),
                "priority": "medium",
            },
            0.78,
            0.70,
            titles_cache,
        ):
            created += 1

    if empty_dirs:
        if add_task_if_new(
            "Review empty directories",
            {
                "problem": "empty_directories_group",
                "paths": empty_dirs[:20],
                "count": len(empty_dirs),
                "priority": "low",
            },
            0.62,
            0.60,
            titles_cache,
        ):
            created += 1

    if len(py_files) > 0 and len(md_files) == 0:
        if add_task_if_new(
            "Add project documentation",
            {
                "problem": "python_without_docs",
                "py_count": len(py_files),
                "priority": "medium",
            },
            0.76,
            0.72,
            titles_cache,
        ):
            created += 1

    if todo_files:
        if add_task_if_new(
            "Resolve TODO markers across repo",
            {
                "problem": "todo_group",
                "paths": todo_files[:30],
                "count": len(todo_files),
                "priority": "medium",
            },
            0.79,
            0.73,
            titles_cache,
        ):
            created += 1

    if debug_print_files:
        if add_task_if_new(
            "Refactor debug prints across repo",
            {
                "problem": "debug_prints_group",
                "paths": debug_print_files[:30],
                "count": len(debug_print_files),
                "priority": "medium",
            },
            0.74,
            0.67,
            titles_cache,
        ):
            created += 1



if __name__ == "__main__":
    analyze_repo(".")
