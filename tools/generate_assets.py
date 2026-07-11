from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parents[1]
SCENARIO = ROOT / "content" / "scenarios" / "tongguan_756"
OUTPUT = ROOT / "apps" / "web" / "public" / "assets"
MANIFEST = OUTPUT / "manifest.json"
ENDPOINT = "https://ark.cn-beijing.volces.com/api/plan/v3/images/generations"
MODEL = "doubao-seedream-5.0-lite"
STYLE = (
    "唐代安史之乱历史策略游戏美术，写实工笔与电影光影结合，"
    "考据唐代服饰、甲胄、建筑和器物，庄重克制，高细节，无现代物品，无文字，无水印"
)


@dataclass(frozen=True)
class Asset:
    id: str
    kind: str
    source_id: str
    file: str
    prompt: str


def load_assets() -> list[Asset]:
    campaign = _read_json(SCENARIO / "campaign.json")
    characters = [*campaign["characters"], *_read_json(SCENARIO / "characters_extra.json")]
    if len(characters) != 31:
        raise ValueError(f"expected 31 characters, found {len(characters)}")

    regions = {item["id"]: item["name"] for item in campaign["regions"]}
    powers = {item["id"]: item["name"] for item in campaign["powers"]}
    assets = [_portrait(character, regions, powers) for character in characters]
    assets.extend(_background(act) for act in campaign["acts"])
    for act in campaign["acts"]:
        assets.extend(_event(event, act) for event in act["event_candidates"])
    return assets


def _portrait(character: dict[str, Any], regions: dict[str, str], powers: dict[str, str]) -> Asset:
    source_id = character["id"]
    prompt = (
        f"{STYLE}。人物半身立绘：{character['name']}，{character['identity']}。"
        f"所属{powers.get(character['power'], character['power'])}，身处{regions.get(character['region'], character['region'])}。"
        f"人物立场：{character['public_stance']}。神情与仪态体现其身份与立场，"
        "中性暗色背景，人物完整不裁切，不使用现代影视明星面孔"
    )
    return Asset(f"portrait:{source_id}", "portrait", source_id, f"portraits/{source_id}.webp", prompt)


def _background(act: dict[str, Any]) -> Asset:
    source_id = act["id"]
    start, end = act["date_window"]
    prompt = (
        f"{STYLE}。横向游戏场景背景，章节《{act['name']}》，时间{start}至{end}。"
        "展现战乱中的中唐大地、城防、驿道与远处军阵，为界面留出充足暗部和空白"
    )
    return Asset(f"background:{source_id}", "background", source_id, f"backgrounds/{source_id}.webp", prompt)


def _event(event: dict[str, Any], act: dict[str, Any]) -> Asset:
    source_id = event["id"]
    prompt = (
        f"{STYLE}。横向历史事件插图，章节《{act['name']}》中的《{event['name']}》。"
        f"历史时间：{event['historical_window']}。以人物行动、环境与军事态势表现事件，"
        "画面有明确叙事焦点，不画游戏 UI"
    )
    return Asset(f"event:{source_id}", "event", source_id, f"events/{source_id}.webp", prompt)


def generate(asset: Asset, api_key: str, model: str, endpoint: str) -> tuple[bytes, dict[str, Any]]:
    size = "2048x2048" if asset.kind == "portrait" else "2560x1440"
    body = json.dumps(
        {"model": model, "prompt": asset.prompt + "。主体避开画面最下方，底部留出安全裁切余量", "size": size, "response_format": "url"},
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        payload = json.loads(response.read().decode("utf-8"))
    item = (payload.get("data") or [payload])[0]
    encoded = item.get("b64_json") or item.get("base64") or item.get("image_base64")
    if encoded:
        if encoded.startswith("data:"):
            encoded = encoded.split(",", 1)[1]
        return base64.b64decode(encoded), payload
    url = item.get("url") or item.get("image_url")
    if not url:
        raise ValueError("Seedream response contains neither URL nor base64 image data")
    with urllib.request.urlopen(url, timeout=300) as response:
        return response.read(), payload


def normalize_image(raw: bytes, kind: str) -> bytes:
    from io import BytesIO
    from PIL import Image

    image = Image.open(BytesIO(raw)).convert("RGB")
    # Seedream currently stamps the lower-right corner. Remove the whole footer,
    # then restore the requested aspect ratio for predictable UI crops.
    footer = max(80, round(image.height * 0.075))
    image = image.crop((0, 0, image.width, image.height - footer))
    target = (1024, 1024) if kind == "portrait" else (1600, 900)
    source_ratio = image.width / image.height
    target_ratio = target[0] / target[1]
    if source_ratio > target_ratio:
        width = round(image.height * target_ratio)
        left = (image.width - width) // 2
        image = image.crop((left, 0, left + width, image.height))
    else:
        height = round(image.width / target_ratio)
        image = image.crop((0, 0, image.width, height))
    image = image.resize(target, Image.Resampling.LANCZOS)
    output = BytesIO()
    image.save(output, "WEBP", quality=88, method=6)
    return output.getvalue()


def select(assets: list[Asset], only: list[str]) -> list[Asset]:
    filters = {part.strip() for value in only for part in value.split(",") if part.strip()}
    if not filters:
        return assets
    aliases = {"portraits": "portrait", "backgrounds": "background", "events": "event"}
    filters |= {aliases[value] for value in filters if value in aliases}
    selected = [asset for asset in assets if asset.id in filters or asset.source_id in filters or asset.kind in filters]
    if not selected:
        raise ValueError(f"--only matched no assets: {', '.join(sorted(filters))}")
    return selected


def run(args: argparse.Namespace) -> int:
    assets = load_assets()
    chosen = select(assets, args.only)
    print(f"assets: {len(chosen)}/{len(assets)}")
    pending: list[Asset] = []
    for asset in chosen:
        print(f"{asset.id} -> {asset.file}\n  {asset.prompt}")
    if args.dry_run:
        return 0

    api_key = os.environ.get("ARK_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("ARK_API_KEY is not set")
    manifest = _load_manifest()
    entries = {item["id"]: item for item in manifest.get("assets", [])}
    for asset in chosen:
        target = OUTPUT / asset.file
        entry = {**asdict(asset), "status": "pending"}
        if target.exists() and not args.force:
            entry.update(status="existing", bytes=target.stat().st_size, sha256=_sha256(target.read_bytes()))
            entries[asset.id] = entry
            continue
        pending.append(asset)

    def work(asset: Asset) -> tuple[Asset, bytes, dict[str, Any]]:
        raw, response = generate(asset, api_key, args.model, args.endpoint)
        return asset, normalize_image(raw, asset.kind), response

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
      futures = {executor.submit(work, asset): asset for asset in pending}
      for future in as_completed(futures):
        asset = futures[future]
        target = OUTPUT / asset.file
        target.parent.mkdir(parents=True, exist_ok=True)
        entry = {**asdict(asset), "status": "pending"}
        try:
            _, image, response = future.result()
            target.write_bytes(image)
            entry.update(
                status="generated",
                bytes=len(image),
                sha256=_sha256(image),
                generated_at=_now(),
                provider_request_id=response.get("id") or response.get("request_id") or "",
            )
            print(f"generated {asset.id}")
        except Exception as error:
            entry.update(status="error", error=str(error), attempted_at=_now())
            entries[asset.id] = entry
            _write_manifest(manifest, entries, assets, args)
            print(f"failed {asset.id}: {error}", file=sys.stderr)
            continue
        entries[asset.id] = entry
        _write_manifest(manifest, entries, assets, args)
    _write_manifest(manifest, entries, assets, args)
    return 1 if any(entries.get(asset.id, {}).get("status") == "error" for asset in chosen) else 0


def _load_manifest() -> dict[str, Any]:
    return _read_json(MANIFEST) if MANIFEST.exists() else {}


def _write_manifest(
    manifest: dict[str, Any], entries: dict[str, dict[str, Any]], assets: list[Asset], args: argparse.Namespace
) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest.update(
        schema_version=1,
        provider="ByteDance Ark Seedream",
        model=args.model,
        endpoint=args.endpoint,
        sizes={"portrait": "2048x2048", "background": "2560x1440", "event": "2560x1440"},
        source_files=[
            "content/scenarios/tongguan_756/campaign.json",
            "content/scenarios/tongguan_756/characters_extra.json",
        ],
        expected_counts={
            "portrait": sum(asset.kind == "portrait" for asset in assets),
            "background": sum(asset.kind == "background" for asset in assets),
            "event": sum(asset.kind == "event" for asset in assets),
        },
        updated_at=_now(),
        assets=[entries[key] for key in sorted(entries)],
    )
    temporary = MANIFEST.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(MANIFEST)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Seedream assets for the Tongguan campaign.")
    parser.add_argument("--only", action="append", default=[], help="Asset id, source id, or kind; comma-separated/repeatable")
    parser.add_argument("--force", action="store_true", help="Regenerate files that already exist")
    parser.add_argument("--dry-run", action="store_true", help="Print selected prompts without network or file writes")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--endpoint", default=ENDPOINT)
    parser.add_argument("--workers", type=int, default=4, help="Concurrent API requests")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
