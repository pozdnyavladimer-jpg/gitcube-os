import os
from datetime import datetime

from runtime_experimental.object_store import get_open_tasks, mark_task_done
from v_bridge import VBridge

BUS_PATH = os.environ.get("V_RESONANCE_PATH", "v_resonance.json")
OUTPUT_DIR = "reports"


def ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def main():
    bridge = VBridge(BUS_PATH)
    state = bridge.read_state()
    signal = dict(state.get("signal", {}))

    action = str(signal.get("action", "WAIT"))
    latest_task_id = str(signal.get("latest_task_id", ""))
    open_tasks = get_open_tasks()

    print("[ACTOR] action:", action)
    print("[ACTOR] open_tasks:", len(open_tasks))
    print("[ACTOR] latest_task_id:", latest_task_id)

    if action == "WAIT":
        return

    if not open_tasks:
        print("[ACTOR] no open tasks")
        return

    task = None

    if latest_task_id:
        for t in open_tasks:
            if str(t.get("id")) == latest_task_id:
                task = t
                break

    if task is None:
        task = open_tasks[0]

    ensure_dir(OUTPUT_DIR)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(OUTPUT_DIR, f"{task['id']}_{ts}.md")

    content = f"""# Task Report

- id: {task.get('id')}
- title: {task.get('title')}
- origin: {task.get('origin')}
- kind: {task.get('kind')}
- status: done
- generated_at: {datetime.utcnow().isoformat()}Z

## Payload
{task.get('payload', {})}

## Actor Decision
action = {action}
"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    mark_task_done(str(task.get("id")), result_path=path)

    print("[ACTOR] created:", path)


if __name__ == "__main__":
    main()
