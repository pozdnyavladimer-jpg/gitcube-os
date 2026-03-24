from dataclasses import dataclass
from typing import Dict

from core.projector import VisualSpec


@dataclass
class RenderRequest:
    positive_prompt: str
    negative_prompt: str
    width: int
    height: int
    steps: int
    cfg_scale: float
    sampler: str
    mode: str


def build_render_request(spec: VisualSpec, mode: str = "image") -> RenderRequest:
    """
    Convert internal visual spec into generation-ready render request.
    """

    negative_prompt = (
        "blurry, low quality, distorted anatomy, broken symmetry, "
        "extra limbs, noisy artifacts, unreadable details, oversaturated, glitch"
    )

    if spec.intensity > 0.75:
        steps = 40
        cfg_scale = 8.5
        sampler = "DPM++ 2M Karras"
    elif spec.intensity > 0.45:
        steps = 32
        cfg_scale = 7.5
        sampler = "Euler a"
    else:
        steps = 24
        cfg_scale = 6.5
        sampler = "Euler"

    if mode == "video":
        width, height = 1280, 720
    else:
        width, height = 1024, 1024

    return RenderRequest(
        positive_prompt=spec.prompt,
        negative_prompt=negative_prompt,
        width=width,
        height=height,
        steps=steps,
        cfg_scale=cfg_scale,
        sampler=sampler,
        mode=mode,
    )


def render_request_to_dict(req: RenderRequest) -> Dict[str, object]:
    return {
        "positive_prompt": req.positive_prompt,
        "negative_prompt": req.negative_prompt,
        "width": req.width,
        "height": req.height,
        "steps": req.steps,
        "cfg_scale": req.cfg_scale,
        "sampler": req.sampler,
        "mode": req.mode,
    }
