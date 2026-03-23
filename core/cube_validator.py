from dataclasses import dataclass


@dataclass
class CubeState:
    pressure: float     # risk / load
    flow: float         # throughput / activity
    structure: float    # API / code integrity
    balance: float      # internal coherence
    law: float          # canonical compliance
    future: float       # experimental divergence


@dataclass
class CubeValidationResult:
    fit_score: float
    shadow_pressure: float
    is_stable: bool
    is_crystal: bool


def validate_cube(cube: CubeState) -> CubeValidationResult:
    weights = {
        "pressure": 0.2,
        "flow": 0.1,
        "structure": 0.2,
        "balance": 0.2,
        "law": 0.2,
        "future": 0.1,
    }

    fit_score = (
        (1 - cube.pressure) * weights["pressure"] +
        cube.flow * weights["flow"] +
        cube.structure * weights["structure"] +
        cube.balance * weights["balance"] +
        cube.law * weights["law"] +
        (1 - cube.future) * weights["future"]
    )

    shadow_pressure = (
        cube.pressure +
        (1 - cube.structure) +
        (1 - cube.balance) +
        (1 - cube.law)
    ) / 4

    is_stable = (
        cube.balance > 0.7 and
        cube.structure > 0.7 and
        cube.law > 0.8
    )

    is_crystal = (
        is_stable and
        shadow_pressure < 0.2 and
        fit_score > 0.85
    )

    return CubeValidationResult(
        fit_score=fit_score,
        shadow_pressure=shadow_pressure,
        is_stable=is_stable,
        is_crystal=is_crystal
    )
