# Dennis Agent Capability Overview v1

## 当前阶段一句话总结

Dennis Agent 已从“单平台只读手脚验证”进入“多源取证、专家研判、证据编排、能力治理”的阶段。

本文是当前统一推荐入口，用一份文档同时承载两种视角：

- 对内工程协作视角：四层架构，即意图识别 / 研判编排 / 平台手脚 / 契约治理。
- 对外汇报复盘视角：专家能力，即大脑 / 手脚 / 证据 / 输出 + 安全防护底座。

后续主表达应优先使用能力名称，而不是历史分包名称。历史分包只作为括号说明，例如“批量风险分簇能力（历史 A 包）”、“多源证据编排能力（历史 B 包）”、“天狮策略平台取证能力（历史 C 包）”。

## 对内工程协作视角：四层架构

### 第一层：意图识别

职责：

- 判断用户问题属于单用户研判、批量分析、单点证据查询、平台细查、策略建议、策略树解释还是离线聚合。
- 决定进入哪条能力链路。

典型路由：

- 单用户综合研判 → 多源证据编排能力。
- 批量风险分析 → 批量风险分簇能力。
- 策略命中查询 → 天狮 `fastQueryHbase`。
- 请求级明细细查 → 天狮 `eventList`。
- 登录链路查询 → 统一登录日志。
- 账号画像查询 → 档案中心。
- 策略树解释 → 后续策略树理解能力。
- 批量 / 跨天 / 历史聚合 → DataAgent / Hive，按需生成计划。

### 第二层：研判编排

职责：

- 单用户多源证据编排。
- 批量风险分簇。
- 举一反三 / 策略建议。
- case learning / bad case 沉淀。
- 输出取证计划、风险簇摘要、`evidence_summary`。

当前重点能力：

- 多源证据编排能力（历史 B 包）：面向单用户 / 单事件综合研判，默认编排天狮、统一登录日志、档案中心。
- 批量风险分簇能力（历史 A 包）：面向一批 user / case / did / event，做 L1 浅查、TOP 维度、频繁项、有向异常相关、代表样本和风险簇摘要。
- 策略建议 / 举一反三：输出扩展锚点、灰度验证、误伤控制、监控指标和候选策略方向。
- case learning / bad case：沉淀 run log、case learning note、golden sample 和 regression。

### 第三层：平台手脚

职责：

- 从具体平台或数据源拿事实。
- 输出标准 observation。
- 不直接做最终风险定性。

当前与后置能力：

- 天狮策略平台取证能力（历史 C 包）
  - `fastQueryHbase`：策略命中概览。
  - `eventList`：请求级 / 事件级细查。
- 统一登录日志：登录、验证、token、三方登录链路。
- 档案中心：账号画像、账号状态、历史风险、封禁、审核信息。
- 前端活跃画像，后置。
- 设备 SDK / Weapon，后置。
- DataAgent / Hive：批量、跨天、历史聚合、离线指标、分母和 baseline。

### 第四层：契约治理

职责：

- 防止 Agent 乱查、乱解释、乱下结论。
- 管能力注册、路由、输入输出、observation、边界、回归和安全。

包含：

- capability registry。
- scene routing。
- contract。
- observation schema。
- smoke / regression。
- browser auth preflight。
- safety boundary。
- 防止 `no_data` 当无风险。
- 防止 auth blocker 当 `no_data`。
- 防止单一证据强判。
- 防止越权和敏感信息泄露。

## 对外汇报复盘视角：专家能力

专家能力主链路：

用户问题
→ 大脑
→ 手脚
→ 证据
→ 输出
→ 安全防护底座贯穿全链路

### 大脑

职责：

- 意图识别。
- 任务路由。
- 单用户多源研判。
- 批量风险分簇。
- 策略建议 / 举一反三。
- case learning。
- 未来策略树理解。

### 手脚

职责：

- 天狮策略平台。
- 统一登录日志。
- 档案中心。
- 前端活跃。
- 设备 SDK / Weapon。
- DataAgent / Hive。

手脚只负责取事实和输出 observation，不直接做最终风险定性。

### 证据

证据负责把 raw data 标准化为可追溯、可比较、可合并的 evidence。

证据类型：

- `strategy_evidence`
- `event_detail_evidence`
- `login_evidence`
- `profile_evidence`
- `behavior_evidence`
- `device_evidence`
- `offline_aggregate_evidence`
- `supporting_evidence`
- `counter_evidence`
- `missing_evidence`
- `blockers`

### 输出

输出面向策略同学，要求可读、可执行、不过度定性。

输出形态：

- `evidence_summary`
- `risk_assessment_summary`
- batch cluster summary
- `recommended_next_checks`
- strategy recommendation
- boundary notes
- case learning note
- run log / regression

### 安全防护底座

安全防护底座贯穿大脑、手脚、证据和输出。

包含：

- contract。
- routing。
- schema。
- regression。
- auth preflight。
- 敏感信息保护。
- 不自动处置。
- 不强判。
- 不越权。
- `no_data` 不当无风险。
- auth blocker 不当 `no_data`。

## 两种视角的对应关系

| 对外专家能力视角 | 对内工程协作视角 | 说明 |
|---|---|---|
| 大脑 | 意图识别 + 研判编排 | 决定怎么想、查什么、怎么归因 |
| 手脚 | 平台手脚 | 查平台、取数据 |
| 证据 | observation schema + evidence summary | 把 raw data 标准化为可追溯证据 |
| 输出 | evidence summary / 风险簇摘要 / 策略建议 | 面向策略同学交付 |
| 安全防护底座 | 契约治理 | 贯穿全链路的质量和安全护栏 |

## 当前已具备的核心能力

### 批量风险分簇能力

历史 A 包。当前支持：

- L1 浅查。
- TOP 维度。
- 频繁项。
- A→B 有向相关。
- 代表样本。
- 风险簇摘要。
- 取证计划。

### 多源证据编排能力

历史 B 包。当前支持：

- 单用户 / 单事件综合研判。
- 默认编排天狮、登录日志、档案中心。
- 支持 supporting / counter / missing / blockers。
- 支持 evidence summary。

### 天狮策略平台取证能力

历史 C 包。当前支持：

- `fastQueryHbase`：策略命中概览。
- `eventList`：请求级 / 事件级细查。
- 已固化 `sourceIds` 非空、小窗口、不跨天、抽样边界、auth blocker、`no_data` 边界。

### 登录日志取证能力

当前支持：

- 登录链路。
- 验证链路。
- token 链路。
- 三方登录链路。

### 档案中心取证能力

当前支持：

- 账号画像。
- 账号状态。
- 历史风险。
- 封禁信息。
- 审核信息。
- recoverable preflight：账号 / 用户名预填时点击“下一步”可恢复会话。

### 后置能力

后续单独建设：

- 策略树理解。
- 前端行为链路。
- 设备账号关联与设备风险。

## 已验证真实链路

- 天狮 `fastQueryHbase` 已验证策略命中概览。
- 天狮 `eventList` 已验证 POST API-read 请求级细查。
- 三源 E2E 已验证：天狮 + 统一登录日志 + 档案中心。
- 档案中心账号 / 用户名预填时点击“下一步”可恢复 preflight。
- `eventList` 已验证 `source_id=2740906395` 的 `USER_REGISTER_NEW` 明细。

## 关键边界

- 单一证据不等于最终作弊定性。
- 天狮命中不等于最终处置成功。
- `eventList no_data` 不代表行为未发生。
- 非命中策略事件存在抽样。
- `sourceIds` 不能为空。
- `eventList` 原则上不跨天。
- auth blocker 不得当 `no_data`。
- DataAgent / Hive 不是万能底座，只用于批量、跨天、历史聚合、离线指标。
- 策略树不在当前天狮取证能力内，后续单独建设。

## 推荐阅读顺序

1. `computer_use_poc/dennis_agent_capability_overview_v1.md`
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
- 不移动历史文件。
- 不重命名已有目录。
- 不删除既有 architecture / expert view 文档。
- 不新增真实查询。
