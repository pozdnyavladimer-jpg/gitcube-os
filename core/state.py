from dataclasses import dataclass
from typing import Dict


STATE_KEYS = [
    "pressure",
    "flow",
    "structure",
    "balance",
    "law",
    "future",
]


@dataclass
class SystemState:
    pressure: float
    flow: float
    structure: float
    balance: float
    law: float
    future: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "pressure": self.pressure,
            "flow": self.flow,
            "structure": self.structure,
            "balance": self.balance,
            "law": self.law,
            "future": self.future,
        }

    @classmethod
    def from_dict(cls, values: Dict[str, float]) -> "SystemState":
        return cls(
            pressure=values["pressure"],
            flow=values["flow"],
            structure=values["structure"],
            balance=values["balance"],
            law=values["law"],
            future=values["future"],
        )


def normalize_state(values: Dict[str, float]) -> Dict[str, float]:
    clipped = {k: max(0.0, float(values[k])) for k in STATE_KEYS}
    total = sum(clipped.values())

    if total <= 1e-9:
        return {k: 1.0 / len(STATE_KEYS) for k in STATE_KEYS}

    return {k: clipped[k] / total for k in STATE_KEYS}


def default_state() -> SystemState:
    return SystemState.from_dict(
        normalize_state(
            {
                "pressure": 0.16,
                "flow": 0.17,
                "structure": 0.17,
                "balance": 0.17,
                "law": 0.16,
                "future": 0.17,
            }
        )
    )
