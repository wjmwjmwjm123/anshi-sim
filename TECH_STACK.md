# 安史之乱 · 技术栈与架构

## 总体架构

```
前端 (React SPA)
  ↕ SSE / REST
后端 (FastAPI)
  ├── 路由层 (routes/)     ← HTTP 接口
  ├── Agent 工厂 (agents.py) ← 角色工厂 + 执行器
  ├── AI 层 (ai.py)        ← LLM 调用 + 供应商适配
  ├── 提示词 (prompts.py)  ← 集中管理
  └── 规则层 (core/management/campaign/strategy) ← 确定性结算
```

## 技术选型

| 层 | 技术 | 理由 |
|---|---|---|
| 前端 | React 19 + Vite | 快速原型，单文件 SPA |
| 后端 | FastAPI + Pydantic | 异步 SSE、类型校验 |
| 存储 | SQLite WAL | 零配置、单文件存档 |
| LLM | OpenAI 兼容 API | 供应商无关 |
| 流式 | httpx SSE + Server-Sent Events | 真流式，逐字输出 |

## AI 层设计

### Agent 工厂模式

每种 LLM 角色有独立的工厂函数，返回 `CouncilAgent` dataclass：

```python
@dataclass
class CouncilAgent:
    name: str
    role: str           # 决定用哪个 model 配置
    system_prompt: str
    config: LLMConfig
    temperature: float
    top_p: float | None
```

工厂函数：
- `create_minister_agent()` — 廷议大臣
- `create_secretary_agent()` — 中书舍人纪要
- `create_character_agent()` — 人物奏对
- `create_court_script_agent()` — 廷议剧本（单次调用）
- `create_simulator_agent()` — 世界推演
- `create_gazette_agent()` — 邸报
- `create_narrator_agent()` — 史官叙事

### 执行器

- `run_agent()` — 非流式，返回完整文本
- `run_agent_stream()` — 真流式，yield 每个 delta
- `run_agent_json()` — JSON 执行，带多级修复

### 模型配置（三角色）

```python
# chat       → 人物扮演、廷议（默认模型）
# simulation → 回合推演、世界模拟（可配更强模型）
# utility    → 文书润色、纪要（可配更快模型）
```

每个角色可独立配置 API key、base_url、model。`for_role()` 让 simulator/extractor 走 advanced model。

### 供应商适配

自动检测 base_url 中的供应商标识，注入特定参数：

```python
def provider_extra_body(base_url: str) -> dict | None:
    # DeepSeek → 关闭思考模式
    # DashScope → 关闭思考模式
    # MiniMax → 关闭思考模式
    # 其他 → None（无额外参数）
```

### 温度/采样参数

每种角色有默认采样参数，定义在 `_ROLE_SAMPLING` 字典中：

| 角色 | temperature | top_p |
|---|---|---|
| minister | 0.65 | 0.9 |
| secretary | 0.4 | 0.5 |
| character | 0.7 | 0.9 |
| simulator | 0.5 | 0.5 |
| court_script | 0.75 | 0.9 |
| gazette | 0.4 | 0.5 |

## SSE 事件协议

### 廷议流 `/api/council/stream`

```
data: {"type": "council_start", "topic": "...", "round": 1}
data: {"type": "speech_start", "name": "哥舒翰", "round": 1}
data: {"type": "speech_delta", "name": "哥舒翰", "delta": "臣"}
data: {"type": "speech_delta", "name": "哥舒翰", "delta": "以为"}
data: {"type": "speech_end", "name": "哥舒翰", "reply": "臣以为当固守...", "round": 1}
...
data: {"type": "minutes", "round": 1, "text": "群臣各陈己见..."}
data: {"type": "emperor_options", "is_final": false}
data: {"done": true}
```

### 结算流 `/api/resolve/stream`

```
data: {"type": "snapshot", "data": {...}}     # 完整结算快照
data: {"type": "gazette_start"}
data: {"type": "gazette_delta", "delta": "至"}
data: {"type": "gazette_delta", "delta": "德"}
...
data: {"type": "gazette_end", "gazette": "至德二载六月..."}
data: {"done": true}
```

## 提示词管理

所有提示词集中在 `prompts.py`，不硬编码在 agent 或路由中：

| 提示词 | 用途 |
|---|---|
| `MINISTER_SYSTEM` | 廷议大臣发言规则 |
| `COURT_SCRIPT_SYSTEM` | 廷议剧本编排规则 |
| `SECRETARY_SYSTEM` | 中书舍人纪要规则 |
| `CHARACTER_SYSTEM` | 人物奏对规则 |
| `NARRATOR_SYSTEM` | 史官叙事规则 |
| `WORLD_PROPOSAL_SYSTEM` | 世界推演规则（含邸报） |
| `GAZETTE_SYSTEM` | 邸报叙事风格 |

## 路由模块

`main.py` 只做初始化和路由挂载，具体端点按职责拆分：

| 模块 | 路由 |
|---|---|
| `routes/council.py` | audience, council, council/stream, secret-edicts |
| `routes/decree.py` | decrees, directives, events, army/move |
| `routes/game.py` | turn, resolve, resolve/stream, saves, snapshot, policies |
| `routes/settings.py` | model-config, token-stats, health |
