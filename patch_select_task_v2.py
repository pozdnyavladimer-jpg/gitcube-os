from runtime_experimental.github_bridge import find_open_issue_by_meta_key

def is_absorbed(task):
    meta_key = task.get("meta_key")
    if not meta_key:
        return False

    issue = find_open_issue_by_meta_key(meta_key)
    return bool(issue)


def select_task(open_tasks, latest_task_id=None):
    # 1. latest пріоритет
    if latest_task_id:
        for t in open_tasks:
            if t.get("id") == latest_task_id and t.get("status") == "open":
                if not is_absorbed(t):
                    return t

    # 2. filter absorbed
    valid_tasks = [t for t in open_tasks if not is_absorbed(t)]

    # 3. якщо всі absorbed — fallback
    if not valid_tasks:
        return None

    # 4. сортування:
    # спочатку ті, що мають path (реальні задачі)
    with_path = []
    without_path = []

    for t in valid_tasks:
        payload = t.get("payload", {})
        path = str(payload.get("path", "")).strip()
        paths = payload.get("paths")

        if path or (isinstance(paths, list) and len(paths) > 0):
            with_path.append(t)
        else:
            without_path.append(t)

    ordered = with_path + without_path

    return ordered[-1]
