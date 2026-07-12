# 技术栈与应用层文档

## 概览

安史之乱·中唐续命（anshi-sim）是一个基于 LLM 的历史策略模拟游戏。玩家扮演唐朝皇帝，通过召见大臣、廷议、拟诏、密诏等方式推动局势发展。

## 技术栈

### 后端

| 技术 | 用途 |
|---|---|
| Python 3.13+ | 运行时 |
| FastAPI | HTTP API 框架 |
| Pydantic v2 | 请求/响应数据校验 |
| httpx | HTTP 客户端（LLM 流式调用） |
| uvicorn | ASGI 服务器 |
| SQLite（via GameStore） | 本地存档、管理状态、回合记录 |

### 前端

| 技术 | 用途 |
|---|---|
| React 18 | UI 框架 |
| TypeScript | 类型安全 |
| Vite | 构建工具 |
| Lucide React | 图标库 |
| SSE（Server-Sent Events） | 廷议流式推送 |

### LLM 集成

| 模型角色 | 环境变量前缀 | 用途 |
|---|---|---|
| 人物议政（chat） | `CHAT_*` / `OPENAI_*` | 大臣奏对、廷议发言 |
| 回合推演（simulation） | `SIMULATION_*` | 世界推演、史官叙事 |
| 文书与记忆（utility） | `UTILITY_*` | 诏书润色、廷议纪要 |

支持的 LLM 提供商：OpenAI 兼容接口（含火山引擎 Ark、LongCat 等）。

## 应用层架构

### Agent 工厂模式（仿照 ming_sim）

```
src/anshi/
├── agents.py      # Agent 工厂（CouncilAgent + 工厂函数 + 执行函数）
├── prompts.py     # 提示词集中管理（所有 system/user prompt 模板）
├── ai.py          # LLM 调用层（chat_completion / stream_chat_completion）
├── token_stats.py # Token 记账
└── ...
```

**Agent 工厂**：每个 LLM 角色有独立的工厂函数，返回配置好的 `CouncilAgent` 对象：

```python
agent = create_minister_agent(character, topic, context, ...)
agent = create_secretary_agent(topic, speeches, ...)
agent = create_character_agent(character, topic, scene="court", ...)
agent = create_narrator_agent()
agent = create_simulator_agent()
```

**执行函数**：

| 函数 | 模式 | 用途 |
|---|---|---|
| `run_agent` | 非流式 | 返回完整文本，带 fallback |
| `run_agent_stream` | 真流式 | yield 每个 delta 片段，逐字推送 |
| `run_agent_json` | 非流式 + JSON 修复 | 返回解析后的 JSON，带 sanitizer 兜底 |

**模型派生**（`for_role`）：

```python
# 推演/打分角色走 advanced_model（更强的模型），其余走 main model
cfg = for_role(llm_config, "simulator")  # → advanced_model
cfg = for_role(llm_config, "minister")   # → main model
```

### 廷议流程

```
1. 前端发起 POST /api/council/stream
2. 后端依次为每位大臣创建 minister_agent
3. 调用 run_agent_stream 真流式生成发言
4. SSE 事件推送：
   - speech_start  → 前端创建占位元素
   - speech_delta  → 前端逐字追加文本
   - speech_end    → 前端显示完整发言 + 态度标签
5. 全部发言后，secretary_agent 生成《会议纪要》
6. 第二轮：每位大臣收到纪要 + 上一位发言 + 皇帝谕旨
7. 最终纪要 → 皇帝决策面板
```

### SSE 事件类型

| 事件 | 字段 | 说明 |
|---|---|---|
| `speech_start` | `character_id`, `name`, `round` | 大臣开始发言 |
| `speech_delta` | `character_id`, `delta` | 流式文本片段 |
| `speech_end` | `character_id`, `name`, `reply`, `stance`, `round` | 发言结束 |
| `minutes` | `round`, `text` | 中书舍人纪要 |
| `emperor_options` | — | 显示皇帝决策面板 |
| `done` | — | 本轮结束 |

### Token 记账

每次 LLM 调用自动记录 token 用量（需 provider 返回 usage 字段）：

```
GET /api/token-stats → { total_calls, total_tokens, recent: [...] }
```

### LLMConfig 扩展

```python
@dataclass(frozen=True)
class LLMConfig:
    api_key: str
    base_url: str
    model: str
    timeout: float = 20.0
    advanced_model: str = ""       # 推演/打分专用更强模型
    advanced_base_url: str = ""    # advanced 角色专用网关
    advanced_api_key: str = ""     # advanced 角色专用 key
```

环境变量：`ADVANCED_MODEL`、`ADVANCED_BASE_URL`、`ADVANCED_API_KEY`。

### JSON 修复（sanitize_json）

LLM 输出可能包含 markdown fence、控制字符、不完整 JSON。`sanitize_json` 依次尝试：

1. 原文直解
2. 去除 ```json fence 后解析
3. 截取最外层 `{...}` + 去控制字符后解析
4. 截取最外层 `[...]` + 去控制字符后解析

### 错误处理

- LLM 调用失败 → 使用 fallback 文本（中文模板），不阻断游戏
- 流式调用中断 → 已推送的片段保留，发言标记为完成
- 网络超时 → 静默降级，前端显示模板文本

## 与 ming_sim 的对应关系

| ming_sim | anshi-sim | 说明 |
|---|---|---|
| `agno.Agent` | `CouncilAgent` | 轻量替代，不依赖 agno |
| `create_season_simulator_agent` | `create_simulator_agent` | 工厂函数 |
| `run_agent_text` | `run_agent` | 非流式执行 |
| `run_agent_stream_text` | `run_agent_stream` | 真流式执行 |
| `parse_agent_json` | `sanitize_json` | JSON 修复 |
| `GameContent` | `prompts.py` | 提示词集中管理 |
| `for_role` | `for_role` | 模型按角色派生 |
| `record_stream_metrics` | `token_stats.record` | Token 记账 |
| `LLMUnavailable` | 直接异常冒泡 | 错误处理 |

## 运行

```bash
# 安装依赖
pip install -e .

# 启动后端
python -m apps.api.run

# 启动前端（开发模式）
cd apps/web && npm run dev
```

## 环境变量

```bash
# 人物议政模型
CHAT_API_KEY=sk-...
CHAT_BASE_URL=https://api.openai.com/v1
CHAT_MODEL=gpt-4o-mini

# 回合推演模型（可选，更强的模型）
SIMULATION_API_KEY=sk-...
SIMULATION_MODEL=gpt-4o

# 文书模型
UTILITY_API_KEY=sk-...
UTILITY_MODEL=gpt-4o-mini

# 高级模型（推演/打分专用，可选）
ADVANCED_MODEL=deepseek-reasoner
ADVANCED_BASE_URL=https://api.deepseek.com/v1
ADVANCED_API_KEY=sk-...
```
