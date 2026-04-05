import json
import os

PATH = "objects.json"


# ===== CORE =====

def load_objects():
    if not os.path.exists(PATH):
        return []
    with open(PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_objects(data):
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _next_id(data):
    nums = []
    for o in data:
        i = str(o.get("id", ""))
        if i.startswith("task_") and i.split("_")[-1].isdigit():
            nums.append(int(i.split("_")[-1]))
    return f"task_{max(nums)+1 if nums else 1}"


# ===== CREATE =====

def add_object(obj):
    data = load_objects()

    if not obj.get("id"):
        obj["id"] = _next_id(data)

    obj.setdefault("type", "task")
    obj.setdefault("status", "open")
    obj.setdefault("published_to_github", False)
    obj.setdefault("github_url", "")

    data.append(obj)
    save_objects(data)
    return obj


# ===== READ =====

def get_open_tasks():
    return [
        o for o in load_objects()
        if o.get("type") == "task" and o.get("status") == "open"
    ]


def get_open():
    return get_open_tasks()


# ===== UPDATE =====

def mark_task_done(task_id, path=""):
    data = load_objects()
    updated = None

    for o in data:
        if o.get("id") == task_id:
            o["status"] = "done"
            o["result_path"] = path
            updated = o

    save_objects(data)
    return updated


def mark_done(task_id, path=""):
    return mark_task_done(task_id, path)


def mark_task_published(task_id, url):
    data = load_objects()
    updated = None

    for o in data:
        if o.get("id") == task_id:
            o["published_to_github"] = True
            o["github_url"] = url
            updated = o

    save_objects(data)
    return updated


def mark_published(task_id, url):
    return mark_task_published(task_id, url)
