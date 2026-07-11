from __future__ import annotations

import sys
from pathlib import Path
from urllib.error import HTTPError

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from anshi.ai import chat_completion, load_config  # noqa: E402

config = load_config()
if config is None:
    raise SystemExit("未配置联网模型")
print(f"模型：{config.model}")
print(f"地址：{config.base_url}")
try:
    print(chat_completion([{"role": "user", "content": "只回复：联网成功"}], config))
except HTTPError as error:
    print(f"HTTP {error.code}: {error.read().decode('utf-8', errors='replace')}")
    raise SystemExit(1)
