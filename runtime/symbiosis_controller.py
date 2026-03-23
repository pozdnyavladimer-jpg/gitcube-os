from dataclasses import dataclass

from core.neuromodulator import NeuroState


@dataclass
class SymbiosisParams:
    pressure: float = 0.5
    flow: float = 0.5
    structure: float = 0.5
    balance: float = 0.5
    law: float = 0.5
    future: float = 0.5


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def clamp_params(params: SymbiosisParams) -> SymbiosisParams:
    return SymbiosisParams(
        pressure=clamp01(params.pressure),
        flow=clamp01(params.flow),
        structure=clamp01(params.structure),
        balance=clamp01(params.balance),
        law=clamp01(params.law),
        future=clamp01(params.future),
    )


def apply_symbiosis(neuro: NeuroState, params: SymbiosisParams) -> SymbiosisParams:
    """
    Neuro → generation control mapping
    """

    updated = SymbiosisParams(
        pressure=params.pressure,
        flow=params.flow,
        structure=params.structure,
        balance=params.balance,
        law=params.law,
        future=params.future,
    )

    # adrenaline
    updated.future += neuro.adrenaline * 0.6
    updated.pressure += neuro.adrenaline * 0.4

    # dopamine
    updated.balance += neuro.dopamine * 0.5
    updated.flow += neuro.dopamine * 0.3

    # cortisol
    updated.law += neuro.cortisol * 0.7
    updated.future -= neuro.cortisol * 0.5

    # serotonin
    updated.structure += neuro.serotonin * 0.6
    updated.balance += neuro.serotonin * 0.4

    return clamp_params(updated)


def get_mode(params: SymbiosisParams) -> str:
    if params.future > 0.8 and params.law < 0.4:
        return "exploration"
    if params.structure > 0.8 and params.balance > 0.8:
        return "stability"
    if params.law > 0.85 and params.future < 0.3:
        return "strict"
    if params.balance > 0.85 and params.flow > 0.7:
        return "lock"
    return "mixed"
