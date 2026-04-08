import os
import base64
import requests


DEFAULT_API_URL = os.getenv("SD_API_URL", "http://127.0.0.1:7860")


def generate_image(render_request, output_path="generated.png", api_url=None):
    api_url = api_url or DEFAULT_API_URL
    url = f"{api_url.rstrip('/')}/sdapi/v1/txt2img"

    payload = {
        "prompt": render_request.positive_prompt,
        "negative_prompt": render_request.negative_prompt,
        "width": render_request.width,
        "height": render_request.height,
        "steps": render_request.steps,
        "cfg_scale": render_request.cfg_scale,
        "sampler_name": render_request.sampler,
    }

    response = requests.post(url, json=payload, timeout=180)

    if response.status_code != 200:
        return None

    data = response.json()
    if "images" not in data or not data["images"]:
        return None

    image_base64 = data["images"][0]
    image_bytes = base64.b64decode(image_base64)

    with open(output_path, "wb") as f:
        f.write(image_bytes)

    return output_path
