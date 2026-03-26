from typing import Dict


MODE_BIASES = {
    "balanced": {
        "planner": 0.0,
        "explorer": 0.0,
        "stabilizer": 0.0,
    },
    "planner-biased": {
        "planner": 0.08,
        "explorer": -0.03,
        "stabilizer": 0.0,
    },
    "explorer-biased": {
        "planner": -0.03,
        "explorer": 0.08,
        "stabilizer": -0.01,
    },
    "stabilizer-biased": {
        "planner": -0.02,
        "explorer": -0.04,
        "stabilizer": 0.09,
    },
}


def get_mode_bias(mode: str) -> Dict[str, float]:
    return MODE_BIASES.get(mode, MODE_BIASES["balanced"]).copy()
