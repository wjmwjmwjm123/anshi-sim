# v0.6.0 — 四维升级

> 2026-07-19 · 基于 v0.5.0 的四项体验与架构升级

---

## 一、地图战略仪表板

### 军队可视化
- 地图上每个地区叠加势力军队标记（唐军绿盾、燕军红盾），同地多军自动错位排列
- 点击军队标记弹出详情弹窗：兵力、士气、补给、当前军令、可调往邻郡列表
- 军队数量徽章与围城火焰动画标记

### 路线系统
- 选中军队后，SVG 虚线高亮从当前驻地到所有相邻地区的可行军路线
- 路线动画脉冲闪烁，配合行军信息一目了然

### 地区详情面板
- 点击地区标记展开详情面板：控制方（color-coded）、民心、动乱、城防、税率
- 该地区驻军列表（含唐/燕 color bar）
- 围城进度条（progress 实时显示）
- 图例增加唐军/燕军标记

### 改动文件
- `apps/web/src/WorldMap.tsx` — 完全重写
- `apps/web/src/maps.css` — 新增 80+ 行军队/围城/路线样式
- `apps/web/src/components/screens.tsx` — RegionsView 传递 strategy 数据

---

## 二、奏报阅读体验

### 卷轴式邸报
- 回合结算报告重新设计：唐字圆形封印 + 章节标题 + 正文缩放风格
- 四字章节标题自动识别（`一、` 至 `十、` 变为带红标的 h4）
- 流式输出时打字光标闪烁动画

### 关键词智能高亮
- 正向动词（升/增/加/复/授/募/赈/修/改）→ 绿色下划线
- 负向动词（降/减/削/裁/罢/夺/遣）→ 红色下划线
- 其他动词（调/拨/发/迁/徙）→ 红棕色下划线

### 诏令执行结果卡片
- 回合结算中所有诏令执行情况汇总展示
- 成功 ✓ 绿色、失败 ✗ 红色，附带效果说明

### 改动文件
- `apps/web/src/components/screens.tsx` — HistoryView 新增 `highlightKeywords()`、`renderReportBody()`
- `apps/web/src/reports.css` — 新增 50+ 行卷轴头、高亮、结果卡片样式
- `apps/web/src/styles.css` — 编年史样式微调

---

## 三、人物关系面板

### 召见界面升级
- `AudienceDrawer` 左侧增加关系指示器：
  - **信任**（trust）：绿色高数值 / 红色低数值
  - **恩宠**（favor）：带正负号显示
  - **畏惧**（fear）：红色高亮高数值
- 未兑现诺言数量标签，hover 显示承诺列表

### 对话历史回顾
- 召见时折叠面板显示此前与该人物的全部奏对记录
- 每条记录标注回合数与场景（朝堂/密诏/远奏），超过 80 字自动截断
- 皇帝发言与大臣发言左右分色

### 改动文件
- `apps/web/src/components/panels.tsx` — AudienceDrawer 接受 conversation prop
- `apps/web/src/App.tsx` — 传递 snap.conversation
- `apps/web/src/styles.css` — 新增关系面板、对话回顾样式

---

## 四、人物记忆系统

### 每回合自动提炼
- 回合结算后，utility 模型自动分析邸报内容，提取关键记忆
- 每条记忆包含：所属人物、摘要（15-40 字）、重要度（1-5）、标签（2-4 个）
- 同时写入 ConversationState（内存）和 SQLite event_memories 表（持久化）

### TTL 衰减机制
```
importance 5 → 永不遗忘
importance 4 → 24 回合后过期
importance 3 → 12 回合后过期
importance 2 → 6 回合后过期
importance 1 → 3 回合后过期
```
过期记忆自动归档（archived=1），不再参与召回。

### 跨角色标签召回
- `recall_by_tags()` 支持按主题标签跨人物搜索记忆
- `recall_by_time()` 支持按回合范围回溯历史
- 前端召见时展示人物近期记忆

### 改写文件
- `src/anshi/conversation.py` — Memory 增加 tags/expires_at/ttl、新增 expire_memories/recall_by_tags/recall_by_time
- `src/anshi/ai.py` — 新增 extract_turn_memories() 函数
- `src/anshi/storage.py` — 新增 event_memories 表 + 3 个 CRUD 方法
- `apps/api/routes/game.py` — 回合结算后自动调用记忆提取与持久化

---

## 五、Agent 架构升级

### 轻量 Agent 运行时
- **新文件** `src/anshi/agent_runtime.py`：零第三方依赖的 Agent 运行时
- **AgentSession**：带对话历史累积的有状态 session，支持 `add_user()`/`add_assistant()`/`add_tool_result()`
- **ToolRegistry**：统一的工具注册中心，从 `build_game_tools()` 输出自动构造，提供 OpenAI function calling 格式
- **run_session_loop()**：session + tool-use 循环执行器
- **run_agent_stream_with_session()**：流式 + session 执行器

### CouncilAgent 升级
- 新增 `session: AgentSession | None` 字段 — 支持跨调用记忆
- 新增 `tools: ToolRegistry | None` 字段 — 支持 tool-use
- 新增 `run_agent_with_tool_loop()` — 带 session 和 tool-use 的执行
- 新增 `run_session_stream()` — 流式 session 执行
- 旧 `run_agent()`/`run_agent_stream()`/`run_agent_json()` 全部保持兼容

### 改写文件
- `src/anshi/agent_runtime.py` — 新文件
- `src/anshi/agents.py` — CouncilAgent 扩展 + 新执行函数

---

## 六、长期局势系统

### 承办人推进公式
```
修正率 = (能力-50) × 1.6% + (忠诚-50) × 0.6% + 5% baseline
范围：1% ~ 80%
```
示例：哥舒翰（能力78/忠诚62）→ 57% 推进率，每回合 +1~2 进度。

### 惯性漂移
- 无承办人时局势自动恶化（tension +1~3/月）
- 惯性因子逐月衰减
- 进度 ≥100 → 办结，tension ≥95 → 恶化失败

### 推进日志
- 每回合记录承办人推进明细（回合/人物/增量/修正率），上限 20 条

### HITL 纠偏决策
- 世界推演 agent prompt 增加决策块指令
- LLM 可在邸报末尾插入 `<<DECISION>>...<<END>>` 块
- 每个决策块含标题、上下文（已试方法+卡点）和 2-3 个互斥选项

### 改写文件
- `src/anshi/management.py` — IssueState 扩展 + assignee_progress_rate() + _world_tick 惯性漂移
- `src/anshi/ai.py` — 世界推演 prompt 增加 HITL 段

---

## 技术统计

| 维度 | v0.5.0 | v0.6.0 | 变化 |
|------|--------|--------|------|
| Python 源码行数 | ~2,500 | ~3,200 | +700 |
| 前端 TSX/CSS 行数 | ~5,160 | ~5,800 | +640 |
| 新增概念模块 | 0 | 3（AgentRuntime/MemoryStore/IssueTracker） | |
| SQLite 新增表 | 0 | 1（event_memories） | |
| 测试通过 | 64 | 61（3 个已存在集成测试未修复） | |
