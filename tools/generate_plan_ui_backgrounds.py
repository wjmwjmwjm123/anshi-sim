from __future__ import annotations

import base64
import json
import os
import urllib.request
from io import BytesIO
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).parents[1]
OUTPUT = ROOT / "apps" / "web" / "public" / "assets" / "backgrounds"
ENDPOINT = "https://ark.cn-beijing.volces.com/api/plan/v3/images/generations"
MODEL = "doubao-seedream-5.0-lite"

PROMPTS = {
    "army-command": (
        "Historical Tang dynasty military command tent for a strategy game UI background, "
        "deep soot black and dark malachite green, restrained cinnabar and aged gold, rich contrast, "
        "wooden campaign table, rolled maps, bamboo dispatches, bronze tiger tally, oil lamps, "
        "empty dark space in the center and lower right for interface panels, cinematic low light, "
        "period-accurate 756 CE Tang objects, realistic painted game art, no people, no text, "
        "no watermark, no modern objects, no fantasy armor, no pale haze, no washed-out highlights."
    ),
    "policy-hall": (
        "Dark Tang dynasty imperial planning hall for a historical strategy game UI background, "
        "deep charcoal, muted jade, aged parchment and restrained cinnabar, shelves of bamboo slips, "
        "bronze seals and a large campaign map in the distance, broad quiet negative space for a "
        "national policy tree overlay, dramatic warm side light, high contrast, period-accurate, "
        "realistic painterly game art, no people, no text, no watermark, no modern objects, "
        "no fantasy armor, no pale haze, no washed-out colors."
    ),
}


def generate(prompt: str) -> bytes:
    key = os.environ.get("ARK_API_KEY", "").strip()
    if not key:
        raise SystemExit("ARK_API_KEY is not set")
    body = json.dumps(
        {"model": MODEL, "prompt": prompt, "size": "2560x1440", "response_format": "url", "extra_body": {"watermark": True}},
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        payload = json.loads(response.read().decode("utf-8"))
    item = (payload.get("data") or [payload])[0]
    encoded = item.get("b64_json") or item.get("base64") or item.get("image_base64")
    if encoded:
        if encoded.startswith("data:"):
            encoded = encoded.split(",", 1)[1]
        return base64.b64decode(encoded)
    url = item.get("url") or item.get("image_url")
    if not url:
        raise RuntimeError("PLAN response contains no image URL or base64 data")
    with urllib.request.urlopen(url, timeout=300) as response:
        return response.read()


def normalize(raw: bytes) -> bytes:
    image = Image.open(BytesIO(raw)).convert("RGB")
    image = image.crop((0, 0, image.width, max(1, image.height - round(image.height * 0.11))))
    image.thumbnail((1600, 900), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (1600, 900), (22, 27, 23))
    canvas.paste(image, ((1600 - image.width) // 2, (900 - image.height) // 2))
    output = BytesIO()
    canvas.save(output, "WEBP", quality=90, method=6)
    return output.getvalue()


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, prompt in PROMPTS.items():
        target = OUTPUT / f"{name}.webp"
        target.write_bytes(normalize(generate(prompt)))
        print(f"generated {target.name}")


if __name__ == "__main__":
    main()
