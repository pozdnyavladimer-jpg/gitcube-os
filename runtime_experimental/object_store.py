import json
import os
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional

PATH = "objects.json"


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def load_objects() -> List[Dict[str, Any]]:
    if not os.path.exists(PATH):
        return []
    with open(PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
        except Exception:
            return []


def save_objects(data: List[Dict[str, Any]]) -> None:
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _next_id(data: List[Dict[str, Any]]) -> str:
    nums = []
    for o in data:
        obj_id = str(o.get("id", ""))
        if obj_id.startswith("task_"):
            tail = obj_id.split("_")[-1]
            if tail.isdigit():
                nums.append(int(tail))
    return f"task_{max(nums) + 1 if nums else 1}"


def get_task_by_id(task_id: str) -> Optional[Dict[str, Any]]:
    for obj in load_objects():
        if str(obj.get("id", "")) == str(task_id):
            return obj
    return None


def get_latest_task() -> Optional[Dict[str, Any]]:
    tasks = [o for o in load_objects() if o.get("type") == "task"]
    if not tasks:
        return None

    def sort_key(x):
        obj_id = str(x.get("id", "task_0"))
        tail = obj_id.split("_")[-1]
        return int(tail) if tail.isdigit() else 0

    tasks.sort(key=sort_key)
    return tasks[-1]


def get_latest_open_task() -> Optional[Dict[str, Any]]:
    tasks = [
        o for o in load_objects()
        if o.get("type") == "task" and o.get("status") == "open"
    ]
    if not tasks:
        return None

    def sort_key(x):
        obj_id = str(x.get("id", "task_0"))
        tail = obj_id.split("_")[-1]
        return int(tail) if tail.isdigit() else 0

    tasks.sort(key=sort_key)
    return tasks[-1]


def add_object(obj: Dict[str, Any]) -> Dict[str, Any]:
    data = load_objects()

    if not obj.get("id"):
        obj["id"] = _next_id(data)

    obj.setdefault("type", "task")
    obj.setdefault("status", "open")
    obj.setdefault("created_at", now_iso())
    obj.setdefault("updated_at", now_iso())
    obj.setdefault("result_path", "")
    obj.setdefault("execution_reason", "")

    data.append(obj)
    save_objects(data)
    return obj


def get_open_tasks():
    return [
        o for o in load_objects()
        if o.get("type") == "task" and o.get("status") == "open"
    ]


def update_task_status(task_id, status, result_path="", reason=""):
    data = load_objects()

    for o in data:
        if str(o.get("id")) != str(task_id):
            continue

        o["status"] = status
        o["updated_at"] = now_iso()
        o["result_path"] = result_path
        o["execution_reason"] = reason

    save_objects(data)


def mark_task_in_progress(task_id, path=""):
    update_task_status(task_id, "in_progress", path)


def mark_task_done(task_id, path="", reason=""):
    update_task_status(task_id, "done", path, reason)


def mark_task_skipped(task_id, path="", reason=""):
    update_task_status(task_id, "skipped", path, reason)


def mark_task_failed(task_id, path="", reason=""):
    update_task_status(task_id, "failed", path, reason)


def mark_task_published(task_id, url, path="", reason=""):
    data = load_objects()

    for o in data:
        if str(o.get("id")) != str(task_id):
            continue

        o["status"] = "published"
        o["github_url"] = url
        o["published_to_github"] = True
        o["updated_at"] = now_iso()
        o["result_path"] = path
        o["execution_reason"] = reason

    save_objects(data)
