from runtime_experimental.object_store import load_objects, mark_task_absorbed
from runtime_experimental.github_bridge import is_github_enabled, find_open_issue_by_meta_key

def main():
    if not is_github_enabled():
        print("GITHUB_NOT_ENABLED")
        return

    cleaned = 0

    for task in load_objects():
        if task.get("type") != "task":
            continue

        if str(task.get("status", "")).strip().lower() != "open":
            continue

        meta_key = str(task.get("meta_key", "")).strip()
        if not meta_key:
            continue

        issue = find_open_issue_by_meta_key(meta_key)
        if not issue:
            continue

        mark_task_absorbed(
            str(task.get("id")),
            reason=f"absorbed_by_issue:{issue.get('url', '')}",
        )
        cleaned += 1

    print(f"ANNIHILATED_GHOSTS: {cleaned}")

if __name__ == "__main__":
    main()
