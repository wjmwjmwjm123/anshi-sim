# 《安史之乱：中唐续命》架构审计与目标架构

> 状态：Pre-production v0.1  
> 审计日期：2026-07-11  
> 参考代码：`E:\AGENT\参考\ming-salvage-sim-0.4.15`  
> 新工程建议路径：`E:\AGENT\anshi-sim`  
> 原则：参考项目只作为经验与反例，不在 `tang_engine` 复制版上继续堆叠

## 1. 审计范围与方法

本审计使用本地 `.codegraph` 索引和源文件交叉分析。索引状态为最新：233 个文件、4,689 个符号节点、10,387 条关系；其中 Python 108 文件、前端 JavaScript/TypeScript/TSX 105 文件。

审计重点：回合主链、LLM 调用数、状态权威、数据库副作用、并发、暂停恢复、API 边界、测试与重放能力。历史与数据质量另见 [research-data-audit.md](../audit/research-data-audit.md)，完整数值合同另见 [numerical_design.md](numerical_design.md)。

## 2. 参考项目真实结构

### 2.1 规模

| 对象 | 现状 | 影响 |
|---|---:|---|
| `web_app.py` | 198 KB、372 个符号 | 路由、存档、DTO、会话和配置集中 |
| API 路由 | 83 条 | 缺少按领域隔离的应用服务层 |
| `GameDB` | 19 个 Mixin、约 46 表 | 域已拆文件，但公共对象过宽 |
| `session.py` | 77 个符号 | 回合、人物、任命、存档、决策均汇聚 |
| `simulation.py` | 70 个符号 | payload、抽取、清洗和兼容逻辑混合 |
| `issues.py` | 86 个符号 | 事件、局势和大量数值落库规则集中 |
| 前端 `types.ts` | 605 个符号 | 整局快照 DTO 膨胀，前后端同名 `GameState` 异义 |

### 2.2 当前回合链

```text
GameSession.resolve_turn
  1. preresolve 自动存档
  2. 固定财政先落账
  3. 程序硬触发 seed issue
  4. 读取章节记忆、密令
  5. simulator Agent 生成整篇邸报
  6. 可选：从邸报解析 HITL 决策，进程内暂停
  7. extractor 第 1 模块串行暖缓存
  8. extractor 后 3 模块线程池并行
  9. 解析/清洗并由 apply_score_extraction 落库
 10. chapter-memory Agent 生成章节记忆
 11. minister-recap Agent 生成人物纪要
 12. issue inertia、帝国修正、结局、回合推进
```

当前代码已经比旧文档更进一步：4 个 extractor 不是全部串行，而是“1 个串行暖缓存 + 3 个并行”。但典型回合仍包含：1 次 simulator、4 次 extractor、1 次章节记忆、1 次人物纪要，合计 7 次模型调用；拟旨另加 1 次，人物召对另计。解析失败还可能追加 sanitizer，结局回合再追加 ending-summary。

### 2.3 当前值得保留的经验

- CLI、Web 共用 `GameSession`，避免核心玩法双实现。
- 内容 JSON 与运行时 DB 分离，支持剧本覆盖。
- extractor 已尝试稳定共享前缀、先暖缓存再并发。
- 结算前自动存档，为模型故障保留人工回滚点。
- SQLite Mixin 按领域拆分，内容、人物、军队和事件已有成熟模型。
- SSE 能把阶段、思考和正文实时推到前端。

## 3. 审计发现

### P0-1：权威结果从叙事反向抽取

数值结果不是先由规则算出，而是 simulator 写叙事后由 4 个 extractor 解释文本。这导致同一事实重复传输、模型格式漂移、清洗器成为数值正确性的最后防线，也让同输入难以重放。

**决定**：新项目先生成不可变 `TurnResult`，叙事只读结果，不允许叙事反写权威状态。

### P0-2：回合不是原子事务

固定财政在模型调用前已经落账。`LLMUnavailable` 会冒泡，其他 simulator 异常则走简化报告并推进回合；恢复依赖玩家加载 `preresolve` 备份。回合的输入、随机种子、Agent 候选、权威结果和叙事没有形成一个可提交/回滚单元。

**决定**：在只读快照上完成所有候选与确定性计算，单事务提交 `commands + turn_result + state_delta + events`；叙事在事务之后生成。

### P0-3：暂停决策只在进程内

`_pending_decisions`、`_pending_resolve_ctx` 和作弊上下文在进程内保存，重启即丢。注释中同时存在“保留使用”和“已废弃”语义，实际 API 仍暴露继续结算路由。

**决定**：决策点、快照哈希、上下文引用和已选项全部落库；恢复时不需要重跑已完成阶段。

### P0-4：LLM、规则和数据库权限混杂

人物工具、执行评估、清洗和 `apply_score_extraction` 共同决定结果。部分任命只由 LLM 判断史实合理性，代码只做最小查重。Agent 能间接触发广泛状态修改。

**决定**：Agent 只能返回候选 `Command`；权限、资源、日期、地图、知识边界和状态转换由 application/core 校验。

### P1-1：共享 SQLite 连接与线程模型不清晰

DB 使用 `check_same_thread=False`，SSE 用 worker 线程调用同步回合，extractor 再开线程池。注释依赖“游戏单写者”假设，但缺少显式每战役锁、工作单元和并发请求拒绝机制。

**决定**：每个 campaign 一个异步锁；写入只在回合提交阶段发生；Agent 并行阶段只读取不可变快照，不共享 DB 连接。

### P1-2：API 和 DTO 过宽

`web_app.py` 同时承担 FastAPI app、菜单、存档、游戏路由、序列化、场景管理和模型配置。前端每次接收完整 `GameState` 快照，动态变化会扩大序列化和认知成本。

**决定**：按 `campaign/court/turn/map/codex` 拆 router；返回领域 DTO 和 `TurnDiff`，仅初始化/读档返回完整快照。

### P1-3：失败降级语义不一致

模型不可用有时中止、有时跳过 extractor 并推进、有时使用拼接记忆。玩家难以知道该回合是否完整结算。

**决定**：规则结算永不依赖 LLM；Agent 超时只损失建议或叙事。所有降级写入 `agent_runs` 并在 UI 显示，不改变规则结果。

### P1-4：典型回合调用仍多

并行 extractor 缩短了部分墙钟，但没有消除 4 次重复阅读和后续 2 次记忆调用。上下文越长，成本仍随战役增长。

**决定**：权威结算 0 次模型调用；需要 AI 候选时按脏域并行 0-3 次；叙事默认 1 次；记忆用结构化事件程序压缩，只有章节终点才调用高级模型。

### P1-5：测试基线不稳定

本机 `pytest -q` 收集 49 项：35 通过、14 失败。13 项来自 Windows 上 `NamedTemporaryFile` 保持打开时 SQLite 无法再次打开同一路径；另 1 项是 `build_simulator_payload` 新增 `army_held_arms_all()` 后测试替身未更新。这说明跨平台测试夹具和接口替身没有形成稳定合同。

**决定**：新项目使用 pytest `tmp_path` 创建未占用路径；repository 以 Protocol/接口替身；CI 至少覆盖 Windows 和 Linux。

### P2：可维护性问题

- 模块级 `_content` 隐式注入。
- `GameState` 前后端同名异义。
- 规则存在于 DB Mixin、Agent 工具、清洗器和 issue 模块多处。
- `try/except Exception` 吞掉记忆和密令异常。
- 自动存档失败静默。
- 大量 probe 与正式工具混在 `scripts/`。

这些问题不要求在参考项目上逐项重构；新工程通过边界设计直接避免。

## 4. 新工程路径

推荐新建独立项目，不在参考项目和 `tang_engine` 内开发：

```text
E:\AGENT\anshi-sim\
├── pyproject.toml
├── package.json
├── README.md
├── apps\
│   ├── api\                    # FastAPI 入口、router、SSE
│   ├── desktop\                # Electron 壳，仅负责桌面生命周期
│   └── web\                    # React/Vite 前端
├── src\anshi\
│   ├── core\                   # 纯 Python、无 DB/HTTP/LLM
│   │   ├── model\              # WorldState、Command、TurnResult、值对象
│   │   ├── rules\              # 战斗、补给、军令、财政、事件、结局
│   │   ├── calendar\           # 历法与事件时钟
│   │   └── reducer.py          # state + commands + seed -> result
│   ├── application\
│   │   ├── turn_service.py     # 回合编排与 campaign 锁
│   │   ├── court_service.py
│   │   ├── campaign_service.py
│   │   └── replay_service.py
│   ├── ai\
│   │   ├── orchestrator.py     # DAG、并发、超时、取消
│   │   ├── roles\              # 人物/军务/情报/政务/叙事/审校
│   │   ├── schemas\            # 严格候选输出
│   │   ├── context_builder.py  # 最小上下文、知识边界
│   │   ├── model_router.py
│   │   └── cache.py
│   ├── content\
│   │   ├── loader.py
│   │   ├── validator.py
│   │   └── source_registry.py
│   ├── persistence\
│   │   ├── schema\
│   │   ├── repositories\
│   │   ├── migrations\
│   │   └── unit_of_work.py
│   └── api\
│       ├── routers\            # campaign/court/turn/map/codex
│       ├── dto\
│       └── streaming.py
├── content\
│   ├── sources\                # 史料登记与逐条引用
│   ├── common\                 # 通用制度、兵种、地形
│   └── scenarios\
│       └── tongguan_756\
│           ├── manifest.json
│           ├── world.json
│           ├── regions.json
│           ├── routes.json
│           ├── armies.json
│           ├── characters.json
│           ├── relations.json
│           ├── events.json
│           ├── obligations.json
│           └── endings.json
├── research\
│   ├── raw\                    # 二轮调研只读快照
│   ├── normalized\             # 清洗后的研究实体
│   ├── audit\                  # 数据与史料审计
│   └── bibliography\           # 来源矩阵
├── tests\
│   ├── unit\
│   ├── contracts\
│   ├── scenarios\
│   ├── replay\
│   ├── monte_carlo\
│   └── ui\
└── tools\
    ├── content_audit\
    ├── balance_sim\
    └── benchmarks\
```

路径使用 ASCII 项目名，避免 Python、Node、打包器和 Steam 工具链在不同机器上的 Unicode 路径差异；游戏内显示名仍使用中文。

## 5. 目标领域模型

### 5.1 三个核心合同

```text
WorldState       某一游戏日的完整权威状态
Command          玩家或 AI 提交、尚未生效的意图
TurnResult       已校验并结算的不可变结果
```

函数合同：

```text
reduce(world_state, accepted_commands, rng_seed, elapsed_days) -> TurnResult
apply(world_state, turn_result) -> NewWorldState
```

两函数均为纯函数或逻辑纯函数，不访问网络、数据库和当前时间。相同输入必须得到相同输出。

### 5.2 权威状态与文本分离

权威层保存人、粮、财政点、日期、关系、军令、位置和事件状态。0-100 指标由底层派生。露布、奏对、朝报是可重新生成的展示层，删除叙事缓存不能改变游戏结果。

### 5.3 命令状态机

```text
draft -> validated -> accepted -> dispatched -> acknowledged
      -> executing -> completed | partial | refused | failed | superseded
```

每个状态转换记录原因、日期、责任人和来源命令。低忠诚不会直接等于叛变，可能表现为拖延、保守执行、虚报、拒绝或转投。

## 6. 目标回合流水线

```text
1. 冻结 snapshot + hash                                      <50 ms
2. 校验玩家命令、资源、权限、地图和冲突                         <50 ms
3. 按脏域启动只读 Agent：军务/情报/政务/对手意图              并行、可选
4. schema 校验 Agent 候选；非法或超时则丢弃                    <50 ms
5. reducer 确定性结算 + 生成 TurnResult                        <300 ms
6. 单事务提交 commands/result/state/events/seed                <100 ms
7. 立即返回 TurnDiff，前端恢复可操作                            P95 <8 s 含 AI
8. 叙事 Agent 读取 TurnResult 并行流式生成                      不阻塞下一步
9. 结构化记忆和审计日志入库                                   后台
```

关闭 LLM 时步骤 1-6 的完整回合 P95 小于 500 ms。联网模式的目标不是等待所有文本，而是 P95 8 秒内获得可操作的结构化结果；叙事首字 P95 小于 2 秒、完整文本 P95 小于 15 秒。

## 7. 多 Agent 设计

| Agent | 读取范围 | 输出 | 权威写权限 |
|---|---|---|---|
| 人物 | 自身记忆、知识、关系、当前议题 | 奏对、异议、命令草案 | 无 |
| 军事参谋 | 玩家已知军情、地形和军队 | 方案、假设、风险 | 无 |
| 情报分析 | 多源 claim，不读取隐藏真值 | 冲突点、复核建议 | 无 |
| 政务参谋 | 财政、民生、派系可见信息 | 代价与执行风险 | 无 |
| 对手意图 | 对手自己的局部状态 | 候选敌方命令 | 无，交 reducer |
| 历史导演 | 锚点、事件因果、偏离状态 | 事件候选 | 无，交 gate |
| 叙事 | 已提交 TurnResult | 露布、朝报、人物反应 | 无 |
| 审校 | 文本、结果、来源标签 | 矛盾报告 | 无 |

规则：

- 只启动与本回合脏域相关的 Agent。
- 68 名人物不常驻，只在召见或涉事时激活。
- 所有并行 Agent 共享同一个不可变快照，不互相修改状态。
- `turn_id + snapshot_hash + role + prompt_version` 构成幂等键。
- 高级模型默认每回合最多 1 次；小模型调用有总数、token 和超时预算。
- Agent 失败只降低信息或文本质量，不改变规则结算。

## 8. 存储与恢复

采用“命令日志 + 周期快照”，不引入完整事件溯源框架：

- 每回合保存 `commands`、`turn_result`、`rng_seed`、`state_hash_before/after`。
- 每 5 回合、重大事件和手动存档保存完整快照。
- `pending_decisions`、外交义务、军令状态和 Agent run 全部落库。
- SQLite 使用 WAL；每个 campaign 单写锁；单事务提交权威结果。
- 叙事、头像和缓存可重建，不进入权威 state hash。
- 重放从最近快照开始逐回合应用结果，并校验 hash。

建议首批表：`campaigns`、`snapshots`、`turns`、`commands`、`turn_results`、`pending_decisions`、`agent_runs`、`narratives`、`source_citations`，以及人物、关系、地区、路线、军队、情报、事件、义务等领域表。

## 9. 前后端边界

- 新局/读档返回 `GameSnapshotDTO`。
- 正常结算返回 `TurnDiffDTO`，不每回合发送全景对象。
- 对话和叙事使用 SSE；取消只取消文本，不回滚已提交结果。
- UI 只发 `CommandDraft`，后端返回规范化命令与风险；玩家确认后才进入回合。
- “为何发生”面板读取 `TurnResult.explanations`，不让 AI 临时编理由。
- 历史注释通过 `/codex` 读取来源登记，与游戏状态 API 分离。

## 10. 性能与成本硬预算

| 指标 | M0 | M1/垂直切片 | Beta |
|---|---:|---:|---:|
| 关闭 LLM 规则回合 P95 | <500 ms | <300 ms | <200 ms |
| 联网可操作结果 P95 | <10 s | <8 s | <6 s |
| 叙事首字 P95 | <3 s | <2 s | <1.5 s |
| 常规高级模型调用 | <=1 | <=1 | <=1 |
| 常规全部 Agent 调用 | <=4 | <=3 | <=3 |
| schema 成功率 | >=95% | >=98% | >=99.5% |
| 重放 hash 一致率 | 100% | 100% | 100% |
| Agent 超时导致回合损坏 | 0 | 0 | 0 |

## 11. 迁移与复用决策

| 参考资产 | 处理 |
|---|---|
| React 地图、抽屉、奏报交互概念 | 参考交互，按新 DTO 重写 |
| `GameSession` 阶段概念 | 保留召见/组令/确认/结算，重写实现 |
| 内容 loader 思路 | 保留数据驱动，改为版本化 schema + validator |
| SQLite | 保留，增加工作单元、hash 和重放表 |
| 章节记忆概念 | 改为结构化事件摘要；章节文本可选生成 |
| Agno 直接散布各模块 | 不复用；封装为 provider-neutral runner |
| simulator + extractor | 删除 |
| `web_app.py` | 不复制，按 router/application 拆分 |
| 明代财政、军械、后宫、科技树 | 不迁移到 MVP |
| `二轮调研` 数据 | 先进入 research/raw，审计修复后才转 content |

## 12. 架构验收门槛

M0 结束前必须同时满足：

1. 潼关无 LLM 原型能在固定 seed 下完全重放。
2. 相同输入在 Windows/Linux 得到相同权威结果。
3. 任一 Agent 被强制超时，回合仍能提交或明确保持未提交。
4. 数据库中不存在“叙事文本解析后直接改权威数值”的入口。
5. 每个数值变化能追溯到命令、规则、随机种子和输入状态。
6. 1000 局自动潼关模拟无负兵力、资源凭空产生、瞬移和状态死锁。
7. 开局数据通过研究审计的 P0 准入门槛。

未达到以上条件时，不开始完整八年内容制作。
