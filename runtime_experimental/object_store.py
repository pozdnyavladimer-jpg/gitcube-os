import json
import os
from typing import Dict, Any, List

OBJECT_PATH = "objects.json"


def load_objects() -> List[Dict[str, Any]]:
    if not os.path.exists(OBJECT_PATH):
        return []
    with open(OBJECT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def save_objects(objs: List[Dict[str, Any]]) -> None:
    with open(OBJECT_PATH, "w", encoding="utf-8") as f:
        json.dump(objs, f, ensure_ascii=False, indent=2)


def _next_id(objs: List[Dict[str, Any]]) -> str:
    nums = []
    for obj in objs:
        oid = str(obj.get("id", ""))
        if oid.startswith("task_"):
            tail = oid.split("_", 1)[1]
            if tail.isdigit():
                nums.append(int(tail))
    n = max(nums) + 1 if nums else 1
    return f"task_{n}"


def add_object(obj: Dict[str, Any]) -> Dict[str, Any]:
    objs = load_objects()
    new_obj = dict(obj)

    if not new_obj.get("id"):
        new_obj["id"] = _next_id(objs)

    objs.append(new_obj)
    save_objects(objs)
    return new_obj


def get_open_tasks() -> List[Dict[str, Any]]:
    return [
        o for o in load_objects()
        if str(o.get("type", "")) == "task"
        and str(o.get("status", "")) == "open"
    ]


def mark_task_done(task_id: str, result_path: str = "") -> Dict[str, Any]:
    objs = load_objects()
    updated = {}

    for obj in objs:
        if str(obj.get("id")) == str(task_id):
            obj["status"] = "done"
            if result_path:
                obj["result_path"] = result_path
            updated = dict(obj)
            break

    save_objects(objs)
    return updated
