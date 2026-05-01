from __future__ import annotations

import time
import json
from pprint import pprint
from pathlib import Path
from typing import Dict, Any

from app.orchestration.task_dispatcher import (
    build_kernel_state,
    ingest_event,
    dispatch_tick,
)
from core.utils.shadow_detector import build_shadow_event
from core.utils.file_watch_snapshot import (
    build_repo_snapshot,
    diff_repo_snapshot,
    build_change_event,
)

def read_external_events(path: str = "external_signal.json"):
    signal_path = Path(path)
    if not signal_path.exists():
        return []

    try:
        data = json.loads(signal_path.read_text(encoding="utf-8"))
    except Exception as e:
        print({"external_signal_error": str(e)})
        return []

    events = data.get("pending_events", [])
    if not isinstance(events, list):
        return []

    # consume events so they do not repeat forever
    try:
        signal_path.write_text(json.dumps({"pending_events": []}, indent=2), encoding="utf-8")
    except Exception as e:
        print({"external_signal_clear_error": str(e)})

    return [ev for ev in events if isinstance(ev, dict)]

TICK_SECONDS = 4.0


def run_kernel_loop(repo_root: str = ".", max_ticks: int | None = None) -> Dict[str, Any]:
    state = build_kernel_state()
    previous_snapshot = build_repo_snapshot(repo_root)

    tick = 0

    while True:
        tick += 1

        external_events = read_external_events()
        for ev in external_events:
            state = ingest_event(state, ev)

        shadow = build_shadow_event(repo_root)
        if not shadow.get("ok", True):
            event = {
                "priority": "critical",
                "payload": {
                    "problem": "shadow_stdlib_group",
                    "paths": shadow.get("paths", []),
                    "has_shadow_backup": True,
                },
            }
            state = ingest_event(state, event)

        current_snapshot = build_repo_snapshot(repo_root)
        diff = diff_repo_snapshot(previous_snapshot, current_snapshot)

        print(f"\n=== V_KERNEL TICK {tick} ===")
        print({
            "has_changes": diff["has_changes"],
            "created": len(diff["created"]),
            "changed": len(diff["changed"]),
            "deleted": len(diff["deleted"]),
        })

        if diff["has_changes"]:
            event = build_change_event(diff, priority="high")
            state = ingest_event(state, event)
            state = dispatch_tick(state)
            pprint({
                "mode": state.get("mode"),
                "last_problem": state.get("last_problem"),
                "last_route": state.get("last_route"),
                "last_result": state.get("last_result"),
                "hotspots": state.get("hotspots"),
                "tick": state.get("tick"),
            })
        else:
            state = dispatch_tick(state)
            pprint({
                "mode": state.get("mode"),
                "last_result": state.get("last_result"),
                "tick": state.get("tick"),
            })

        previous_snapshot = current_snapshot

        if max_ticks is not None and tick >= max_ticks:
            return state

        time.sleep(TICK_SECONDS)


if __name__ == "__main__":
    final_state = run_kernel_loop(".", max_ticks=5)
    print("\n=== FINAL STATE ===")
    pprint(final_state)
