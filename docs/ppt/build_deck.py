"""把 template-swiss.html + slides.html + base64 图片拼成单文件 deck。"""
import base64
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # anshi-sim
SKILL = ROOT / ".claude" / "skills" / "guizang-ppt-skill"
TEMPLATE = SKILL / "assets" / "template-swiss.html"
SLIDES = ROOT / "docs" / "ppt" / "slides.html"
OUT = ROOT / "docs" / "ppt" / "index.html"
ASSETS = ROOT / "apps" / "web" / "public" / "assets"
PIC = ROOT / "docs" / "pic"


def data_uri(path: Path) -> str:
    mime = "image/png" if path.suffix.lower() == ".png" else "image/webp"
    return "data:" + mime + ";base64," + base64.b64encode(path.read_bytes()).decode("ascii")


P = ASSETS / "portraits"
E = ASSETS / "events"
TOKENS = {
    "{{COURT}}": ASSETS / "backgrounds" / "court-hall.webp",
    "{{P_XUANZONG}}": P / "xuanzong.webp",
    "{{P_GAOLISHI}}": P / "gao_lishi.webp",
    "{{P_YANGGUOZHONG}}": P / "yang_guozhong.webp",
    "{{P_GESHUHAN}}": P / "geshu_han.webp",
    "{{P_GUOZIYI}}": P / "guo_ziyi.webp",
    "{{P_LIGUANGBI}}": P / "li_guangbi.webp",
    "{{P_LIHENG}}": P / "li_heng.webp",
    "{{P_ANLUSHAN}}": P / "an_lushan.webp",
    "{{P_ANQINGXU}}": P / "an_qingxu.webp",
    "{{P_SHISIMING}}": P / "shi_siming.webp",
    "{{P_LIBI}}": P / "li_bi.webp",
    "{{P_WANGSILI}}": P / "wang_sili.webp",
    "{{E_LINGBAO}}": E / "lingbao_battle.webp",
    "{{E_MAWEI}}": E / "mawei_mutiny.webp",
    "{{E_TONGGUAN}}": E / "hold_tongguan.webp",
    "{{E_SUIYANG}}": E / "suiyang_siege.webp",
    "{{E_RECAPTURE}}": E / "recapture_capitals.webp",
    "{{E_UIGHUR}}": E / "uighur_treaty.webp",
    "{{S_CODEX_CODE}}": PIC / "codex编码.png",
    "{{S_CODEX_AGENT}}": PIC / "codex子agent.png",
    "{{S_CLAUDE}}": PIC / "claudecode.png",
    "{{S_GITHUB}}": PIC / "github.png",
}

template = TEMPLATE.read_text(encoding="utf-8")
slides = SLIDES.read_text(encoding="utf-8")

missing = []
for tok, path in TOKENS.items():
    if not path.exists():
        missing.append(str(path))
        continue
    slides = slides.replace(tok, data_uri(path))

template = template.replace("[必填] 替换为 PPT 标题 · Deck Title", "安史之乱 · AI Agent 开发实践")

start_marker = '<div id="deck">'
end_marker = '<div id="nav">'
i = template.index(start_marker) + len(start_marker)
j = template.index(end_marker)
new_html = template[:i] + "\n" + slides + "\n</div>\n\n" + template[j:]

# ponytail: dark slides inherit --text-primary from :root (dark ink), invisible on dark bg
dark_css = '<style>.slide.dark,.slide.hero.dark{--text-primary:#f0f0ee;--text-secondary:rgba(255,255,255,.78);--text-helper:rgba(255,255,255,.55);--border-subtle:rgba(255,255,255,.18);background:var(--ink)}.slide.dark .canvas-card,.slide.hero.dark .canvas-card{background:var(--ink)}</style>\n'
new_html = new_html.replace('</head>', dark_css + '</head>')

OUT.write_text(new_html, encoding="utf-8")
print("wrote", OUT)
print("size KB:", len(new_html.encode("utf-8")) // 1024)
if missing:
    print("MISSING FILES:", missing)
leftover = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", new_html)))
if leftover:
    print("LEFTOVER TOKENS:", leftover)
fill = sorted(set(re.findall(r"\[必填\][^<]*", new_html)))
if fill:
    print("LEFTOVER 必填:", fill)
print("slide count:", new_html.count('class="slide'))
