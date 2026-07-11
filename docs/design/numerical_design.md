# 《安史之乱：中唐续命》数值系统规格书

> 状态：Pre-production v0.1  
> 基准日期：天宝十五载六月初一（公元 756 年夏，游戏内部统一使用儒略日/ISO 映射）  
> 数据输入：`二轮调研/D1-D6`、`D8_GapAnalysis.md`、`潼关之战深度研究报告.md`  
> 目的：定义可编码、可测试、可复盘的数值合同。本文数值是原型基线，不是假称精确的历史事实。

## 1. 数值设计原则

1. **有单位的原始量先于 0-100 摘要。** 兵力是“人”，粮是“标准粮单位”，距离是“行军日”，时间是“日”。`military_power=55` 只由底层状态派生，不参与战斗计算。
2. **所有流量按日定义。** 一次结算量为 `daily_rate * elapsed_days`，危机回合 1-3 日、战役回合 10-15 日、战略回合 30-90 日不会改变系统量纲。
3. **史料值分层保存。** 每个史实字段同时保存 `value/range`、`evidence_grade`、`source_ids`、`confidence`。史书所称“二十万”保存为锚点区间，不冒充点估计。
4. **结果由规则裁决。** AI 只能提交 schema 合法的意图、解释和叙事，不能直接改兵力、粮秣、忠诚、关系或事件进度。
5. **随机可复现且不替代因果。** 每次战役、密谋、疾病检定记录 `seed`。同一状态、命令和 seed 必须得到相同结果。
6. **不做乘法陷阱。** 多个 0-1 因子直接连乘会让战力轻易趋零。统一使用加权评分转倍率，并对倍率设上下限。
7. **数字必须可解释。** 战报输出贡献最大的 3-5 个因素，玩家能理解为什么败，而不是只看到随机骰点。

## 2. 通用类型、精度与刷新规则

| 类型 | 范围/单位 | 存储 | UI | 说明 |
|---|---:|---|---|---|
| `Score` | 0-100 | `uint8` | 整数、分档 | 0 极差，50 常态，100 极佳 |
| `Relation` | -100..100 | `int16` | 定性或整数 | 敌对到亲密 |
| `Ratio` | 0..1 | `float32` | 百分比 | 内核每步 clamp |
| `People` | 人 | `int32` | 取整/约数 | 账面兵、可战兵、伤病分存 |
| `Grain` | 标准粮单位 GLU | `int64` | “可供 X 日”优先 | 1 GLU = 1 名标准步兵 1 日口粮 |
| `Cash` | 财政点 CP | `int64` | 财政点/收入天数 | 原型抽象币值，史实绢、钱另存价格 |
| `Distance` | 行军日 | `float32` | 预计到达日 | 道路、天气修正后得到 |
| `Rate` | 每日 | `float32` | 日/月折算 | 禁止使用无单位 `per_turn` |
| `Date` | 游戏日 | `int32` | 历法日期 | 事件比较只使用规范化日期 |

更新层级：

- **日步进**：口粮、饷欠、疲劳、伤病、围城、生产、运输、情报老化、健康压力。
- **行动完成时**：移动、战斗、军令接受、召见、任命、外交签约。
- **旬结算（10 日）**：税收汇总、募兵、治安、派系议程、叛军联盟稳定。
- **月结算（30 日）**：人口迁移、生产恢复、土地兼并、自治倾向、外部势力战略意图。
- **事件结算**：首都陷落、皇帝更替、名将死亡等离散冲击；事件不能重复施加同一效果。

## 3. 世界与朝廷状态

### 3.1 底层字段

| 字段 | 单位/范围 | 756-06 基线 | 刷新 | UI |
|---|---:|---:|---|---|
| `date` | 游戏日 | 756-06-01（剧本历） | 日 | 可见 |
| `court_cash_cp` | CP，>=0 | 40,000 | 日/月 | 可见 |
| `central_grain_glu` | GLU，>=0 | 18,000,000 | 日 | 显示可供天数 |
| `transport_capacity_glu_day` | GLU/日 | 185,000 | 日 | 可见摘要 |
| `arrears_cp` | CP，>=0 | 8,000 | 日 | 可见 |
| `attention` | 0-10 | 6 | 每行动阶段恢复 3 | 可见 |
| `administrative_capacity` | 0-20 | 10 | 旬 | 可见 |
| `political_capital` | 0-100 | 42 | 行动/旬 | 可见 |
| `court_legitimacy` | 0-100 | 62 | 事件/月 | 可见 |
| `central_prestige` | 0-100 | 45 | 派生/事件 | 可见 |
| `popular_support` | 0-100 | 35 | 月/事件 | 可见 |
| `fiscal_health` | 0-100 | 40 | 派生 | 可见 |
| `military_power` | 0-100 | 55 | 派生 | 可见 |
| `imperial_continuity` | 0-100 | 70 | 事件 | 可见 |
| `war_exhaustion` | 0-100 | 28 | 日/月 | 可见 |
| `civilian_deaths` | 人 | 0（从剧本开场计） | 事件 | 区间可见 |
| `displaced_population` | 人 | 0（从剧本开场计） | 月/事件 | 区间可见 |
| `western_control` | 0-100 | 72 | 月 | 可见 |
| `central_army_ratio` | 0-100% | 约 20% | 派生 | 可见 |

`court_cash_cp=40,000` 和粮储是**设计基准**，不是历史币量断言。首月无新增收入、维持现有可直接调度军队时，应形成“能应急但不能无限动员”的压力；Alpha 前再用经济仿真校准。

### 3.2 摘要指标公式

```text
fiscal_health = clamp(0, 100,
  35 * min(1, cash / target_cash)
  + 35 * min(1, grain_days / 90)
  + 20 * collection_efficiency
  + 10 * (1 - arrears_ratio))

military_power = clamp(0, 100,
  45 * normalized_ready_strength
  + 20 * mean_training
  + 15 * mean_supply_ratio
  + 10 * command_cohesion
  + 10 * strategic_mobility)

central_prestige_delta_month =
  capital_control_delta * 15
  + major_victories * 6 - major_defeats * 8
  + oath_fulfillment * 3 - oath_breach * 8
  - clamp(0, 8, arrears_ratio * 10)
```

摘要每次底层状态变化后重算，不接受事件直接写 `military_power +/- 30000` 这类量纲错误。

### 3.3 开局危机

| 危机 | 基线 | 正向为 | 日变化 | 阈值 |
|---|---:|---|---:|---|
| 潼关危机 | 65/100 | 越高越接近灾变 | 催战 +8；坚守且补给足 -2；可靠河北捷报 -3 | 80：强制朝议；100：出关/兵变分支 |
| 将相倾轧 | 80/100 | 越高越危险 | 杨系进谗 +6；面圣调解 -12；撤监军 -8 | 90：命令干扰；100：清洗/兵变 |
| 假情报压力 | 90/100 | 越高越危险 | 未复核报告 +4；独立来源证实 -15 | 95：错误建议占主导；100：催战令 |

危机不再以固定日期自动失败；日期只加压力。玩家能改变原因，才能改变结果。

## 4. 地区、交通与经济

### 4.1 地区字段

| 字段 | 单位/范围 | 说明 | UI |
|---|---:|---|---|
| `controller_id` | ID | 实际军事控制者 | 可见/情报延迟 |
| `claimants` | ID[] | 法理主张 | 可见 |
| `population_tier` | 1-5 | 调研基线；后续映射人口区间 | 可见 |
| `population_estimate` | 人/区间 | 不足证时仅内部采样 | 模糊 |
| `agriculture_capacity` | 0-100 | 农业潜能 | 可见分档 |
| `commerce_capacity` | 0-100 | 商税潜能 | 可见分档 |
| `production_damage` | 0-100 | 战争破坏 | 可见 |
| `morale` | 0-100 | 地方拥护和韧性 | 可见 |
| `unrest` | 0-100 | 骚乱与反抗风险 | 可见 |
| `security` | 0-100 | 官府控制 | 可见 |
| `tax_burden` | 0-100 | 50 为常态 | 可见 |
| `grain_stock_glu` | GLU | 本地仓储 | 显示可供天数 |
| `cash_stock_cp` | CP | 地方可调用财力 | 可见 |
| `daily_grain_output` | GLU/日 | 季节化 | 估算 |
| `daily_tax_output` | CP/日 | 旬入账 | 估算 |
| `recruit_pool` | 人 | 不是每回合收入 | 可见 |
| `fortification` | 0-100 | 城防完整度 | 可见 |
| `siege_stock_days` | 日 | 派生 | 可见 |

### 4.2 756-06 地区导入基线

下表保留 D4 的 22 地区数据。`金/粮/募兵` 是旧稿相对产出点，导入时分别解释为 `30 日基础 CP`、`千 GLU/日的权重`、`当前可征募池`，不得继续命名 `per_turn`。

| 地区 | 控制 | 人口级 | 士气 | 动乱 | 旧金/30日 | 旧粮权重 | 募兵池 |
|---|---|---:|---:|---:|---:|---:|---:|
| 长安 | 唐玄宗 | 5 | 50 | 45 | 5000 | 8000 | 8000 |
| 潼关 | 哥舒翰/唐 | 2 | 65 | 20 | 500 | 2000 | 1000 |
| 灵宝西原 | 争夺 | 2 | 40 | 60 | 300 | 1500 | 800 |
| 洛阳 | 安禄山/燕 | 5 | 30 | 70 | 4000 | 7000 | 6000 |
| 陕郡 | 崔乾佑/燕 | 3 | 35 | 65 | 1000 | 3000 | 2000 |
| 范阳 | 燕 | 4 | 45 | 50 | 3000 | 5000 | 8000 |
| 平卢 | 燕 | 3 | 50 | 40 | 1500 | 3000 | 4000 |
| 河东/太原 | 争夺 | 4 | 55 | 45 | 2500 | 4500 | 5000 |
| 朔方/灵州 | 郭子仪/唐 | 3 | 75 | 15 | 2000 | 3500 | 5000 |
| 河西/凉州 | 唐 | 3 | 70 | 20 | 1800 | 3000 | 3500 |
| 陇右/鄯州 | 唐 | 2 | 65 | 25 | 1500 | 2500 | 3000 |
| 安西/龟兹 | 唐 | 2 | 60 | 30 | 1000 | 1500 | 2000 |
| 北庭/庭州 | 唐 | 2 | 60 | 30 | 800 | 1200 | 1800 |
| 剑南/成都 | 杨系/唐 | 4 | 60 | 30 | 3500 | 6000 | 4000 |
| 南阳 | 唐 | 3 | 50 | 55 | 1200 | 2500 | 2000 |
| 雍丘 | 张巡/唐 | 2 | 45 | 60 | 400 | 1000 | 800 |
| 睢阳 | 唐 | 3 | 40 | 65 | 800 | 1500 | 1200 |
| 常山 | 史思明/燕 | 3 | 35 | 70 | 1000 | 2500 | 3000 |
| 平原 | 颜真卿/唐 | 3 | 65 | 40 | 1200 | 3000 | 3500 |
| 马嵬驿 | 唐 | 1 | 30 | 80 | 100 | 300 | 200 |
| 江陵 | 唐 | 3 | 55 | 35 | 2000 | 4000 | 2500 |
| 扬州 | 唐 | 4 | 50 | 40 | 4000 | 5000 | 3000 |

转换公式须经经济测试后固化：

```text
daily_tax_cp = old_gold_per_turn / 30
daily_grain_output_glu = old_grain_weight * 10
actual_output = base_output
  * seasonal_factor(0.55..1.35)
  * control_factor(0.25 + 0.75 * security/100)
  * damage_factor(1 - production_damage/100)
  * labor_factor(1 - levy_ratio * 0.6)

unrest_delta_month =
  + max(0, tax_burden - 50) * 0.12
  + requisition_rate * 15
  + occupation_abuse * 10
  + food_shortage_days * 0.35
  - security * 0.08
  - relief_spending_per_capita
```

### 4.3 交通边

每条边必须有：`from/to`、`bidirectional`、`base_days`、`capacity_glu_day`、`road_quality`、`waterway`、`season_mod`、`control`、`interdiction`、`ambush_risk`。D4 当前只有 16 条边，不能支撑 22 个地区；未连通地区在实现前视为数据错误，不得瞬移。

```text
travel_days = base_days
  * unit_mobility_mod
  * weather_mod
  * congestion_mod
  / road_quality

edge_throughput = capacity_glu_day
  * control_ratio
  * (1 - interdiction)
  * weather_capacity_mod

transport_loss_ratio = clamp(0, 0.65,
  0.015 * travel_days
  + 0.20 * interdiction
  + 0.10 * (1 - road_quality))
```

## 5. 军队与兵员

### 5.1 军队字段

| 字段 | 单位/范围 | 说明 | UI |
|---|---:|---|---|
| `paper_strength` | 人 | 名册/号称 | 模糊或确切 |
| `present_strength` | 人 | 实际在队 | 己方可见 |
| `fit_strength` | 人 | 可立即作战 | 己方可见 |
| `wounded/sick/absent` | 人 | 分项 | 可见摘要 |
| `infantry/cavalry/militia/tribal` | 人 | 构成总和须等于在队人数 | 可见/敌方估计 |
| `training` | 0-100 | 训练 | 可见分档 |
| `equipment` | 0-100 | 装备完好 | 可见分档 |
| `morale` | 0-100 | 临战精神 | 可见 |
| `cohesion` | 0-100 | 队伍组织度 | 可见 |
| `fatigue` | 0-100 | 越高越差 | 可见 |
| `supply_ratio` | 0-1 | 当前需求满足率 | 可见 |
| `grain_stock_glu` | GLU | 随军口粮 | 可供天数 |
| `arrears_days` | 日 | 欠饷 | 可见 |
| `loyalty_to_commander` | 0-100 | 对将 | 仅情报估计 |
| `loyalty_to_regime` | 0-100 | 对政权 | 仅情报估计 |
| `command_cohesion` | 0-100 | 多军协同 | 可见 |
| `stance` | enum | 守、行军、攻城、休整等 | 可见 |

### 5.2 756-06 账面兵力基线

| 阵营 | 军队 | 人数 | 备注 |
|---|---|---:|---|
| 唐 | 潼关哥舒翰部 | 200,000 | 史载号称；可战比例初始 0.62 |
| 唐 | 朔方军 | 64,700 | 可战比例 0.82 |
| 唐 | 河东军 | 45,000 | 调研报告另称 55,000，待核 |
| 唐 | 河北义军 | 200,000 | 聚合声势，不能作为单一机动军团；可战比例 0.35 |
| 唐 | 南阳守军 | 50,000 | 被围，野战可用受限 |
| 唐 | 雍丘守军 | 7,000 | 开局时点与睢阳阶段需拆分 |
| 唐 | 陇右军 | 60,000 | 调离将削弱边防 |
| 唐 | 河西军 | 55,000 | 调离将削弱边防 |
| 唐 | 剑南军 | 30,900 | 杨系影响 |
| 燕 | 安禄山直属 | 80,000 | 洛阳方向 |
| 燕 | 崔乾佑潼关前线 | 20,000 | 史料也有“数千”说法，区间 4,000-20,000 |
| 燕 | 范阳留守 | 50,000 | 后方守备 |
| 燕 | 史思明河北部 | 50,000 | 独立性较高 |
| 燕 | 平卢军 | 30,000 | 后方/侧翼 |
| 燕 | 河东占领军 | 25,000 | 与“河东军”地域口径冲突 |
| 燕 | 睢阳围攻军 | 130,000 | 属 757 年状态，不应在 756-06 以现役位置导入 |
| 外部 | 吐蕃总动员估计 | 150,000 | 不是可立即投放到关中的单支军队 |
| 外部 | 回纥总动员估计 | 80,000 | 可谈判援军首批 5,000-10,000 |
| 外部 | 南诏 | 50,000 | 战略势力池 |
| 外部 | 契丹 | 30,000 | 部族池 |
| 外部 | 奚 | 20,000 | 部族池 |

D2 唐军逐项合计为 **712,600**，不是 `summary_statistics.total_troops_tang_side=612,600`；总数少算 100,000。叛军逐项确为 385,000，但其中 130,000 睢阳围军时点错误。两方总兵力不得直接用于开局强弱比较。

### 5.3 可战人数与补员

```text
fit_strength = present_strength
  - wounded - sick - detached - absent

readiness_ratio = clamp(0.15, 1.0,
  0.30
  + 0.20 * training/100
  + 0.15 * equipment/100
  + 0.15 * morale/100
  + 0.10 * cohesion/100
  + 0.10 * supply_ratio
  - 0.25 * fatigue/100)

daily_desertion_rate = clamp(0, 0.012,
  0.0001
  + 0.002 * max(0, 0.7 - supply_ratio)
  + 0.002 * max(0, arrears_days - 15)/30
  + 0.003 * max(0, 40 - morale)/40
  + 0.002 * max(0, 40 - loyalty_to_commander)/40)
```

补员并非点击即到：`recruit_pool` 扣除后，训练 15-60 日。民团基础训练 25、市井新募 32、正规募兵 45、边军 65。每日训练增长 `instructor_quality * 0.015`，上限由训练设施决定。

## 6. 人物、关系、派系与命令执行

### 6.1 人物字段

现有 D3 每人 9 个 0-100 属性：`ability, loyalty, integrity, courage, diplomacy, military, administration, politics, scholarship`。实现时 `ability` 改为其余能力的展示摘要，不参与公式，避免重复加权。新增：

| 字段 | 范围 | 756-06 示例 | 可见性 |
|---|---:|---|---|
| `health` | 0-100 | 玄宗 54；哥舒翰 32；郭子仪 78；安禄山 22 | 模糊 |
| `stress` | 0-100 | 玄宗 72；哥舒翰 88；郭子仪 42；安禄山 86 | 模糊 |
| `ambition` | 0-100 | 杨国忠 80；郭子仪 28；史思明 92 | 隐藏/推测 |
| `risk_tolerance` | 0-100 | 个性映射 | 推测 |
| `trust_regime` | 0-100 | 与静态忠诚拆分 | 推测 |
| `office_power` | 0-100 | 职位实际权力 | 可见 |
| `information_access` | 0-100 | 接触信息能力 | 不完全可见 |
| `grievance` | 0-100 | 累积怨恨 | 隐藏 |
| `obligation_ids` | ID[] | 恩义、任命、誓约 | 已知部分可见 |

关键调研基线：玄宗政治 90/行政 88；杨国忠政治 85/军事 35/忠诚 40；哥舒翰军事 92/忠诚 75；郭子仪军事 93/政治 88/忠诚 95；安禄山军事 90/政治 80/忠诚 10。它们仅保证剧本内部相对排序，非客观历史评分。

健康按日而非每回合衰减：

```text
daily_health_delta =
  - age_decay(age)               # 50岁以下 0；50-64: 0.003；65+: 0.008/日
  - chronic_disease_rate
  - max(0, stress - 70) * 0.0008
  + care_quality * 0.004

death_hazard_daily = base_age_hazard
  * disease_multiplier
  * (health < 20 ? 4 : 1)
```

历史定年死亡是默认时间线的事件条件，不是无视状态的硬杀；玩家改变因果后，转入风险模型。

### 6.2 双向关系

关系边保存 `trust, fear, respect, affection, grievance`（均 -100..100 或 0..100）及公开程度。D3 单一 `tension` 迁移为 `grievance/fear`，关系类型仅作标签。

```text
acceptance_score =
  0.24 * trust_issuer
  + 0.16 * loyalty_to_regime
  + 0.14 * order_legitimacy
  + 0.12 * objective_agreement
  + 0.10 * clarity
  + 0.08 * supply_feasibility
  + 0.08 * commander_courage
  + 0.08 * fear_of_sanction
  - 0.12 * personal_risk
  - 0.10 * grievance
  - 0.08 * conflicting_orders
```

所有输入归一化到 0-100，最后 clamp。`>=70` 按令执行；50-69 保守执行；30-49 拖延/变更；15-29 象征执行或拒令；`<15` 才进入公开抗命候选。叛变另需：动机 `>=60`、能力 `>=50`、机会 `>=50`、替代归属 `>=40` 四项同时满足。

### 6.3 派系

开局议题影响力沿用调研：杨国忠系 45、哥舒翰/边将系 30、太子系 15、宦官系 10。它们是当前朝议权重，并非人口百分比。

| 字段 | 范围 | 刷新 | UI |
|---|---:|---|---|
| `influence` | 0-100 | 旬/事件 | 可见 |
| `cohesion` | 0-100 | 旬 | 模糊 |
| `access_to_emperor` | 0-100 | 任命/事件 | 可见 |
| `military_backing` | 人/战力 | 日 | 推测 |
| `agenda_support[issue]` | -100..100 | 事件 | 可见于朝议 |
| `radicalization` | 0-100 | 旬 | 隐藏 |

派系影响力不要求总和 100；UI 可按某议题归一化为席位比例。政变不能由“影响力 >60 且皇室信任 <30”两项自动触发，还须具备首都武力、合法性叙事和关键节点控制。

## 7. 情报与战争迷雾

### 7.1 情报对象

每条报告保存：`claim_type`、`subject`、`claimed_value/range`、`true_value`（仅内核）、`source_id`、`source_chain_id`、`observed_at`、`delivered_at`、`reliability_prior`、`corroboration`、`deception_risk`、`confidence`、`known_by`。

| 来源 | 先验可靠度 | 时效半衰期 | 典型偏差 |
|---|---:|---:|---|
| 直属斥候 | 0.72 | 5 日 | 视野有限 |
| 地方官 | 0.62 | 12 日 | 报喜避祸 |
| 商旅 | 0.48 | 10 日 | 传闻、滞后 |
| 降人/俘虏 | 0.45 | 7 日 | 求生、诱骗 |
| 独立密探 | 0.70 | 15 日 | 成本高 |
| 监军奏报 | 0.58 | 10 日 | 派系动机修正 -0.25..0 |

```text
freshness = 2 ^ (-age_days / half_life_days)
source_quality = prior
  * freshness
  * (1 - compromise_risk)

confidence = 1 - product(1 - independent_source_quality_i)
```

共享同一 `source_chain_id` 的报告不算独立来源。玩家看到 `低/中/高` 置信及兵力区间；数值置信度只在情报机构升级或高难度关闭时显示。

敌军兵力区间宽度：

```text
relative_error = clamp(0.08, 0.80,
  0.75 - 0.55 * confidence
  + concealment * 0.25
  + deception * 0.30)
display_range = estimate * [1-relative_error, 1+relative_error]
```

“敌方权谋 >70 每回合 25% 造假、低准确率 30% 自动相信”废弃。造假是敌方行动，有成本和目标；玩家收到矛盾报告并自行决断，程序不替玩家“相信”。

## 8. 补给、军饷与围城

### 8.1 日消耗

以 GLU 统一：步兵 1.0、骑兵 2.6、民团 0.9、非战斗随军人口 0.8。骑兵系数包含人粮和折算草料。

```text
daily_food_need =
  infantry * 1.0
  + cavalry * 2.6
  + militia * 0.9
  + tribal * unit_type_factor
  + camp_followers * 0.8

activity_factor: 休整 0.95；守备 1.00；行军 1.15；战斗 1.25；严寒 1.20
actual_need = daily_food_need * activity_factor
supply_ratio = delivered_glu / actual_need
```

潼关 20 万军若构成为步 14 万、骑 4 万、部族 2 万（按骑兵 2.2），日需求约 **288,000 GLU**，30 日约 864 万 GLU。这个数用于校准，不对应史实石/斗，避免假精确换算。

供给后果按连续不足天数累积：

| 供给率 | 1-2 日 | 3-6 日 | 7 日以上 |
|---|---|---|---|
| >=0.9 | 无 | 无 | 无 |
| 0.7-0.89 | 士气 -0.2/日 | 疲劳 +0.5/日 | 疾病率 +0.1%/日 |
| 0.4-0.69 | 士气 -0.8/日 | 逃亡 +0.1%/日 | 非战斗损耗 0.15%/日 |
| <0.4 | 士气 -1.5/日 | 逃亡 +0.3%/日 | 非战斗损耗 0.4%/日 |

切断补给不再固定“每回合兵力 -5%”；结果取决于随军存粮。粮尽也不瞬间“自动溃散 30%”，而进入逐日崩解。

### 8.2 围城

```text
siege_stock_days = city_grain_glu / (garrison_need + civilian_ration_need)
fortification_daily_damage = attacker_siege_power
  * breach_focus * weather_mod / defender_repair_capacity

surrender_pressure =
  0.30 * hunger
  + 0.20 * breach
  + 0.15 * disease
  + 0.15 * isolation
  + 0.10 * elite_factionalism
  - 0.10 * commander_resolve
  - 0.10 * relief_expectation
```

“食人”不作为加粮按钮。若保留该历史内容，作为 18+ 抽象事件处理，产生不可逆人口、军心、人物创伤与声誉后果，不提供净收益式最优解。

## 9. 战斗结算

### 9.1 作战输入与战力

战斗最小单位是军队分遣队，按战场正面宽度决定实际投入人数：

```text
engaged_strength = min(fit_strength, frontage_capacity * formation_density)

quality_score =
  0.24 * training
  + 0.18 * equipment
  + 0.18 * morale
  + 0.14 * cohesion
  + 0.12 * commander_military
  + 0.08 * supply_ratio*100
  + 0.06 * (100-fatigue)

quality_multiplier = clamp(0.55, 1.55, 0.55 + quality_score/100)

tactical_multiplier = clamp(0.45, 1.75,
  1
  + terrain_delta
  + intelligence_delta
  + surprise_delta
  + formation_delta
  + command_delta
  + weather_delta)

combat_power = engaged_strength
  * arm_mix_factor
  * quality_multiplier
  * tactical_multiplier
```

`arm_mix_factor` 通常 0.85-1.15；兵种克制不超过 +/-15%，避免兵种标签压倒地形和军令。预备队不直接贡献首轮战力，但影响轮换、突破利用与撤退。

### 9.2 伤亡、溃散与追击

每个战斗脉冲 2 小时，最多 6 个脉冲/日：

```text
power_ratio = attacker_power / max(1, defender_power)
base_casualty_rate = 0.006 * intensity             # 每脉冲 0.6%-1.5%

defender_losses = engaged_defender
  * base_casualty_rate
  * clamp(0.55, 1.80, power_ratio^0.55)
  * exposure_mod
  * seeded_noise(0.90, 1.10)

attacker_losses = engaged_attacker
  * base_casualty_rate
  * clamp(0.55, 1.80, (1/power_ratio)^0.55)
  * assault_mod
  * seeded_noise(0.90, 1.10)
```

每个脉冲更新凝聚力：伤亡、侧击、失联、烟火、退路拥堵会降 cohesion。`cohesion <25` 且 `morale <35` 时开始局部溃散；全军溃散须超过 35% 投入单位崩溃或指挥链失效。追击/拥堵阶段可造成比正面战斗更高的伤亡和被俘。

```text
rout_loss_rate = clamp(0.02, 0.45,
  0.04
  + 0.18 * retreat_congestion
  + 0.12 * enemy_cavalry_exploitation
  + 0.10 * blocked_escape
  + 0.08 * panic
  - 0.10 * rearguard_quality)
```

### 9.3 灵宝历史校准场景

史实默认输入：唐账面 200,000、实际出战约 150,000；训练 38、装备 55、士气 43、凝聚 36、哥舒翰健康 32、命令冲突高；叛军 4,000-20,000 区间，训练 72、士气 80、凝聚 82、伏击准备 90；唐军进入低正面宽度狭道，侦察失败，烟火与黄河退路共同作用。

应出现：唐军首轮并非被“2 万正面杀死 16 万”，而是投入受限、指挥失联、后队拥堵，随后大规模溃散、坠河、被俘。历史配置并非必败硬编码，但蒙特卡洛失败概率需很高；玩家提前复核情报、分梯队、留预备队、保障退路可显著降低灾难，坚守则避免开战。

## 10. 外交、义务与叛军联盟

### 10.1 外交字段与基线

| 势力 | 关系 -100..100 | 威胁 0-100 | 可立即援军 | 基线意图 |
|---|---:|---:|---:|---|
| 回纥 | 5 | 35 | 5,000-10,000 骑 | 求利，可结盟 |
| 吐蕃 | -35 | 62 | 0 | 趁虚扩张 |
| 南诏 | -20 | 35 | 0-2,000 | 边境施压 |
| 契丹 | -45 | 30 | 敌方部族池 | 随利益摇摆 |
| 奚 | -35 | 25 | 敌方部族池 | 随利益摇摆 |

字段：`relation, trust, fear, leverage, war_weariness, aggression, treaty_ids, claim_ids, mobilization_pool, deployed_force, fulfillment_score`。

```text
tibet_aggression_monthly_score =
  35
  + (50 - tang_prestige) * 0.45
  + max(0, 50 - western_control) * 0.55
  + western_troop_withdrawal_ratio * 25
  - treaty_deterrence

aggression >=70：准备入侵；>=85：若路径可行则发动。
```

### 10.2 可追踪义务

每份外交或政治承诺保存：

| 字段 | 说明 |
|---|---|
| `debtor/creditor` | 义务双方 |
| `kind` | 岁币、和亲、劫掠许可、封爵、军权、归还领土等 |
| `amount/unit` | 数量与单位 |
| `due_date/window` | 到期或执行窗口 |
| `publicity` | 秘密、有限公开、公开 |
| `fulfillment_progress` | 0-100 |
| `breach_severity` | 0-100 |
| `autonomy_debt` | 0-100，授军权/保留部曲造成 |
| `civilian_cost` | 人口/治安风险 |

回纥首轮援军建议套餐：骑兵 5,000，预付 8,000 CP 等价物，年付 20,000 绢等价义务，战利品许可范围 0-100，和亲政治成本 12-25。玩家可谈判改变各项，不允许“固定花 5,000 金直接招兵”。

### 10.3 叛军联盟

联盟按安禄山直属、史思明部、地方降军、族群武装分开保存：`cohesion, leader_legitimacy, loot_satisfaction, supply, fear, succession_tension, exit_option`。

```text
coalition_stability =
  0.25 * leader_legitimacy
  + 0.20 * recent_campaign_success
  + 0.15 * supply
  + 0.15 * loot_satisfaction
  + 0.10 * shared_enemy_pressure
  + 0.10 * fear
  + 0.05 * personal_ties
  - succession_tension * 0.25
```

旬度计算，`<40` 出现公开争执，`<25` 成员寻求退路，`<15` 且有替代归属时可脱离。安禄山死亡不是“首领死亡率 ×20”，而是一次继承冲击，并由成员关系决定方向。

### 10.4 政治与私人义务

外交义务与国内恩义共用同一账本，另用 `scope` 区分 `international/court/military/private`。任命、救命之恩、保留部曲、赦免旧罪、婚姻和质子均必须形成记录，不能只加一次忠诚后消失。

```text
obligation_pressure = face_value
  * publicity_factor(秘密 0.7, 有见证 1.0, 天下皆知 1.3)
  * urgency_factor
  * creditor_leverage

honor_cost_on_breach = obligation_pressure
  * character_integrity/100
  * relationship_weight
```

人物是否履约由诚信、利害、恐惧、关系和替代选项共同决定。义务状态为 `promised -> due -> fulfilled/breached/renegotiated`；每次转移写审计日志。UI 对己方公开承诺显示准确值，对秘密恩义只显示已知线索。

## 11. 自治债务与终局

### 11.1 藩镇自治

每个军镇保存：`troop_share, tax_retention, appointment_rights, hereditary_tendency, local_legitimacy, central_trust, distance, retained_rebel_command, obligation_debt`。

```text
governor_autonomy = clamp(0, 100,
  0.20 * troop_share_normalized
  + 0.18 * tax_retention
  + 0.15 * appointment_rights
  + 0.14 * hereditary_tendency
  + 0.12 * local_legitimacy
  + 0.10 * obligation_debt
  + 0.07 * distance_factor
  + 0.04 * retained_rebel_command
  - 0.15 * central_trust)

warchief_autonomy_index =
  weighted_mean(governor_autonomy, weights = governor_controlled_troops)

central_control = clamp(0, 100,
  45 * central_army_ratio
  + 20 * fiscal_health/100
  + 15 * prestige/100
  + 10 * appointment_control
  + 10 * transport_control
  - 35 * warchief_autonomy_index/100)
```

旧公式 `Σ(兵力 × 独立倾向 × 0.01)` 无法保证 0-100，军队规模一大即溢出，废弃。

### 11.2 六维终局评分

| 维度 | 权重 | 0 分 | 100 分 |
|---|---:|---|---|
| 皇统连续 | 15% | 政权分裂/断绝 | 合法继承且无双中心内战 |
| 两京与核心领土 | 20% | 两京皆失 | 两京稳定控制、交通畅通 |
| 叛军瓦解 | 15% | 主力仍完整 | 组织瓦解且无复叛能力 |
| 中央控制 | 20% | 军阀化 | 中央军/财/任命权稳固 |
| 财政民生 | 20% | 财政破产、人口灾难 | 税路恢复、低破坏低流民 |
| 外交边疆 | 10% | 西域/河陇大失、债务违约 | 边疆可守、条约履行 |

```text
final_score = weighted_sum(dimensions) - atrocity_penalty - oath_breach_penalty
```

结局阈值只组合，不用一条总分抹平代价：

- **中兴而有制**：总分 >=80，中央控制 >=70，民生 >=60。
- **两京复得，藩镇坐大**：叛军瓦解 >=75，但中央控制 35-69。
- **中兴失边**：核心领土 >=70，但外交边疆 <35。
- **胜而民殇**：军事相关 >=75，但民生 <30。
- **王朝分裂**：皇统 <30 或两套朝廷持续敌对。
- **五代前夜**：中央控制 <25 且 3 个以上军镇自治 >=75。

## 12. 难度与 AI 数值权限

难度不得直接给敌军“伤害 +50%”。使用信息、容错与规划深度：

| 项目 | 剧情 | 标准 | 史实 |
|---|---:|---:|---:|
| 玩家情报区间宽度 | -25% | 基准 | +20% |
| 命令风险预览 | 精确分档 | 分档 | 仅异议 |
| 敌方规划深度 | 1 | 2 | 3 |
| 战败自动建议 | 开 | 可选 | 关 |
| 随机噪声 | +/-6% | +/-10% | +/-10% |
| 存档限制 | 无 | 无 | 可选铁人 |

各 AI 只能读同一版本快照并输出提案。军事 AI 输出 `intent/target/priority/constraints`；情报 AI 输出报告与置信依据；人物 AI 输出立场与言辞；叙事 AI 输出战报。所有数值增量由模拟内核返回，AI 响应中的未知字段一律拒绝。

## 13. 平衡仿真与验收目标

每个正式版本固定运行至少 10,000 局批量模拟；关键切片每个策略配置 50,000 个 seed。保存初始数据版本、策略 bot 版本和 seed。

### 13.1 潼关切片

| 策略 | 标准难度目标 |
|---|---:|
| 完全按史实催战、无额外侦察 | 唐军灾难性失败 80-92% |
| 出战但分梯队、侦察、留预备队和退路 | 灾难性失败 30-50%，有序撤退 25-40% |
| 坚守潼关 30 日且河北战线未崩 | 守住 70-85% |
| 无前置投入、最后一刻单选“坚守” | 守住不高于 55%，避免无成本正确答案 |

灾难性失败定义：潼关失守，且出战军死亡/失踪/被俘 >45%，或指挥链崩溃。历史极端结果应处于分布尾部但合理可达。

### 13.2 全战役

标准策略 bot 与不同风格 bot 的目标：

- 首通有效回合 P50 40，P10-P90 为 34-50；无重大决策的连续自动推进不超过 2 次。
- 标准难度新手获“任何可继续结局”概率 65-80%，最优结局概率 3-8%。
- 熟练 bot 最优结局 12-25%，不允许单一开局策略 >60% 占优。
- 史实路径在无玩家反事实干预时，关键事件时序落入历史窗口的比例 >=70%，但不硬锁结果。
- 单次战斗同输入不同 seed 的胜率若在 20-80% 区间，伤亡 P90/P10 比不超过 2.5；优势比 >2:1 时弱方翻盘率通常 <10%，伏击/隘道例外必须能由战报解释。
- 经济系统中任何阵营不得凭空产生资源；全局账本误差为 0。
- 玩家等待性能目标由架构测试负责，但数值模拟本体单回合 P95 <100ms，10,000 局无 UI 批处理可并行运行。

### 13.3 敏感性与回归

对训练、士气、补给、情报、地形、统帅六个核心输入分别做 +/-10 点敏感性测试：正常区间中任何单项不应让胜率跳变超过 20 个百分点；灵宝的地形和情报联合作用允许超过，但须不是单一隐藏阈值。每次改公式保存胜率、平均伤亡、资源余量、终局分布的基线快照。

## 14. 审计发现、矛盾与处理决定

| 严重度 | 问题 | 处理决定 |
|---|---|---|
| P0 | D2 唐军逐项 712,600，摘要写 612,600 | 禁用摘要总数；由导入器实时求和并校验 |
| P0 | 睢阳围攻军 130,000 属 757 年，却放入 756-06 军队基线 | 改为未来编成模板/事件生成，不计开局现役 |
| P0 | D4 有 22 地区但仅 16 条交通边，北庭、江陵、扬州等孤立 | 地图补边前禁止进入完整战役 |
| P0 | D6 按“每回合”扣粮、健康、土地，事件时钟又有 1-90 日回合 | 全部改为日率 |
| P0 | D1 `military_power` 是 0-100，D5 却对其减 30,000-90,000 | 事件改为具体军队损失，摘要派生 |
| P0 | D1 叛变式 `(100-loyalty)*0.01*ambition` 若 ambition 为 0-100 会远超概率 1 | 采用四条件叛变模型，不以单骰替代因果 |
| P1 | 河东军 D2 为 45,000，研究报告称 55,000 | 保存 45,000-55,000 区间；原型点值 50,000，待史料核验 |
| P1 | 潼关唐军既称 200,000，又引文称出关步兵 150,000 | 前者存 `paper_strength`，后者存 `deployed_strength` |
| P1 | 崔乾佑军一处 20,000，一手引文称数千/四五千 | 保存 4,000-20,000 区间；场景采样和难度不能偷偷改变真实值 |
| P1 | 河北义军 200,000 被当作单一军队且构成字段仅 30,000 民团 | 拆为多个地方节点；大数解释为响应/声势上限，不是集中野战军 |
| P1 | 外部势力“总兵力”等同可用援军 | 拆 `mobilization_pool` 与 `deployed_force` |
| P1 | 地区和军队均产生 `grain_per_turn`，有重复记账风险 | 只有地区/仓储生产资源；军队的旧 `resource_output` 删除或解释为随营缴获上限 |
| P1 | D3 44 人，目标/旧规划多处写 68 人 | 数值表只承诺现有 44；新增 24 人须独立审校后导入 |
| P1 | D6 士气 >=80 给攻击 +20%、防御 +15%、追击 +40%，跨阈值跳变 | 改连续质量评分；追击单独计算 |
| P1 | 旧有效战力把士气、地形、情报、健康直接连乘，易趋零并重复惩罚 | 使用加权质量与有界战术倍率 |
| P1 | `width <5 米` 与 20 万人战略单位不在同一地图尺度 | 改为抽象 `frontage_capacity`，具体米数只作战场资料 |
| P2 | `central_prestige=45` 同时作为史实事实和设计值 | 标为设计基线；保留理由和来源，不称可考绝对值 |
| P2 | 经济金粮没有史实单位与价格体系 | MVP 使用 CP/GLU；若未来改钱帛石斗，需专门经济史研究和版本迁移 |
| P2 | D1 固定日期 fail condition 会抵消玩家反事实选择 | 日期只触发压力，失败由状态和行动导致 |

## 15. 待补研究与数据验收

进入垂直切片前必须完成：

1. 为潼关/灵宝的兵力、投入人数、伤亡结构建立逐项来源矩阵，区分《旧唐书》《新唐书》《资治通鉴》与现代转述。
2. 核验河东军 45,000/55,000、河北义军 200,000、睢阳围军 130,000 的口径和日期。
3. 补全 22 地区交通图，每条边至少有行军日、容量、水陆、季节与控制规则；D4 所称长安至朔方 4 日、长安至剑南 6 日等明显可能过短，须核验。
4. 建立 756 年六月真正存在的军队快照；未来部队使用 `available_from`，不得提前占用粮饷和地图位置。
5. 经济史专题决定是否将 CP/GLU 转换为钱、绢、石/斛；在证据不足前保持抽象单位并公开说明。
6. 44 名现有人物逐一做属性相对排序审校；`ability` 不进公式，性格标签映射成行为倾向而非战力加成。
7. 为回纥和亲、岁币、战利品约定建立不同史源版本，外交义务显示“史载/推演/纯设计”。

数据导入硬校验：ID 唯一；兵种和等于在队人数；负资源拒绝；关系目标存在；军队所在地区存在；交通图关键节点可达；事件角色/地区存在；`source_ids` 非空；未来状态不早于 `available_from`。任何 P0 校验失败应阻断构建，而不是在运行时静默修正。

## 16. 实施顺序

1. **M0 数据合同**：实现以上类型、日率、账本、证据字段和校验器。
2. **M1 潼关切片**：只接长安-潼关-灵宝-陕郡，哥舒翰部与崔乾佑部，军令、情报、补给、战斗和溃退。
3. **M2 河北与两京**：补交通图、军队拆分、地方控制、征募和回纥义务。
4. **M3 全战役**：围城、叛军联盟、皇统切换、吐蕃与自治债务。
5. **M4 平衡**：运行固定 bot/seed 基准，锁定 v1 公式；此时才允许微调基线，不允许用事件脚本掩盖系统失败。

本规格的判定标准不是“表很多”，而是任何一个显示数字都能追到来源、单位、公式和变化日志；任何一次失败都能由相同输入重放。
