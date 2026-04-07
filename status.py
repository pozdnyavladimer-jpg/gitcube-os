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

    print("=== GITCUBE STATUS ===")
    print("step:", meta.get("step"))
    print("phase:", meta.get("phase"))
    print("mode:", meta.get("mode"))
    print("vitality:", meta.get("vitality"))
    print("structure_floor:", meta.get("structure_floor"))
    print("law_floor:", meta.get("law_floor"))
    print("object_count:", meta.get("object_count"))
    print("signal_action:", signal.get("action"))
    print("signal_decision:", signal.get("decision"))
    print("signal_winner_agent:", signal.get("winner_agent"))
    print("signal_dominant_class:", signal.get("dominant_class"))
    print("flower_pressure:", flower.get("pressure"))
    print("flower_flow:", flower.get("flow"))
    print("flower_structure:", flower.get("structure"))
    print("flower_balance:", flower.get("balance"))
    print("flower_law:", flower.get("law"))
    print("flower_future:", flower.get("future"))

    if latest_task is None:
        print("latest_task: none")
        return

    print("--- latest task ---")
    print("id:", latest_task.get("id"))
    print("title:", latest_task.get("title"))
    print("status:", latest_task.get("status"))
    print("parent_id:", latest_task.get("parent_id"))
    print("graph_depth:", latest_task.get("graph_depth"))
    print("related_to:", latest_task.get("related_to"))
    print("intensity:", latest_task.get("intensity"))
    print("novelty:", latest_task.get("novelty"))
    print("audit_status:", latest_task.get("audit_status"))
    print("audit_reason:", latest_task.get("audit_reason"))
    print("pressure_applied:", latest_task.get("pressure_applied", False))
    print("published_to_github:", latest_task.get("published_to_github"))
    print("github_url:", latest_task.get("github_url"))
    print("result_path:", latest_task.get("result_path"))


if __name__ == "__main__":
    main()
