import json
import os
from typing import Any, Dict, List, Optional

PATH = "objects.json"


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


def get_latest_task() -> Optional[Dict[str, Any]]:
    tasks = [o for o in load_objects() if o.get("type") == "task"]
    if not tasks:
        return None

    def sort_key(x: Dict[str, Any]) -> int:
        obj_id = str(x.get("id", "task_0"))
        tail = obj_id.split("_")[-1]
        return int(tail) if tail.isdigit() else 0

    tasks.sort(key=sort_key)
    return tasks[-1]


def get_latest_open_task() -> Optional[Dict[str, Any]]:
    tasks = [o for o in load_objects() if o.get("type") == "task" and o.get("status") == "open"]
    if not tasks:
        return None

    def sort_key(x: Dict[str, Any]) -> int:
        obj_id = str(x.get("id", "task_0"))
        tail = obj_id.split("_")[-1]
        return int(tail) if tail.isdigit() else 0

    tasks.sort(key=sort_key)
    return tasks[-1]


def get_task_by_id(task_id: str) -> Optional[Dict[str, Any]]:
    for obj in load_objects():
        if str(obj.get("id")) == str(task_id):
            return obj
    return None


def update_object(obj_id: str, patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    data = load_objects()
    updated = None

    for obj in data:
        if str(obj.get("id")) == str(obj_id):
            obj.update(patch or {})
            updated = obj
            break

    save_objects(data)
    return updated


def add_object(obj: Dict[str, Any]) -> Dict[str, Any]:
    data = load_objects()

    if not obj.get("id"):
        obj["id"] = _next_id(data)

    obj.setdefault("type", "task")
    obj.setdefault("status", "open")
    obj.setdefault("published_to_github", False)
    obj.setdefault("github_url", "")
    obj.setdefault("parent_id", None)
    obj.setdefault("related_to", [])
    obj.setdefault("graph_depth", 0)

    data.append(obj)
    save_objects(data)
    return obj


def create_task(
    title: str,
    origin: str,
    kind: str = "task",
    intensity: float = 0.0,
    novelty: float = 0.0,
    payload: Optional[Dict[str, Any]] = None,
    parent_id: Optional[str] = None,
    related_to: Optional[List[str]] = None,
) -> Dict[str, Any]:
    latest = get_latest_task()

    if parent_id is None and latest is not None:
        parent_id = str(latest.get("id"))

    if related_to is None:
        related_to = [parent_id] if parent_id else []

    graph_depth = 0
    if latest and parent_id:
        try:
            graph_depth = int(latest.get("graph_depth", 0)) + 1
        except Exception:
            graph_depth = 1

    task = {
        "type": "task",
        "title": title,
        "origin": origin,
        "status": "open",
        "kind": kind,
        "intensity": float(intensity),
        "novelty": float(novelty),
        "payload": payload or {},
        "parent_id": parent_id,
        "related_to": related_to,
        "graph_depth": graph_depth,
    }
    return add_object(task)


def get_open_tasks() -> List[Dict[str, Any]]:
    return [
        o for o in load_objects()
        if o.get("type") == "task" and o.get("status") == "open"
    ]


def get_open() -> List[Dict[str, Any]]:
    return get_open_tasks()


def mark_task_in_progress(task_id: str, path: str = "") -> Optional[Dict[str, Any]]:
    patch = {"status": "in_progress"}
    if path:
        patch["result_path"] = path
    return update_object(task_id, patch)


def mark_task_done(task_id: str, path: str = "", reason: str = "") -> Optional[Dict[str, Any]]:
    patch = {"status": "done"}
    if path:
        patch["result_path"] = path
    if reason:
        patch["execution_reason"] = reason
    return update_object(task_id, patch)


def mark_done(task_id: str, path: str = "") -> Optional[Dict[str, Any]]:
    return mark_task_done(task_id, path)


def mark_task_skipped(task_id: str, path: str = "", reason: str = "") -> Optional[Dict[str, Any]]:
    patch = {"status": "skipped"}
    if path:
        patch["result_path"] = path
    if reason:
        patch["execution_reason"] = reason
    return update_object(task_id, patch)


def mark_task_failed(task_id: str, path: str = "", reason: str = "") -> Optional[Dict[str, Any]]:
    patch = {"status": "failed"}
    if path:
        patch["result_path"] = path
    if reason:
        patch["execution_reason"] = reason
    return update_object(task_id, patch)


def mark_task_absorbed(task_id: str, path: str = "", reason: str = "") -> Optional[Dict[str, Any]]:
    patch = {"status": "absorbed"}
    if path:
        patch["result_path"] = path
    if reason:
        patch["execution_reason"] = reason
    return update_object(task_id, patch)


def mark_task_published(task_id: str, url: str, path: str = "", reason: str = "") -> Optional[Dict[str, Any]]:
    patch = {
        "status": "published",
        "published_to_github": True,
        "github_url": url,
    }
    if path:
        patch["result_path"] = path
    if reason:
        patch["execution_reason"] = reason
    return update_object(task_id, patch)


def mark_published(task_id: str, url: str) -> Optional[Dict[str, Any]]:
    return mark_task_published(task_id, url)
