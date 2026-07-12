from io import BytesIO
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).parents[1]
OUTPUT = ROOT / "apps" / "web" / "public" / "assets" / "backgrounds"

for path in (OUTPUT / "army-command.webp", OUTPUT / "policy-hall.webp"):
    image = Image.open(path).convert("RGB")
    image = image.crop((0, 0, image.width, max(1, image.height - 36)))
    output = BytesIO()
    image.save(output, "WEBP", quality=90, method=6)
    path.write_bytes(output.getvalue())
    print(f"trimmed {path.name}")
