from dataclasses import dataclass
from typing import Dict

from core.neuromodulator import NeuroState


@dataclass
class VisualSpec:
    mood: str
    palette: str
    composition: str
    texture: str
    intensity: float
    prompt: str


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def state_to_visual_spec(
    final_state: Dict[str, float],
    neuro: NeuroState,
    symbiosis_mode: str = "mixed",
) -> VisualSpec:
    pressure = clamp01(final_state.get("pressure", 0.5))
    flow = clamp01(final_state.get("flow", 0.5))
    structure = clamp01(final_state.get("structure", 0.5))
    balance = clamp01(final_state.get("balance", 0.5))
    law = clamp01(final_state.get("law", 0.5))
    future = clamp01(final_state.get("future", 0.5))

    # Mood
    if balance > 0.75 and structure > 0.75:
        mood = "calm coherent crystal"
    elif future > 0.7 and flow > 0.6:
        mood = "exploratory dynamic emergence"
    elif pressure > 0.6:
        mood = "tense unstable field"
    else:
        mood = "transitional adaptive state"

    # Palette
    if symbiosis_mode == "stability":
        palette = "cool blue, green, silver"
    elif symbiosis_mode == "exploration":
        palette = "violet, orange, electric cyan"
    elif symbiosis_mode == "strict":
        palette = "white, deep blue, black"
    elif symbiosis_mode == "lock":
        palette = "gold, blue, crystal white"
    else:
        palette = "balanced teal, amber, soft violet"

    # Composition
    if structure > 0.75:
        composition = "symmetric structured geometric composition"
    elif future > 0.7:
        composition = "asymmetric emergent composition"
    else:
        composition = "balanced centered composition"

    # Texture
    if pressure > 0.6:
        texture = "fractal noisy energetic texture"
    elif balance > 0.75:
        texture = "clean polished crystal texture"
    else:
        texture = "soft layered cinematic texture"

    intensity = clamp01(
        0.30 * pressure +
        0.20 * flow +
        0.15 * future +
        0.15 * neuro.adrenaline +
        0.10 * neuro.dopamine +
        0.10 * (1.0 - neuro.cortisol)
    )

    prompt = (
        f"{mood}, {composition}, {texture}, "
        f"palette of {palette}, "
        f"visualize a living system state with "
        f"pressure {pressure:.2f}, flow {flow:.2f}, structure {structure:.2f}, "
        f"balance {balance:.2f}, law {law:.2f}, future {future:.2f}, "
        f"mode {symbiosis_mode}, "
        f"intensity {intensity:.2f}, "
        f"cinematic, high detail, symbolic system visualization"
    )

    return VisualSpec(
        mood=mood,
        palette=palette,
        composition=composition,
        texture=texture,
        intensity=intensity,
        prompt=prompt,
    )
