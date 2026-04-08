import json
import os

OBJECTS_PATH = "objects.json"
STATE_PATH = "v_resonance.json"


def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def find_latest_task(objects):
    tasks = [o for o in objects if o.get("type") == "task"]
    if not tasks:
        return None

    def task_num(obj):
        obj_id = str(obj.get("id", "task_0"))
        tail = obj_id.split("_")[-1]
        return int(tail) if tail.isdigit() else 0

    tasks.sort(key=task_num)
    return tasks[-1]


def main():
    objects = load_json(OBJECTS_PATH, [])
    state = load_json(STATE_PATH, {})

    latest_task = find_latest_task(objects)

    flower = state.get("flower", {})
    meta = state.get("meta", {})
    signal = state.get("signal", {})


    if latest_task is None:
        return



if __name__ == "__main__":
    main()
