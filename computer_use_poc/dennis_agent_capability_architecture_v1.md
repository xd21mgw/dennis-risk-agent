# Dennis Agent Capability Architecture v1

本文是 Dennis Risk Agent 当前能力体系的推荐起点，用四层架构重新组织 A/B/C/D/E/F 能力包、平台手脚、contract/schema/routing/regression 和安全边界。

核心澄清：A/B/C/D/E/F 不是同一层级的并列模块。A/B 是研判大脑 / 分析编排能力，C/E/F 是证据取数 / 平台手脚能力，D 是未来策略配置理解能力，contract/schema/routing/regression 是能力治理层。

## 四层架构

### 第一层：意图识别与任务路由层

职责：

- 识别用户到底要做什么。
- 判断是单用户研判、批量分析、单点证据查询、平台细查、策略建议，还是未来策略树解释。
- 决定进入 A/B/C/D/E/F 哪类能力链路。

典型路由：

| 用户意图 | 目标链路 |
|---|---|
| 单用户综合研判 | B 包：多源证据编排 |
| 批量风险分析 | A 包：批量风险分簇 |
| 策略命中查询 | C 包：天狮 `fastQueryHbase` |
| 请求级明细细查 | C 包：天狮 `eventList` |
| 登录链路查询 | 统一登录日志 |
| 账号画像查询 | 档案中心 |
| 策略树解释 | D 包，后置 |
| 前端行为链路 | E 包，后置 |
| 设备账号关联 | F 包，后置 |
| 批量 / 跨天 / 历史聚合 | DataAgent / Hive，按需 |

### 第二层：研判大脑 / 分析编排层

职责：

- 组织分析思路。
- 决定查哪些证据源。
- 合并 supporting / counter / missing / blockers。
- 输出 `evidence_summary`、风险簇摘要、取证计划或策略建议。

包含能力：

#### B 包：单用户多源证据编排

面向问题：

- “这个用户是不是风险？”
- “为什么被拦 / 为什么登录验证？”
- “这个具体 case 怎么判断？”

默认编排：

- 天狮 `fastQueryHbase`：策略命中概览。
- 统一登录日志：登录 / token / 验证链路。
- 档案中心：账号画像 / 历史风险 / 当前状态。

条件补证：

- 需要请求字段时补天狮 `eventList`。
- 后续可补 E 包前端行为、F 包设备证据、DataAgent / Hive 离线聚合。

#### A 包：批量风险分簇

面向一批 user / case / did / event：

- L1 宽表 / 画像浅查。
- TOP 维度下探。
- 频繁项 / 贡献度分析。
- A → B 有向异常相关。
- 代表样本抽样。
- 风险簇摘要。
- 取证计划和策略建议。

#### 举一反三 / 策略建议

当前作为专家分析模式使用，用于扩展锚点、监控指标、灰度验证、误伤控制和策略候选方向。后续可单独契约化。

#### case learning / bad case 沉淀

通过 run log、case learning note、golden sample、smoke / regression 防止退化。

### 第三层：证据取数 / 平台手脚层

职责：

- 从具体平台或数据源拿证据。
- 输出标准 observation。
- 不直接做最终风险定性。

包含能力：

#### C 包：天狮 / 策略平台取证能力

- `fastQueryHbase`：策略命中概览。
- `eventList`：请求级 / 事件级细查。
- 不包含策略树解析。

#### 统一登录日志

用于登录、验证、token、三方登录链路补证。`no_data`、超窗、blocked、timeout 必须进入 evidence gap，不得作为无风险强反证。

#### 档案中心

用于账号画像、历史风险、当前状态、封禁、审核信息。历史封禁不得自动与今日策略命中合并为同一因果链。

#### E 包：前端行为证据，后置

未来覆盖前端活跃、访问路径、行为序列、页面模块行为。

#### F 包：设备账号证据，后置

未来覆盖用户 ↔ 设备、设备风险、设备一致性、root / hook / 多开 / 模拟器。

#### DataAgent / Hive

用于批量、跨天、历史聚合、离线指标、分母和 baseline。DataAgent / Hive 是离线取数分析能力，不是万能数据底座。

### 第四层：能力契约 / 安全治理层

职责：

- 防止 Agent 乱查、乱解释、乱下结论。
- 管能力注册、路由、输入输出、observation、边界、回归和安全。

包含：

| 治理资产 | 职责 |
|---|---|
| `capability_registry.md` | 管有哪些能力、能力叫什么、在哪里 |
| `scene_to_capability_routing.md` | 管用户问题应该走哪类能力 |
| contract | 管每个能力怎么用、输入输出是什么、边界是什么 |
| observation schema | 管平台返回怎么标准化成证据 |
| smoke / regression | 防止 no_data 当无风险、eventList 跨天查、单证据强判、sourceIds 为空、auth blocker 被误当 no_data |
| browser auth preflight | 管登录态、独立登录域、可恢复 preflight |
| safety boundary | 不输出 cookie/token/header，不做写操作，不自动处置，不越权 |

## A/B/C/D/E/F 重新归属表

| 包 | 当前归属层级 | 能力类型 | 定位 |
|---|---|---|---|
| A 批量风险分簇 | 第二层：研判大脑 / 分析编排层 | 批量分析能力 | 批量输入 → L1 浅查 → TOP 维度 → 频繁项 → A→B 有向相关 → 代表样本 → 风险簇摘要 / 取证计划 / 策略建议 |
| B 多源证据编排 | 第二层：研判大脑 / 分析编排层 | 单用户 / 单事件综合研判编排能力 | 面向单用户综合研判，编排天狮、统一登录日志、档案中心，并输出 evidence summary |
| C 天狮策略平台能力契约 | 第三层 + 第四层 | 平台取证能力 + 能力契约治理 | 提供 `fastQueryHbase` 和 `eventList` 的只读取证 contract、schema、routing、regression |
| D 策略树理解 | 未来能力 | 策略配置理解能力 | 解析策略树、节点、条件表达式、命中路径、版本 / 实验 / 灰度，当前不在 C 包内 |
| E 前端行为链路 | 第三层，后置 | behavior evidence | 前端活跃、访问路径、行为序列、页面模块行为 |
| F 设备账号关联 | 第三层，后置 | device evidence | 用户 ↔ 设备、设备风险、设备一致性、root / hook / 多开 / 模拟器 |

## 关键澄清

- A/B/C/D/E/F 不是同一层级的并列模块。
- B 和 C 不是同级调用关系；B 是编排能力，C 是被 B 调用的取证能力。
- A 和平台手脚会并列出现在能力地图里，但不是同类；A 是分析能力，平台手脚是取证能力。
- contract/schema/routing/regression 不是业务取证能力，而是第四层治理能力。
- DataAgent / Hive 是离线取数分析能力，不是万能数据底座。
- D/E/F 暂不展开，不影响当前主链路。

## 主链路文字流程图

### 单用户综合研判

用户问题
→ 第一层：意图识别与任务路由
→ 如果是单用户综合研判
→ 第二层：B 包多源证据编排
→ 第三层：调用 C 包天狮、统一登录日志、档案中心，必要时 E/F/DataAgent
→ 第二层：合并 `evidence_summary`
→ 第四层：contract/schema/regression/safety 约束全链路

### 批量风险分析

用户问题
→ 第一层：意图识别与任务路由
→ 如果是批量风险分析
→ 第二层：A 包批量风险分簇
→ 输出风险簇摘要、代表样本、取证计划
→ 必要时调用第三层平台手脚或 DataAgent/Hive

### 策略树解释

用户问题
→ 第一层：意图识别与任务路由
→ 如果是策略树解释
→ 标记 `future_strategy_tree_capability`
→ 后续进入 D 包，不在当前 C 包内强答

## 推荐阅读顺序

1. `computer_use_poc/dennis_agent_capability_architecture_v1.md`
2. `computer_use_poc/capability_registry.md`
3. `computer_use_poc/scene_to_capability_routing.md`
4. `computer_use_poc/multi_evidence_orchestration_contracts/README.md`
5. `computer_use_poc/tianshi_strategy_platform_contracts/README.md`
6. `computer_use_poc/observation_contract_v2_4_6.md`
7. `computer_use_poc/smoke_tests.md`

## 当前不处理项

- 不访问真实平台。
- 不调用 DataAgent。
- 不更新 release package。
- 不修改核心 Skill。
- 不重命名或移动已有目录。
- 不展开 D/E/F 具体实现。
- 不新增真实查询。
