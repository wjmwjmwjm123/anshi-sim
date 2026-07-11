# 安史之乱项目二轮调研数据审计

**审计对象**：`E:\AGENT\二轮调研` 全部 19 个文件  
**审计日期**：2026-07-11  
**审计范围**：D1-D8、6 个 patch、`merge.js`、README、项目进度报告、潼关研究报告 Markdown/HTML 版本  
**不在范围内**：`tang_engine` 的实现与复制架构；本审计只判断研究资料能否成为新游戏的数据与策划依据  
**结论**：**当前资料可作为概念稿和选题索引，不可直接作为生产数据导入。进入游戏制作前必须先完成 P0 数据修复与二次史料核验。**

---

## 1. 审计方法与判定标准

本次采用四层检查：

1. **机器结构检查**：以 UTF-8 读取全部 JSON，检查可解析性、顶层结构、实际记录数、ID 唯一性、字段并集与缺失值。
2. **跨表一致性检查**：检查人物、军队、地区、事件之间的外键；比较 `_meta`、README、进度报告与实际数据。
3. **时空与数值检查**：检查开局快照是否符合 `756.06.01`、事件日期口径、兵力求和、军队编成、地图连通性。
4. **证据质量检查**：区分传世史籍、现代研究、官方资料、百科/门户文章和纯游戏设计；检查每条数值是否能追溯到来源。

严重度定义：

| 级别 | 定义 |
|---|---|
| **CRITICAL** | 会使开局状态、时间推进、地图行动或数据合并产生错误，足以使核心结论或游戏结算失效 |
| **HIGH** | 会显著误导数值平衡、人物/事件史实或制作范围，必须在垂直切片前修复 |
| **MEDIUM** | 不立即阻断原型，但会造成维护、检索、叙事一致性或后续扩展成本 |

所有 JSON 均能在**显式 UTF-8**读取时成功解析。Windows PowerShell 旧版默认编码会显示乱码，因此审计命令必须显式指定 UTF-8；乱码不代表源文件损坏。

---

## 2. 文件清单与角色

| 组 | 文件 | 实际用途 | 审计状态 |
|---|---|---|---|
| 主数据 | `D1_WorldState.json` | 4 个全局指标、3 个危机、7 个帝国遗产、双视角摘要 | 可读，数值无逐条来源 |
| 主数据 | `D2_ArmiesGovernors.json` | 21 支军队/外部武装及汇总 | **开局快照与兵力口径失效** |
| 主数据 | `D3_Characters.json` | 68 条人物记录、九维属性、关系与命运 | 有陈旧汇总、语义重复、史实硬伤 |
| 主数据 | `D4_RegionsMap.json` | 22 地区、16 条边、灵宝战场细节 | **地图不连通** |
| 主数据 | `D5_Events.json` | 15 个事件、45 个选项 | 元数据错误；触发/结果不可直接执行 |
| 主数据 | `D6_Systems.json` | 10 个机制的伪代码与参数 | 是策划草案，不是可运行规则 |
| 主数据 | `D7_SourcesScripts.json` | 10 条来源、4 条语料、20 条角色台词、20 个 CG | 来源层级混杂；总数陈旧 |
| 主文档 | `D8_GapAnalysis.md` | 可玩性、优先级和风险分析 | 概念有用，但部分结论建立在错误数据上 |
| 补丁 | `patch_D3_A.json` | 7 条 A 类人物 | 已全部进入 D3 |
| 补丁 | `patch_D3_B.json` | 7 条 B 类人物 | 已全部进入 D3 |
| 补丁 | `patch_D3_C.json` | 7 条 C 类人物 | 已全部进入 D3，含田承嗣深化重复体 |
| 补丁 | `patch_D3_D.json` | 3 条 D 类人物 | 已全部进入 D3 |
| 补丁 | `patch_D5_events.json` | 7 个后续事件 | 已全部进入 D5；再次合并会重复 |
| 补丁 | `patch_D7_scenes.json` | 16 个 CG | 已全部进入 D7 |
| 工具 | `merge.js` | 把 patch 写回主文件 | **D5 合并非幂等，且不刷新统计** |
| 说明 | `README.md` | 数据说明与 GDD 摘要 | 多项计数与实际文件不一致 |
| 报告 | `项目进度报告_安史之乱中唐续命.md` | 复制引擎阶段的进度说明 | 不应作为新架构或史实证据 |
| 研究 | `潼关之战深度研究报告.md` | 约 755-756 的长篇研究底稿 | 来源弱、日期/数字有冲突 |
| 派生报告 | `潼关之战深度研究报告.html` | Markdown 报告的压缩展示版 | 内容并非逐字等价，不能当第二份独立证据 |

### 2.1 Patch 状态

6 个 patch 的每一个 ID 都已存在于主文件：D3 `24/24`、D5 `7/7`、D7 `16/16`。因此它们现在只是审计留档，不应再被运行时加载，也不能与主文件共同计数。

---

## 3. 实际记录数与声明值

| 数据 | 实际值 | 文件声明/文档值 | 结论 |
|---|---:|---:|---|
| D1 全局指标 | 4 | 4 | 一致 |
| D1 危机 | 3 | README 3；进度报告另称 7 | 研究源为 3；进度报告的 7 无法由本语料复核 |
| D1 帝国遗产 | 7 | 7 | 一致 |
| D2 唐方军队 | 9 | 9 | 数量一致，兵力不一致 |
| D2 叛军军队 | 7 | 7 | 数量一致，但包含未来军队 |
| D2 外部军队 | 5 | 5 | 数量一致，兵力无可靠出处 |
| D2 总军队 | 21 | 21 | 一致 |
| D2 唐方兵力求和 | **712,600** | `summary_statistics` **612,600**；README 又称“约 28 万有效兵” | 三种口径未定义 |
| D2 叛军兵力求和 | 385,000 | 385,000；README 摘要却写“约 20 万” | 快照兵力与起兵规模混用 |
| D2 外部兵力求和 | 330,000 | 330,000 | 一致但没有逐军来源 |
| D3 记录 | 68 | `_meta` 68；`summary_statistics` **44** | 汇总陈旧 |
| D3 历史人物实体 | **至多 67** | README 称 68 人 | `tian-chengsi` 与 `tian-chengsi_v2` 是同一人物两版 |
| D3 分类 | A15 / B23 / C22 / D8 | README 写 A8 / B13 / C22 / D5 | README 分类和合计均错误 |
| D4 地区 | 22 | 22 | 一致 |
| D4 边 | 16 | 16 | 一致但不足以连通地图 |
| D5 事件 | 15 | `_meta.total_events` **18**；README 15 | 元数据错误 |
| D5 决策选项 | 45 | 未声明 | 每事件固定 3 个 |
| D6 系统 | 10 | 10 | 一致 |
| D7 来源 | 10 | 未分项声明 | 6 条史籍摘录 + 4 条网页资料 |
| D7 语料 | 4 | 未分项声明 | 一致 |
| D7 台词 | 20 | 20 | 一致 |
| D7 CG | 20 | 20 | 一致 |
| D7 四类合计 | **54** | `_meta.total_items` **34** | 合并 CG 后未更新元数据 |

`README.md` 的人物分类表写出的数字相加只有 48，却在合计行写 68；这不是显示误差，而是不可依赖的手工汇总。

---

## 4. Schema 盘点

### 4.1 D1 世界状态

```text
_meta
global_indicators.{central_prestige,military_power,popular_support,treasury_fiscal}
  -> {value,min,max,reason,trend,per_turn_delta_range}
crisis_issues[]
  -> {id,name,progress,max_progress,direction_positive,direction_negative,
      resolve_condition,fail_condition,severity,anchor}
empire_legacies[]
  -> {id,name,type,effect,clear_conditions,current_impact_pct|current_impact_pct_mixed,anchor}
dual_perspective_summary.{tang_court_view,rebel_view}
```

问题：条件和效果都是自由文本；`trend` 与 `per_turn_delta_range` 没有回合单位；4 个初始指标没有逐值来源。

### 4.2 D2 军队

```text
army_categories.*.forces[]
  -> {army_id,name,type,garrison_location,troop_strength,composition,
      commander_id,loyalty_to,initial_status,relation_to_player,
      resource_output,key_generals,anchor,historical_note}
composition -> {infantry,cavalry,tribal_mercenaries,militia}
```

21 支军队的 `composition` 均能精确加总为 `troop_strength`，但这只能证明算术自洽，不能证明历史口径正确。9 个 `commander_id` 和 2 个 `key_generals` 无法解析到 D3；其中部分是占位符而不是人物 ID。

未解析 commander：`geshu-han-deputy`、`hesi-deputy`、`yang_guozhong_proxy`、`pinglu-deputy`、`hedong-rebel-proxy`、`bayanchur_khan`、`nanzhao_king`、`khitan_chief`、`xi_chief`。  
未解析 key general：`li-chengguang`、`hun-shizhi`。

### 4.3 D3 人物

```text
character_categories.*.characters[]
  -> {char_id,name,title,faction,location,birth_death,
      appearance_turn,exit_turn,attributes,personality_tags,
      relationships,historical_fate,game_rewrite_space,existence}
attributes
  -> {ability,loyalty,integrity,courage,diplomacy,military,
      administration,politics,scholarship,notes}
relationships[] -> {to,type,tension}
```

68 条九维属性都在 0-100 范围内，79 条人物关系均能解析到人物 ID。但 `appearance_turn`/`exit_turn` 混用 `YYYY`、`YYYY.MM`、`YYYY.MM.DD`，没有精度字段；人物层没有 `anchor` 或 `source_refs`，`existence` 不能说明每个属性值的证据状态。

### 4.4 D4 地区与地图

```text
regions[]
  -> {region_id,name,modern_location,controller_756_06,
      population_tier,morale,unrest_level,resources,strategic_value,
      terrain_tags,historical_events,anchor,[neighbors],[ambush_zones]}
topology_graph.edges[]
  -> {from,to,distance_days,distance_li,pass_conditions}
```

只有潼关记录含 `neighbors`，只有灵宝记录含 `ambush_zones`；真正路径来自 `topology_graph.edges`。坐标留在 D2 的字符串中，D4 没有可计算的经纬度、道路类型、季节、河渡或补给容量。

### 4.5 D5 事件

```text
events_act*[]
  -> {event_id,name,anchor,trigger_conditions,prerequisite_events,
      description_text,player_decisions,historical_branch,outcome_deltas,
      intelligence_distortion,involved_characters,involved_regions}
player_decisions[] -> {option,text,result_range}
```

`trigger_conditions` 有 4 种不统一字段组合：`turn`、`turn_range`、`condition`、`OR`。条件同时使用 `=`、`==`、自然语言和带连字符的变量 `shi_siming_campaign_at-luoyang`。`result_range` 全是自然语言，不能安全结算；`outcome_deltas` 又同时承载数值范围、布尔数组、状态字符串和地区控制权。

外键缺失：事件 `yang-geshu-conflict-75606` 引用不存在的人物 `du-qianyun` 和地区 `ba-shang`。

### 4.6 D6 机制

10 个系统均包含 `system_id/name/mechanics_description/player_mechanics/ai_behavior/variables`，但只有 2 个系统有 `difficulty_scaling`，只有地形伏击有 `battlefield_presets`。公式使用 Markdown、中文自然语言、三元表达式和未定义变量混排，属于策划伪代码，不是稳定契约。

### 4.7 D7 来源与剧本

```text
historical_sources_primary[] -> {source_id,title,excerpt,anchor,usage_hint}
period_dialogue_corpus[]      -> {corpus_id,type,speaker,context,text,anchor,usage_hint}
character_voice_lines[]       -> {line_id,character,emotion,trigger,text,anchor,usage_hint}
cinematic_scene_scripts[]     -> {scene_id,title,duration_seconds,camera_shots,
                                  background_music,voiceover,on_screen_text,anchor,usage_hint}
```

来源条目缺出版版本、卷内定位、页码、校勘本、URL 访问日期、作者、出版者和 claim-to-source 映射。`character_voice_lines.character` 使用显示名而非人物 ID，后续改名会破坏关联。

---

## 5. CRITICAL 问题

### C-01：`756.06.01` 军队快照包含互相排斥的历史时点

证据：

| 记录 | 数据中的状态 | 同库冲突 |
|---|---|---|
| `TANG-004` 河北义军 | 20 万，颜杲卿指挥，`rebellion_behind_lines` | D3 中 `yan-gaoqing.exit_turn = 756.02`；D4 在 756.06 已把常山控制者写为叛军 |
| `REBEL-007` 睢阳围攻军 | 13 万，尹子奇，围城中 | 自身 `historical_note` 与 D3 都说明这是 757 年事件，不能出现在 756.06 快照 |
| `TANG-006` 雍丘守军 | 7,000，状态 `under_siege`，注释称“757 年正月被围” | 把 756 年雍丘战事与 757 年睢阳战事合并成一个状态 |

影响：开局兵力、控制区、人物存活、AI 可用军队和补给结算都会错误。D2 不能作为 `WorldState@756.06.01` 导入。

修复：把“军队编制目录”与“时间快照”拆开。建立 `force_templates`、`force_instances`、`force_strength_estimates`、`state_snapshots` 四层；所有实例必须有 `valid_from/valid_to` 和 `as_of`。

### C-02：`merge.js` 对 D5 不是幂等操作

证据：脚本初始化事件去重集合时只扫描 `events_act1_crisis` 和 `events_act2_collapse`，没有扫描已经存在的 Act3-5。当前 7 个 patch 事件已经在主文件中；再次运行脚本会把它们再次追加，D5 将从 15 条变成 22 条并产生重复 ID。

脚本同时不会刷新：

- D3 的 `summary_statistics`；
- D5 的 `_meta.total_events`；
- D7 的 `_meta.total_items`。

影响：按 README 重新合并会直接污染主数据，且污染后元数据仍可能看似正常。

修复：停止对当前主文件运行 `merge.js`。以后采用“patch 输入 -> 新 build 目录”的纯函数式构建，扫描所有分组、重复即失败、写临时文件、校验后原子替换；所有统计由构建器重算，禁止手填。

### C-03：地图不连通，路径/补给系统无法成立

22 个地区只有 16 条无向边。主连通分量包含 17 个地区，5 个孤立点为：

```text
ping-lu, he-dong, bei-ting, jiang-ling, yang-zhou
```

一个 22 节点无向连通图至少需要 21 条边；当前不仅边少，河东、平卢等核心战区也完全不可达。D6 又规定“部队必须与城池/粮仓有路径连通”，因此这些地区的部队会永久断粮或无法行动。

修复：先定义战略地图尺度，再补历史道路/关隘/水运边。若某地是“域外节点”，必须用 `offmap=true` 和显式转场规则表示，不能用孤立节点冒充普通地区。

### C-04：日历未声明，事件日期可整体错位约一个月

D5 的 `756.06.08`、`756.06.14` 等字符串显然按天宝十五载农历月日编码；研究报告附录却同时给出对应公历 `756-07-04`、`756-07-10`。文件没有 `calendar` 字段，形式又像公历 ISO 日期。

另外：

- D3 时间精度混用年、月、日；
- D1 危机条件使用同样的伪日期；
- 研究报告正文把杨国忠之死写为“六月十三日”，附录/D5 写“六月十四”；
- 游戏范围一处写“96 个月/回合”，D8 又设计为 30-50 回合，没有统一回合长度。

影响：事件调度、年龄、补给、月产出、历史提示和存档比较都会出现系统性错误。

修复：每个历史节点同时保存 `era_name`、`lunar_date_text`、`proleptic_gregorian_date`、`date_precision`、`date_confidence`；引擎只以一个明确的标准日期推进，展示层再转换年号/农历。

---

## 6. HIGH 问题

### H-01：兵力统计混用“编制额、时点实兵、号称、地方响应和有效战兵”

D2 唐方逐军求和为 712,600，而汇总写 612,600，恰差 100,000。研究报告又有以下互不等价数字：

- 潼关可用兵力 32-34 万；
- 十节度使边防编制约 49 万；
- 全国含中央军约 61 万；
- 河北十七郡“共聚义军 20 余万”；
- README 称唐方“账面 61 万、有效战兵 28 万”。

D2 还同时计算潼关 20 万、河西/陇右/朔方剩余军和河北义军，存在抽调兵重复计数风险；叛军 38.5 万又包含 757 年睢阳围攻军 13 万，不能拿来描述 756 年六月。

修复：每个数字必须带：

```text
value_low, value_high, preferred_value, unit,
count_type (authorized/claimed/present/effective/cumulative),
as_of, geographic_scope, included_force_ids, source_refs, confidence
```

任何“总兵力”都应由同一时点、互斥集合自动聚合。

### H-02：人物表存在语义重复与可确认的内部硬伤

1. `tian-chengsi` 与 `tian-chengsi_v2` 是同一历史人物。旧记录虽有 `_superseded_by_v2=true`，仍被计入 68 人并可被系统读取。
2. D6 人物寿命写“郭子仪 819 年卒”，D3 写 781 年，二者内部冲突。
3. `dai-zong` 的注释与命运均写“758 年即位”，应重新按权威年表核验；这会影响皇统切换。
4. ID `me-agtsom` 对应的人名、出生年和命运却是赤松德赞，两个吐蕃赞普身份发生混合。
5. `yehu-khan`、`yidijian-khan` 的父子/兄弟、759 年继承和弑父叙述彼此可疑，必须由回纥史专门核验，不能直接锁定。
6. 静态 `title` 把李豫在 756 年直接写为“唐代宗皇帝”，缺少随时间变化的官职/身份记录。

修复：人物主表只保留身份；官职、称号、阵营、所在和存亡进入带起止日期的 timeline。人物属性必须区分“史实描述”与“游戏评分”。

### H-03：D5 不是可执行事件契约

主要风险：

- 触发条件没有 AST/JSON Logic；`=` 与 `==` 混用。
- `OR` 有时是 `game_start`，有时是布尔表达式，语义不稳定。
- `result_range` 是混合中英文自由文本，程序无法无歧义应用。
- `outcome_deltas` 的数组没有说明是 `[min,max]`、多选值还是先后状态。
- `shi_siming_campaign_at-luoyang` 含连字符，常见表达式解析器会当减法。
- `historical_branch = "A/C"` 不是单一历史分支。
- 15 个事件中最后一个触发于 761，却把 762 年再复洛阳、763 年史朝义灭亡和河朔三镇成型压进一条描述；实际没有 762/763 的独立结算节点。

修复：使用结构化条件和操作，例如 `all/any/not/comparison`；每个选项只输出明确的 `effects[]`，每个 effect 有 `op/path/value/unit`。历史叙述与状态变更分离。

### H-04：来源体系不能支撑“详细数值策划”

D7 的 `historical_sources_primary` 共有 10 条，其中只有 6 条来自《资治通鉴》《旧唐书》《新唐书》，另外 4 条是百度百科或 OSGeo Wiki，却同样标为 `[史实锚定]`。

潼关 Markdown 报告列 15 条参考资料：

- 3 条传世史籍；
- 1 条地方政府现代地理资料；
- 1 条新闻文化文章；
- 10 条百科、门户、自媒体或 Wiki。

报告声称使用“学术论文与专著”，参考文献中却没有可识别的学术专著或同行评审论文。史籍也没有版本、页码或卷内精确条目。HTML 版参考文献与 Markdown 版数量和内容不同，说明 HTML 是摘要改写而不是证据副本。

建议质量分级：

| 等级 | 当前材料 | 可用方式 |
|---|---|---|
| B/C | 6 条传世史籍摘录 | 可作事件线索；补版本、卷页并核对原文后才能锁定 |
| C | 地方政府自然地理 | 仅用于现代行政/自然地理，不证明古战场微地形 |
| C/D | 澎湃等编辑媒体 | 只作选题索引 |
| D/F | 百度/搜狗百科、中华网、网易、搜狐、头条、OSGeo Wiki | 不作为兵力、伤亡、制度公式的最终依据 |
| 缺失 | 现代唐史专著、军事史/制度史论文、历史地图/GIS、出土文献研究 | 必须补齐 |

### H-05：零条核心数值记录具备逐条来源引用

D1 指标、D2 兵力、D3 九维、D4 资源/民心/距离、D5 数值效果、D6 公式均没有 `source_refs`。`anchor=[史实锚定]` 只能表示作者意图，不能证明哪个来源支持哪个数值。

修复：建立独立 `sources.json` 与 `claims.json`。任何可验证事实通过 `claim_id` 关联来源；任何游戏数值通过 `design_rationale`、`calibration_status`、`target_metric` 说明，不再伪装成史实。

### H-06：README 和进度报告不能作为真值来源

- README 人物分类数字与实际数据严重不符。
- 进度报告说“68 人（含田悦补齐）”，D3 没有田悦，只有田承嗣的第二版本。
- 进度报告的 7 个危机无法由 D1 的 3 个危机复核。
- “约 96 个月/回合”与 D8 的 30-50 回合设计互相冲突。
- 进度报告主要证明复制引擎阶段做过什么，用户已明确不采用该架构，因此只能当历史记录，不应进入新项目的架构依据。

修复：所有文档统计由构建脚本生成；研究库、策划库、运行时内容分别设 manifest 和版本号。

---

## 7. MEDIUM 问题

### M-01：史实/推演/虚构标签不统一

README 宣布三类标签：`[史实锚定]`、`[合理推演]`、`[虚构设计]`，实际还有：

- `[古风拟作]`
- `[剧作设计]`
- `[史实锚定·内容抽象处理]`
- 带长说明后缀的十余种变体

D3 甚至没有 `anchor`，而使用“必用史实/可选史实/合理推演”的 `existence`。D6 把游戏概率、阈值和公式整体标成 `[史实锚定]`，标签粒度错误。

建议改成正交字段：

```text
epistemic_status: documented | estimate | inference | counterfactual | fictional
content_form: fact | paraphrase | dialogue | cinematic | mechanic
confidence: high | medium | low | disputed
source_refs: []
review_status: draft | verified | rejected
```

### M-02：地区控制者和阵营 ID 未规范化

`controller_756_06` 同时出现 `tang`、`tang_emperor_xuanzong`、`tang_geshu_han`、`yang_guozhong_faction`、`rebel_*`、`contested`。这些有的是国家、有的是人物、有的是派系、有的是状态，无法做稳定外键。

建议拆成 `sovereign_power_id`、`occupying_force_id`、`local_administration_id`、`control_status`。

### M-03：资源单位和回合单位缺失

`gold_per_turn`、`grain_per_turn`、`recruitment_pool` 没有货币、粮食、人口单位，也没有说明一回合是日、旬、月还是事件阶段。D6 的部队消耗同样按 `per turn` 计算，无法与 D4 产出配平。

### M-04：地图距离过度抽象且缺乏验证

16 条边只给 `distance_days` 和 `distance_li`，没有步骑差异、道路类型、季节、坡度、河流、关隘容量、敌控区和补给损耗。`长安 -> 潼关`、`马嵬 -> 剑南` 等边把复杂路线压成单边，会让战略 AI 产生不合理捷径。

### M-05：HTML 与 Markdown 报告版本治理缺失

HTML 是压缩版，省略多段论证并改变参考文献列表；两者都标注同一生成日期和约 28,000 字。应明确一个 source-of-truth，由构建流程生成另一个，不能手工维护两个版本。

### M-06：敏感数字与叙述缺少争议标记

“睢阳杀敌十二万/围军十三万”“安史之乱人口锐减约 3600 万”“伤亡/食人/劫掠人数”等都具有口径或解释争议，当前却直接进入事件、角色说明或 CG。需要 `disputed=true`、多来源并列、内容分级与抽象展示策略。

---

## 8. 关键证据表

| 证据 | 位置 | 说明 |
|---|---|---|
| 唐军求和 712,600 | D2 九支 `troop_strength` 求和 | 与同文件汇总 612,600 冲突 |
| 颜杲卿已退出但仍领 20 万 | D3 `yan-gaoqing.exit_turn=756.02`；D2 `TANG-004` | 756.06 快照不可能同时成立 |
| 睢阳军提前一年出现 | D2 `REBEL-007`；D3 `yin-ziqi.appearance_turn=757.01` | 未来军队污染开局 |
| 田承嗣重复 | D3 `tian-chengsi`、`tian-chengsi_v2` | 两 ID 同一历史人物 |
| 郭子仪卒年冲突 | D3 写 781；D6 `character_aging` 写 819 | 机制校验数据错误 |
| 吐蕃人物 ID 混淆 | D3 `me-agtsom` 的姓名为赤松德赞 | 身份键与实体不一致 |
| D5 事件数冲突 | 实际 15；`_meta=18` | 构建统计未刷新 |
| D7 内容数冲突 | 实际 54；`_meta=34` | CG 合并后未刷新 |
| 5 个孤立地区 | D4 topology | 平卢、河东、北庭、江陵、扬州不可达 |
| D5 外键缺失 | `du-qianyun`、`ba-shang` | 人物/地区未定义 |
| 日期双口径 | D5 `756.06.08`；研究报告附录公历 `756-07-04` | 未声明农历，易被当 ISO 日期 |
| 马嵬日冲突 | 研究报告正文“六月十三”；附录/D5“六月十四” | 需以校订本和历日表统一 |
| 史实标签泛化 | D6 9/10 系统整体标史实 | 史实启发不等于公式史实 |
| 学术来源缺失 | 研究报告参考文献 | 没有可识别的现代学术专著/同行评审论文 |

---

## 9. 进入游戏制作前必须补的研究

### P0：阻断性研究与数据工程

1. **756 年开局日快照**：逐军、逐人、逐地确认在场、存活、控制权、位置、兵力范围和状态。
2. **双历日期表**：755-763 所有核心事件的年号/农历/公历映射，记录日期分歧和可信度。
3. **兵力口径表**：编制额、号称、实到、参战、战后存余、累计地方响应必须分列；禁止跨时间相加。
4. **地图与交通研究**：关中-河南-河北-河东-河西-江淮的道路、关隘、渡口、漕运、行军日数和季节性。
5. **来源账本**：为每个事实/估计建立 claim、来源、原文、版本、页码、解释和争议状态。
6. **运行时 schema**：用 JSON Schema 或等价类型系统约束 ID、日期、条件、effects、单位和枚举。

### P1：垂直切片前完成

1. **潼关战役 order of battle**：20 万的组成、出关序列、指挥链、叛军疑兵/伏兵、战损区间。
2. **军令与政治链**：玄宗、杨国忠、哥舒翰、王思礼、田良丘、宦官奏报的权限与信息路径。
3. **后勤基准**：军粮计量、日耗、运输损耗、城仓容量、征发与民变的量纲。
4. **财政/人口基准**：地区产出不能直接用无单位的 0-8000；需要价格、税源、户口与战乱折损模型。
5. **人物履历 timeline**：官职、阵营、所在地、健康、存亡按时段变化；清理静态皇帝称号。
6. **回纥与吐蕃专题**：人物谱系、称号译名、借兵条款、劫掠叙述、763 长安事件分别核验。
7. **事件链补全**：为 761-763 建立独立事件和结算，不用一个 761 事件代替两年历史。

### P2：完整制作前完成

1. 普通民众、地方官、运输者、商人、难民和女性视角，修正目前过度集中于君臣名将的问题。
2. 河朔三镇、神策军、盐法、漕运、宦官监军等中长期制度专题。
3. 伤亡、人口下降、睢阳、屠城与劫掠等敏感内容的争议史料与分级呈现。
4. 反事实分支的可行性评审：每条 IF 线要写必要条件、代价、二阶后果和最大偏离点。
5. 数值校准实验：确定单回合长度、通关时长、失败率、有效策略数和 AI 决策预算后再定概率。

---

## 10. 建议的新研究数据路径

此处只定义研究与内容层，不绑定任何既有引擎：

```text
research/
  sources/                 # 书目、版本、页码、URL、访问日期
  claims/                  # 原子事实、估计、争议、source_refs
  chronology/              # 双历日期与事件时间线
  entities/                # 人物、势力、地区、军队身份主表
  estimates/               # 兵力、人口、财政、距离的区间估计
  maps/                    # 节点、道路、渡口、关隘、GIS 证据
  reviews/                 # 历史顾问核验记录

design/
  scenarios/756_tongguan/  # 经审核的开局快照
  events/                  # 结构化触发与 effects
  mechanics/               # 带单位的确定性公式
  balance/                 # 与史实分离的游戏参数及校准结果
  narrative/               # 台词、CG、敏感内容变体

build/
  manifests/               # 版本、哈希、依赖、排除 patch 规则
  generated/               # 只读运行时数据，不手改
  validation/              # schema、外键、时间、连通性、单位测试报告
```

研究事实和游戏数值必须分层。史料可以证明“发生了什么、约在何时、规模可能多大”，不能直接证明“忠诚 83”“每回合 25% 假情报”“粮耗 0.01”。后者必须标为设计参数并经过模拟校准。

---

## 11. 制作准入门槛

满足以下条件后，资料才可进入垂直切片：

- [ ] 所有主文件只有一个 source-of-truth，patch 不参与运行时加载。
- [ ] 合并/构建可重复运行，输出哈希稳定，重复 ID 直接失败。
- [ ] `_meta` 和 README 统计全部自动生成。
- [ ] 人物、军队、地区、事件外键缺失数为 0。
- [ ] `WorldState@756` 中不存在未登场、已退出或未来军队。
- [ ] 所有日期明确日历与精度，核心事件有双历映射。
- [ ] 战略地图连通；所有孤立节点都有明确 off-map 语义。
- [ ] 所有兵力聚合来自同一时点和同一计数口径。
- [ ] 所有历史数值有 `source_refs/confidence`，所有设计数值有 `design_rationale`。
- [ ] 事件触发和结果为结构化数据，不依赖自然语言抽取。
- [ ] 完成潼关战役、回纥/吐蕃、皇统切换三个专题顾问复核。
- [ ] 至少跑通一条 756.06 开局至潼关守/战分支的确定性回放测试。

---

## 12. 可复现审计命令

### 12.1 UTF-8 JSON 有效性

```powershell
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::new()
Get-ChildItem -LiteralPath 'E:\AGENT\二轮调研' -Filter '*.json' |
  Sort-Object Name |
  ForEach-Object {
    $text = [IO.File]::ReadAllText($_.FullName, [Text.Encoding]::UTF8)
    try { $null = $text | ConvertFrom-Json; "VALID`t$($_.Name)" }
    catch { "INVALID`t$($_.Name)`t$($_.Exception.Message)" }
  }
```

### 12.2 核心计数与兵力求和

```powershell
@'
const fs = require('fs'), p = 'E:/AGENT/二轮调研/';
const j = n => JSON.parse(fs.readFileSync(p + n, 'utf8'));
const d2 = j('D2_ArmiesGovernors.json');
const forces = Object.values(d2.army_categories).flatMap(x => x.forces);
for (const [k,v] of Object.entries(d2.army_categories))
  console.log(k, v.forces.length, v.forces.reduce((s,x)=>s+x.troop_strength,0));
const d3 = j('D3_Characters.json');
const chars = Object.values(d3.character_categories).flatMap(x => x.characters);
console.log('characters', chars.length, new Set(chars.map(x=>x.char_id)).size);
const d5 = j('D5_Events.json');
const events = Object.entries(d5).filter(([k])=>k.startsWith('events_')).flatMap(([,v])=>v);
console.log('events', events.length, new Set(events.map(x=>x.event_id)).size);
const d7 = j('D7_SourcesScripts.json');
console.log('D7 total', ['historical_sources_primary','period_dialogue_corpus',
  'character_voice_lines','cinematic_scene_scripts'].reduce((s,k)=>s+d7[k].length,0));
'@ | node -
```

### 12.3 地图连通性方法

1. 以 `regions[].region_id` 建立节点集合。
2. 把 `topology_graph.edges[]` 当无向边加入邻接表。
3. 对所有未访问节点执行 BFS/DFS。
4. 输出连通分量；本次结果为 6 个分量：一个 17 节点主分量和 5 个单节点分量。

### 12.4 Patch 重复检查

分别取主文件现有 `char_id/event_id/scene_id` 集合，与 patch 对应 ID 求交集。当前交集为 D3 `24`、D5 `7`、D7 `16`，等于所有 patch 记录数，证明 patch 已全部合并。

---

## 13. 最终判定

这批资料的价值在于：已经找出了潼关、将相倾轧、情报失真、地形伏击、河北牵制、借兵代价和藩镇遗产等正确的设计主题，也形成了可继续深化的人物/事件索引。

它当前的主要问题是把四种不同东西装进了同一层 JSON：

1. 史籍叙述；
2. 现代网络摘要；
3. 作者推演；
4. 未校准的游戏参数。

因此下一阶段不应继续堆人物、事件或 AI prompt，而应先完成**史料账本、756 开局快照、双历时间线、兵力口径和连通地图**。这五项完成后，才有资格讨论详细数值平衡和多 AI 如何消费数据。

**AI 辅助说明**：本审计使用 AI 辅助进行结构扫描、交叉一致性检查和报告编排；所有史实修订项仍需由唐史专业人员依据指定版本原典复核。
