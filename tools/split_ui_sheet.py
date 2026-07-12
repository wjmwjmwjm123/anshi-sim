from pathlib import Path

from PIL import Image

ROOT = Path(__file__).parents[1]
SOURCE = ROOT / "pic" / "task-mrgfghvtcwn5n.png"
OUTPUT = ROOT / "apps" / "web" / "public" / "assets" / "ui" / "army-actions"
NAMES = ["scroll", "seal", "archives", "official-hat", "coin-grain", "ritual", "tiger-tally", "bamboo-orders", "dispatches", "fortress", "movement", "training", "supply", "scouting", "recruitment"]

def main() -> None:
    image = Image.open(SOURCE).convert("RGB")
    width, height = image.width // 5, image.height // 3
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for index, name in enumerate(NAMES):
        column, row = index % 5, index // 5
        image.crop((column * width, row * height, (column + 1) * width, (row + 1) * height)).save(OUTPUT / f"{name}.webp", "WEBP", quality=90, method=6)
    print(f"wrote {len(NAMES)} tiles to {OUTPUT}")

if __name__ == "__main__":
    main()
