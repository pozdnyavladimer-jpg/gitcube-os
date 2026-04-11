from runtime_experimental.object_store import load_objects

def get_open_tasks():
    tasks = []

    for obj in load_objects():
        if obj.get("type") != "task":
            continue

        status = str(obj.get("status", "")).strip().lower()

        if status == "open":
            tasks.append(obj)

    return tasks
