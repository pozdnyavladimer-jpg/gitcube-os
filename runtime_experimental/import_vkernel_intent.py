# -*- coding: utf-8 -*-
"""
Import V-Kernel D46 FieldIntent task into GitCube OS.

Input:
  reports/gitcube_os_task_candidate.json

Output:
  objects.json
  reports/vkernel_import_result.json

Purpose:
  V-Kernel detects field pain.
  This bridge turns selected FieldIntentAtom into a GitCube OS pending task.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_INPUT = "reports/gitcube_os_task_candidate.json"
DEFAULT_OBJECTS = "objects.json"
DEFAULT_RESULT = "reports/vkernel_import_result.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return deepcopy(default)
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return deepcopy(default)
    return json.loads(text)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def stable_id(meta_key: str) -> str:
    raw = str(meta_key or "vkernel-field-intent").encode("utf-8")
    h = hashlib.sha1(raw).hexdigest()[:10]
    return f"vkernel_{h}"


def normalize_priority(value: Any) -> str:
    v = str(value or "").strip().lower()
    if v in {"critical", "high", "medium", "low"}:
        return v
    try:
        f = float(value)
        if f >= 0.80:
            return "critical"
        if f >= 0.62:
            return "high"
        if f >= 0.45:
            return "medium"
        return "low"
    except Exception:
        return "medium"


def normalize_candidate(candidate: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(candidate, dict):
        raise ValueError("candidate must be a JSON object")

    if not candidate:
        raise ValueError("candidate is empty")

    meta_key = str(candidate.get("meta_key") or "").strip()
    if not meta_key:
        intent = candidate.get("intent", "UNKNOWN_INTENT")
        field_case = candidate.get("field_case", "UNKNOWN_CASE")
        problem = candidate.get("problem", "field_intent_bridge_task")
        meta_key = f"vkernel:d46:{intent}:{field_case}:{problem}"

    task_id = str(candidate.get("id") or stable_id(meta_key))

    payload = candidate.get("payload")
    if not isinstance(payload, dict):
        payload = {}

    resonance_vector = candidate.get("resonance_vector")
    if not isinstance(resonance_vector, dict):
        resonance_vector = {}

    problem = str(candidate.get("problem") or "field_intent_bridge_task")
    intent = str(candidate.get("intent") or payload.get("intent") or "UNKNOWN_INTENT")
    agent = str(
        candidate.get("target_agent")
        or candidate.get("executor_hint")
        or payload.get("target_agent")
        or "MAGE"
    )

    title = str(
        candidate.get("title")
        or f"V-Kernel field intent: {intent}"
    )

    task = {
        "id": task_id,
        "kind": "FIELD_INTENT_TASK",
        "source": "v_kernel",
        "bridge": "D46_FIELD_INTENT_BRIDGE",
        "status": str(candidate.get("status") or "pending"),
        "problem": problem,
        "intent": intent,
        "title": title,
        "priority": normalize_priority(candidate.get("priority", candidate.get("intensity"))),
        "intensity": float(candidate.get("intensity", payload.get("pain_score", 0.0)) or 0.0),
        "novelty": float(candidate.get("novelty", payload.get("ambiguity", 0.0)) or 0.0),
        "executor_hint": agent,
        "target_agent": agent,
        "field_case": str(candidate.get("field_case") or payload.get("case") or "UNKNOWN_CASE"),
        "meta_key": meta_key,
        "resonance_vector": resonance_vector,
        "payload": {
            **payload,
            "candidate": candidate,
        },
        "created_at": str(candidate.get("created_at") or utc_now()),
        "updated_at": utc_now(),
    }

    return task


def detect_task_list(objects_data: Any) -> Tuple[Any, List[Dict[str, Any]], Optional[str]]:
    """
    Supports common shapes:
      objects.json = []
      objects.json = {"objects": []}
      objects.json = {"tasks": []}
      objects.json = {"items": []}
      objects.json = {"pending": []}
    """
    if isinstance(objects_data, list):
        return objects_data, objects_data, None

    if isinstance(objects_data, dict):
        for key in ("tasks", "objects", "items", "pending"):
            value = objects_data.get(key)
            if isinstance(value, list):
                return objects_data, value, key

        objects_data["objects"] = []
        return objects_data, objects_data["objects"], "objects"

    return {"objects": []}, [], "objects"


def upsert_task(task_list: List[Dict[str, Any]], task: Dict[str, Any]) -> Dict[str, Any]:
    task_id = task.get("id")
    meta_key = task.get("meta_key")

    for i, existing in enumerate(task_list):
        if not isinstance(existing, dict):
            continue

        same_id = existing.get("id") == task_id
        same_meta = meta_key and existing.get("meta_key") == meta_key

        if same_id or same_meta:
            preserved = deepcopy(existing)
            preserved.update(task)
            preserved["created_at"] = existing.get("created_at", task.get("created_at"))
            preserved["updated_at"] = utc_now()
            task_list[i] = preserved
            return {
                "action": "updated",
                "id": preserved.get("id"),
                "meta_key": preserved.get("meta_key"),
            }

    task_list.append(task)
    return {
        "action": "created",
        "id": task.get("id"),
        "meta_key": task.get("meta_key"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=DEFAULT_INPUT)
    ap.add_argument("--objects", default=DEFAULT_OBJECTS)
    ap.add_argument("--result", default=DEFAULT_RESULT)
    args = ap.parse_args()

    input_path = Path(args.input)
    objects_path = Path(args.objects)
    result_path = Path(args.result)

    candidate = load_json(input_path, default=None)
    if candidate is None:
        result = {
            "ok": False,
            "reason": "missing_candidate",
            "input": str(input_path),
        }
        write_json(result_path, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    task = normalize_candidate(candidate)

    objects_data = load_json(objects_path, default={"objects": []})
    root, task_list, container_key = detect_task_list(objects_data)

    upsert = upsert_task(task_list, task)

    if isinstance(root, dict) and container_key:
        root[container_key] = task_list

    if not objects_path.exists():
        objects_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        backup_path = objects_path.with_suffix(objects_path.suffix + ".bak")
        backup_path.write_text(objects_path.read_text(encoding="utf-8"), encoding="utf-8")

    write_json(objects_path, root)

    result = {
        "ok": True,
        "reason": "vkernel_intent_imported",
        "input": str(input_path),
        "objects": str(objects_path),
        "container": container_key or "root_list",
        "upsert": upsert,
        "task": task,
    }

    write_json(result_path, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
