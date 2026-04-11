import json
import os
import time
from typing import List, Dict, Any

STORE_PATH = "objects.json"


def load_objects() -> List[Dict[str, Any]]:
    if not os.path.exists(STORE_PATH):
        return []

    try:
        with open(STORE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception:
        return []


def save_objects(objects: List[Dict[str, Any]]):
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(objects, f, indent=2, ensure_ascii=False)


def _generate_id(objects: List[Dict[str, Any]]) -> str:
    max_id = 0
    for obj in objects:
        obj_id = str(obj.get("id", "task_0"))
        tail = obj_id.split("_")[-1]
        if tail.isdigit():
            max_id = max(max_id, int(tail))
    return f"task_{max_id + 1}"


def add_object(obj: Dict[str, Any]) -> Dict[str, Any]:
    objects = load_objects()

    new_obj = dict(obj)

    if "id" not in new_obj:
        new_obj["id"] = _generate_id(objects)

    if "created_at" not in new_obj:
        new_obj["created_at"] = int(time.time())

    if "status" not in new_obj:
        new_obj["status"] = "open"

    objects.append(new_obj)
    save_objects(objects)

    return new_obj


def get_open_tasks() -> List[Dict[str, Any]]:
    """
    🔥 FIX: максимально tolerant фільтр
    бачить всі open задачі незалежно від формату
    """
    tasks = []

    for obj in load_objects():
        if str(obj.get("type", "")).strip().lower() != "task":
            continue

        status = str(obj.get("status", "")).strip().lower()

        # 🔥 tolerant:
        if status in ("open", "new", "pending", ""):
            tasks.append(obj)

    return tasks


def close_task(task_id: str):
    objects = load_objects()

    for obj in objects:
        if str(obj.get("id")) == str(task_id):
            obj["status"] = "closed"

    save_objects(objects)


def update_object(task_id: str, patch: Dict[str, Any]):
    objects = load_objects()

    for obj in objects:
        if str(obj.get("id")) == str(task_id):
            obj.update(patch)

    save_objects(objects)
