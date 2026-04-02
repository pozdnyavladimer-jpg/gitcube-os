#!/bin/bash

echo "=== V-CORE SETUP START ==="

mkdir -p runtime_experimental

# -----------------------
# v_bridge.py
# -----------------------
cat > v_bridge.py <<'PY'
import json
import os
import tempfile
import time
from datetime import datetime


class VBridge:
    def __init__(self, file_path="v_resonance.json"):
        self.file_path = file_path

    def read_state(self):
        if not os.path.exists(self.file_path):
            return {}
        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except:
            return {}

    def write_state(self, data):
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=2)

    def update(self, section, patch):
        state = self.read_state()

        if section not in state:
            state[section] = {}

        state[section].update(patch)
        state["meta"]["updated_at"] = datetime.utcnow().isoformat()

        self.write_state(state)
PY

# -----------------------
# v_resonance.json
# -----------------------
cat > v_resonance.json <<'JSON'
{
  "flower": {
    "pressure": 0.5,
    "flow": 0.5,
    "structure": 0.5,
    "balance": 0.5,
    "law": 0.5,
    "future": 0.5
  },
  "meta": {
    "step": 0,
    "phase": "DAY",
    "mode": "FLOW",
    "vitality": 0.42
  },
  "signal": {
    "action": "WAIT"
  }
}
JSON

# -----------------------
# CORE (os_sync)
# -----------------------
cat > runtime_experimental/os_sync.py <<'PY'
from v_bridge import VBridge
import random


def main():
    bridge = VBridge()

    state = bridge.read_state()
    flower = state.get("flower", {})
    meta = state.get("meta", {})

    step = meta.get("step", 0)
    vitality = meta.get("vitality", 0.42)

    # simple logic
    pressure = random.uniform(0.3, 0.9)
    flow = 1.0 - pressure

    decision = "REJECT"
    action = "WAIT"

    if flow > 0.7:
        decision = "COMMIT"
        action = "BUILD"
    elif flow > 0.5:
        decision = "SOFT_COMMIT"
        action = "STABILIZE"

    # update flower
    bridge.update("flower", {
        "pressure": round(pressure, 3),
        "flow": round(flow, 3)
    })

    # update meta
    bridge.update("meta", {
        "step": step + 1,
        "vitality": round(vitality + (flow - pressure) * 0.1, 3)
    })

    # update signal
    bridge.update("signal", {
        "action": action,
        "decision": decision
    })

    print("CORE STEP:", step, "| decision:", decision, "| action:", action)


if __name__ == "__main__":
    main()
PY

# -----------------------
# ACTOR
# -----------------------
cat > actor_executor.py <<'PY'
from v_bridge import VBridge
import time


def main():
    bridge = VBridge()

    state = bridge.read_state()
    signal = state.get("signal", {})

    action = signal.get("action", "WAIT")

    print("[ACTOR] action:", action)

    if action == "BUILD":
        print("[ACTOR] building...")
        bridge.update("flower", {"structure": 0.8})

    elif action == "STABILIZE":
        print("[ACTOR] stabilizing...")
        bridge.update("flower", {"balance": 0.8})

    # reset
    bridge.update("signal", {"action": "WAIT"})


if __name__ == "__main__":
    main()
PY

echo "=== DONE ==="
