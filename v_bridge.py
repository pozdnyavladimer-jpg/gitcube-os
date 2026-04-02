import json
import os
import tempfile
from datetime import datetime
from typing import Dict, Any


class VBridge:
    def __init__(self, file_path: str = "v_resonance.json"):
        self.file_path = file_path

    def read_state(self) -> Dict[str, Any]:
        if not os.path.exists(self.file_path):
            return {
                "flower": {
                    "pressure": 0.5,
                    "flow": 0.5,
                    "structure": 0.5,
                    "balance": 0.5,
                    "law": 0.5,
                    "future": 0.5,
                },
                "meta": {
                    "step": 0,
                    "phase": "DAY",
                    "mode": "FLOW",
                    "vitality": 0.42,
                },
                "signal": {
                    "source": "CORE",
                    "target": "ACTOR",
                    "action": "WAIT",
                    "bond": "NONE",
                    "reason": "idle",
                },
            }

        with open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def write_state(self, data: Dict[str, Any]) -> None:
        directory = os.path.dirname(self.file_path) or "."
        fd, tmp_path = tempfile.mkstemp(prefix="vtmp_", suffix=".json", dir=directory)

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.file_path)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    def update(self, section: str, patch: Dict[str, Any], updated_by: str = "UNKNOWN") -> Dict[str, Any]:
        state = self.read_state()

        if section not in state or not isinstance(state[section], dict):
            state[section] = {}

        state[section].update(patch)

        meta = state.setdefault("meta", {})
        meta["updated_by"] = updated_by
        meta["updated_at"] = datetime.utcnow().isoformat() + "Z"

        self.write_state(state)
        return state
