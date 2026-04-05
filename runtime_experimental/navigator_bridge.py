import json
import urllib.request
from typing import Dict, Any

FEEDBACK_URL = "https://raw.githubusercontent.com/pozdnyavladimer-jpg/geometric-state-navigator/main/navigator_feedback.json"


def load_navigator_feedback() -> Dict[str, Any]:
    try:
        with urllib.request.urlopen(FEEDBACK_URL) as response:
            return json.loads(response.read().decode())
    except Exception:
        return {
            "source": "NAVIGATOR",
            "action": "STABLE",
            "issues": [],
            "vector": {},
        }


def build_feedback_patch(feedback: Dict[str, Any]) -> Dict[str, Any]:
    action = str(feedback.get("action", "STABLE"))

    weights = {
        "shadow": 1.0,
        "coherence": 1.0,
        "target_fit": 1.0,
        "vitality": 1.0,
    }

    patch: Dict[str, Any] = {
        "weights": weights,
        "navigator_action": action,
    }

    if action == "INCREASE_FLOW":
        patch["weights"]["vitality"] = 1.25
        patch["weights"]["target_fit"] = 1.10
        patch["mode"] = "flow_boost"

    elif action == "INCREASE_LAW":
        patch["weights"]["coherence"] = 1.20
        patch["weights"]["shadow"] = 1.10
        patch["mode"] = "law_boost"

    elif action == "REDUCE_PRESSURE":
        patch["weights"]["shadow"] = 1.35
        patch["weights"]["coherence"] = 1.15
        patch["mode"] = "pressure_reduction"

    elif action == "DESTABILIZE":
        patch["weights"]["vitality"] = 1.20
        patch["weights"]["coherence"] = 0.95
        patch["mode"] = "destabilize"

    else:
        patch["mode"] = "stable"

    return patch
