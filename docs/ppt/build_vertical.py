"""生成竖版介绍页面，工具前置，单文件自包含。"""
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "apps" / "web" / "public" / "assets"
PIC = ROOT / "docs" / "pic"
OUT = ROOT / "docs" / "ppt" / "vertical.html"

def b64(path: Path) -> str:
    mime = "image/png" if path.suffix.lower() == ".png" else "image/webp"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")

P = ASSETS / "portraits"
E = ASSETS / "events"

# preload images
court = b64(ASSETS / "backgrounds" / "court-hall.webp")
portraits = {n: b64(P / f"{n}.webp") for n in [
    "xuanzong","gao_lishi","yang_guozhong","geshu_han","guo_ziyi",
    "li_guangbi","li_heng","an_lushan","an_qingxu","shi_siming","li_bi","wang_sili",
]}
events = {n: b64(E / f"{n}.webp") for n in [
    "lingbao_battle","mawei_mutiny","hold_tongguan",
    "suiyang_siege","recapture_capitals","uighur_treaty",
]}
screenshots = {n: b64(PIC / f"{n}") for n in [
    "codex编码.png","codex子agent.png","claudecode.png","github.png",
]}
event_labels = {
    "lingbao_battle":"灵宝之战","mawei_mutiny":"马嵬之变","hold_tongguan":"潼关坚守",
    "suiyang_siege":"睢阳之战","recapture_capitals":"收复两京","uighur_treaty":"回纥盟约",
}
portrait_labels = {
    "xuanzong":"玄宗","gao_lishi":"高力士","yang_guozhong":"杨国忠","geshu_han":"哥舒翰",
    "guo_ziyi":"郭子仪","li_guangbi":"李光弼","li_heng":"李亨","an_lushan":"安禄山",
    "an_qingxu":"安庆绪","shi_siming":"史思明","li_bi":"李泌","wang_sili":"王思礼",
}

def portrait_grid():
    return "\n".join(
        f'<figure><img src="{portraits[k]}" alt="{portrait_labels[k]}"><figcaption>{portrait_labels[k]}</figcaption></figure>'
        for k in portraits
    )

def event_grid():
    return "\n".join(
        f'<figure><img src="{events[k]}" alt="{event_labels[k]}"><figcaption>{event_labels[k]}</figcaption></figure>'
        for k in events
    )

def screenshot_grid():
    labels = {"codex编码.png":"Codex 编码中","codex子agent.png":"Codex 子 Agent 并行",
              "claudecode.png":"Claude Code 主编码","github.png":"GitHub 提交记录"}
    return "\n".join(
        f'<figure><img src="{screenshots[k]}" alt="{labels[k]}"><figcaption>{labels[k]}</figcaption></figure>'
        for k in screenshots
    )

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>安史之乱 · AI Agent 开发实践</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans SC","Microsoft YaHei",sans-serif;color:#0a0a0a;background:#fafafa;line-height:1.65;font-size:16px}}
.hero{{background:#002FA7;color:#fff;padding:80px 24px 60px;text-align:center}}
.hero h1{{font-size:clamp(2.4rem,5vw,3.6rem);font-weight:200;letter-spacing:-.02em;line-height:1.15;margin-bottom:16px}}
.hero h1 em{{font-style:italic;font-weight:300}}
.hero p{{font-size:clamp(1rem,2vw,1.2rem);font-weight:400;opacity:.85;max-width:600px;margin:0 auto;line-height:1.7}}
.wrap{{max-width:960px;margin:0 auto;padding:0 24px}}
section{{padding:56px 0}}
section:nth-child(even){{background:#f0f0ee}}
h2{{font-size:clamp(1.6rem,3.2vw,2.2rem);font-weight:200;letter-spacing:-.015em;margin-bottom:8px}}
.sub{{font-size:.85rem;color:#737373;letter-spacing:.12em;text-transform:uppercase;margin-bottom:4px}}
.lead{{font-size:1.05rem;color:#444;max-width:64ch;margin-bottom:32px;line-height:1.7}}
.grid-3{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:20px;margin-top:24px}}
.card{{background:#fff;border:1px solid #e0e0e0;padding:20px 22px;display:flex;flex-direction:column;gap:8px}}
.card h3{{font-size:1.1rem;font-weight:500}}
.card p{{font-size:.92rem;color:#555;line-height:1.6}}
.card .tag{{display:inline-block;font-size:.72rem;font-weight:600;letter-spacing:.06em;padding:2px 8px;background:#002FA7;color:#fff;width:fit-content}}
.kpi-row{{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:20px;margin:32px 0}}
.kpi{{text-align:center}}
.kpi .num{{font-size:clamp(2.4rem,5vw,3.2rem);font-weight:200;color:#002FA7;line-height:1}}
.kpi .label{{font-size:.85rem;color:#737373;margin-top:4px}}
.img-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:12px;margin-top:24px}}
.img-grid.events{{grid-template-columns:repeat(auto-fill,minmax(240px,1fr))}}
.img-grid figure{{margin:0;overflow:hidden;background:#f0f0ee}}
.img-grid img{{width:100%;aspect-ratio:3/4;object-fit:cover;object-position:center 18%;display:block}}
.img-grid.events img{{aspect-ratio:16/10}}
.img-grid figcaption{{font-size:.78rem;font-weight:500;padding:6px 8px;text-align:center}}
.shot-grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:24px}}
.shot-grid figure{{margin:0;background:#fff;border:1px solid #e0e0e0;display:flex;flex-direction:column}}
.shot-grid img{{width:100%;aspect-ratio:16/9;object-fit:contain;padding:10px}}
.shot-grid figcaption{{font-size:.85rem;font-weight:500;padding:10px 14px;border-top:1px solid #e0e0e0}}
.statement{{font-size:clamp(1.4rem,3vw,2rem);font-weight:200;line-height:1.3;max-width:28ch;margin:24px 0;letter-spacing:-.01em}}
.cols{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:24px;margin-top:24px}}
.cols .col h3{{font-size:1.15rem;font-weight:500;margin-bottom:8px}}
.cols .col p{{font-size:.92rem;color:#555;line-height:1.65}}
.cols .col .big{{font-size:2.4rem;font-weight:200;color:#002FA7;margin-top:12px}}
footer{{background:#0a0a0a;color:rgba(255,255,255,.7);padding:40px 24px;text-align:center;font-size:.85rem}}
footer a{{color:rgba(255,255,255,.9)}}
.badge{{display:inline-block;font-size:.72rem;font-weight:600;padding:2px 10px;background:#002FA7;color:#fff;margin:2px 4px 2px 0}}
</style>
</head>
<body>

<div class="hero">
  <h1>安史之乱<br><em>中唐续命</em></h1>
  <p>一个对话驱动的历史策略游戏。从前期验证到工程落地，超过一半的工作量由 AI Agent 完成。下面是工具、过程和成果。</p>
</div>

<!-- ===== 一、AI 工具与工作流（前置） ===== -->
<section>
<div class="wrap">
  <div class="sub">TOOLS &amp; WORKFLOW</div>
  <h2>用了哪些 AI 工具</h2>
  <p class="lead">整个项目超过一半的工作量由 AI Agent 完成。前期用 Codex 跑通概念，Claude Code 做主力编码与架构规划，同时负责 API 搭建和数据接入，seedream 负责全部美术素材。</p>
  <div class="kpi-row">
    <div class="kpi"><div class="num">&gt;50%</div><div class="label">工作量由 AI 完成</div></div>
    <div class="kpi"><div class="num">5+</div><div class="label">AI 模型参与</div></div>
    <div class="kpi"><div class="num">3</div><div class="label">主力 AI 工具</div></div>
    <div class="kpi"><div class="num">59</div><div class="label">AI 生成美术素材</div></div>
  </div>
  <div class="grid-3">
    <div class="card">
      <span class="tag">前期验证</span>
      <h3>Codex</h3>
      <p>拆需求、验可行性、跑通概念原型。先确认这条路能走通，再投入工程。</p>
    </div>
    <div class="card">
      <span class="tag">编码 + 规划</span>
      <h3>Claude Code</h3>
      <p>API 搭建、架构规划、数据接入，以及与其他 AI 模型的编排协作。</p>
    </div>
    <div class="card">
      <span class="tag">美术生成</span>
      <h3>seedream</h3>
      <p>43 位人物立绘、16 张事件插图、5 幕背景，全部由 seedream 逐张生成。</p>
    </div>
    <div class="card">
      <span class="tag">其他参与</span>
      <h3>gpt5.6sol / deepseek-v4pro / kimi-k2.7 / qwen3.8max</h3>
      <p>按场景在多个模型间切换，人物议政、回合推演、文书润色各走各的配置。</p>
    </div>
  </div>
  <h3 style="margin-top:40px;margin-bottom:16px;font-size:1rem;font-weight:500">开发留痕</h3>
  <div class="shot-grid">{screenshot_grid()}</div>
</div>
</section>

<!-- ===== 二、项目介绍 ===== -->
<section>
<div class="wrap">
  <div class="sub">THE PROJECT</div>
  <h2>安史之乱：中唐续命</h2>
  <p class="lead">天宝十五载，渔阳鼙鼓动地来。你扮演大唐最高决策者，通过召见、廷议、密诏与御笔诏书，重新推动这台失序的国家机器。</p>
  <img src="{court}" alt="紫宸殿朝堂" style="width:100%;max-height:420px;object-fit:cover;margin-bottom:24px">
  <div class="kpi-row">
    <div class="kpi"><div class="num">43</div><div class="label">位人物</div></div>
    <div class="kpi"><div class="num">16</div><div class="label">张事件插图</div></div>
    <div class="kpi"><div class="num">5</div><div class="label">幕战役</div></div>
    <div class="kpi"><div class="num">16</div><div class="label">地区地图</div></div>
  </div>
</div>
</section>

<!-- ===== 三、核心玩法 ===== -->
<section>
<div class="wrap">
  <div class="sub">GAMEPLAY</div>
  <h2>六种玩法</h2>
  <p class="lead">对话驱动，策略结算。模型管表达，规则管结算。</p>
  <div class="grid-3">
    <div class="card"><h3>紫宸殿奏对</h3><p>朝堂、密诏、远奏三种场景，人物反应各不相同。关系、信任与诺言跨回合保留。</p></div>
    <div class="card"><h3>廷议集议</h3><p>选二至六人入殿，单次调用生成整场辩论。谁发难、谁打断、谁补台，后发言者读前臣意见。</p></div>
    <div class="card"><h3>御笔拟诏</h3><p>自由写下旨意，文书模型润色为唐廷风格圣旨，拆解为可校验的朝堂行动。</p></div>
    <div class="card"><h3>军令调度</h3><p>十六地区地图、军队调动、会战、围城与补给。军令先入队，颁诏时统一执行。</p></div>
    <div class="card"><h3>国策经略</h3><p>中枢整饬、军镇经略、河朔联络、财赋民生四条分支，每回合推进一项。</p></div>
    <div class="card"><h3>人物记忆</h3><p>每回合自动提炼关键记忆，按重要度定寿命。重要的永不遗忘，琐碎的几回合后归档。</p></div>
  </div>
</div>
</section>

<!-- ===== 四、推演架构 ===== -->
<section>
<div class="wrap">
  <div class="sub">ARCHITECTURE</div>
  <h2>推演架构</h2>
  <p class="statement">模型负责说得像，<br>规则负责算得准。</p>
  <p class="lead">权威结果先由规则算出，模型只读结果写叙事，不允许叙事反过来改状态。删掉全部叙事缓存，结局一个不变。</p>
  <div class="grid-3">
    <div class="card"><span class="tag">01</span><h3>冻结快照</h3><p>兵力、钱粮、路线、战斗，确定性规则先行。</p></div>
    <div class="card"><span class="tag">02</span><h3>推演提案</h3><p>模型生成 JSON 提案与邸报叙事。</p></div>
    <div class="card"><span class="tag">03</span><h3>本地校验</h3><p>白名单、目标与幅度，越权的写入被拒。</p></div>
    <div class="card"><span class="tag">04</span><h3>写入裁决</h3><p>民心、动乱、士气、补给、忠诚，允许的才写入。</p></div>
    <div class="card"><span class="tag">05</span><h3>史官纪事</h3><p>自动存档，可回放，可追溯。</p></div>
  </div>
</div>
</section>

<!-- ===== Agent 应用细节 ===== -->
<section>
<div class="wrap">
  <div class="sub">AGENT APPLICATION</div>
  <h2>Agent 怎么用的</h2>
  <p class="lead">不是"调一下 API"那么简单。这个项目里，Agent 有记忆、有上下文、能自己查盘面、能并行工作，前端和后端各管一摊。</p>
  <div class="grid-3">
    <div class="card">
      <span class="tag">记忆</span>
      <h3>跨回合人物记忆</h3>
      <p>每条记忆带重要度（1-5）和标签。重要度 5 永不遗忘，重要度 1 三个回合后自动归档。支持按标签跨人物召回，按回合范围回溯历史。</p>
    </div>
    <div class="card">
      <span class="tag">上下文</span>
      <h3>有状态 Session</h3>
      <p>AgentSession 保持跨调用对话历史，add_user / add_assistant / add_tool_result 逐轮累积。每个 Agent 角色都能在 session 里看到之前的对话，不会"失忆"。</p>
    </div>
    <div class="card">
      <span class="tag">Tool-Use</span>
      <h3>模型自查盘面</h3>
      <p>推演模型带 tool-use，能自己调用查看地区、军队、财政、局势的工具。先查再答，不是凭印象编。</p>
    </div>
    <div class="card">
      <span class="tag">多 Agent</span>
      <h3>七种角色各司其职</h3>
      <p>大臣（廷议发言）、中书舍人（纪要）、人物（奏对）、廷议编剧（单次调用生成整场辩论）、推演（世界结算）、邸报（叙事）、史官（长期记忆）。每个角色有独立的系统提示、采样参数和模型配置。</p>
    </div>
    <div class="card">
      <span class="tag">前后端</span>
      <h3>前端 React + 后端 FastAPI</h3>
      <p>前端 React 19 SPA，通过 Vite proxy 访问后端。后端 FastAPI 按域拆路由（廷议 / 诏令 / 回合 / 设置）。SSE 真流式，逐字推到前端。所有 API 调用收口到 api.ts，游戏状态集中在 App.tsx。</p>
    </div>
    <div class="card">
      <span class="tag">流式</span>
      <h3>SSE 逐字输出</h3>
      <p>廷议、召见、邸报走 SSE 流式接口。模型边生成，前端边渲染。廷议剧本单次调用，按分隔符拆到各位大臣头上，边写边分。</p>
    </div>
  </div>
</div>
</section>

<!-- ===== 五、AI 美术 ===== -->
<section>
<div class="wrap">
  <div class="sub">AI ART · seedream</div>
  <h2>四十三位人物</h2>
  <p class="lead">全部由 seedream 逐张生成，覆盖三省六部、禁军、边镇与燕廷。</p>
  <div class="img-grid">{portrait_grid()}</div>
</div>
</section>

<section>
<div class="wrap">
  <div class="sub">AI ART · seedream</div>
  <h2>十六张事件插图</h2>
  <p class="lead">五幕关键节点各有一幅，全部由 seedream 生成。</p>
  <div class="img-grid events">{event_grid()}</div>
</div>
</section>

<!-- ===== 六、成果 ===== -->
<section>
<div class="wrap">
  <div class="sub">OUTPUT</div>
  <h2>做到什么程度</h2>
  <div class="kpi-row">
    <div class="kpi"><div class="num">3.2K</div><div class="label">Python 源码 · 行</div></div>
    <div class="kpi"><div class="num">5.8K</div><div class="label">前端 TSX/CSS · 行</div></div>
    <div class="kpi"><div class="num">64</div><div class="label">后端测试 · 通过</div></div>
    <div class="kpi"><div class="num">15</div><div class="label">后端模块</div></div>
  </div>
  <div class="grid-3">
    <div class="card"><h3>Agent 运行时</h3><p>零第三方依赖，自带 session 记忆与 tool-use 循环，模型能自查盘面再回答。</p></div>
    <div class="card"><h3>人物记忆系统</h3><p>每回合自动提炼，TTL 衰减，按标签跨人物召回。</p></div>
    <div class="card"><h3>长期局势追踪</h3><p>承办人推进公式、惯性漂移、办结与恶化判定。</p></div>
    <div class="card"><h3>供应商自适应</h3><p>一个 OpenAI 兼容接口，自动识别 DeepSeek、DashScope、MiniMax 并注入参数。</p></div>
    <div class="card"><h3>三角色模型路由</h3><p>人物、推演、文书各走各的配置，独立更换供应商。</p></div>
    <div class="card"><h3>真流式编排</h3><p>SSE 逐字输出，廷议剧本单次调用边写边分到各位大臣。</p></div>
  </div>
</div>
</section>

<!-- ===== 七、设计决策 ===== -->
<section>
<div class="wrap">
  <div class="sub">DECISIONS</div>
  <h2>三个不妥协</h2>
  <div class="cols">
    <div class="col">
      <h3>权威与叙事分离</h3>
      <p>数值先由规则算定，模型写的内容不许改状态。删掉全部叙事缓存，结局一个不变。</p>
    </div>
    <div class="col">
      <h3>单次调用廷议</h3>
      <p>整场廷议一次生成。谁发难、谁打断、谁补台，后发言的人会先读前面几位大臣的意见。</p>
    </div>
    <div class="col">
      <h3>记忆会遗忘</h3>
      <p>每条记忆按重要度定寿命。重要的永不遗忘，琐碎的几个回合后自动归档，不再参与召回。</p>
    </div>
  </div>
</div>
</section>

<footer>
  <p>安史之乱 · 中唐续命 · 一人 + 一群 Agent · 2026</p>
  <p style="margin-top:8px;font-size:.78rem;opacity:.6">模型 · gpt5.6sol / deepseek-v4pro / kimi-k2.7 / qwen3.8max · 图像 · seedream</p>
</footer>

</body>
</html>"""

OUT.write_text(html, encoding="utf-8")
print("wrote", OUT)
print("size KB:", len(html.encode("utf-8")) // 1024)
