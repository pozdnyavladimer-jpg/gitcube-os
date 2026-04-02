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
