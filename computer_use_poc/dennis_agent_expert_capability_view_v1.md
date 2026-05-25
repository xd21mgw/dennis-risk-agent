# Dennis Agent Expert Capability View v1

本文是 Dennis Agent 的专家能力视角总览，适合组内分享、复盘总结和对非工程同学解释当前能力体系。

`dennis_agent_capability_architecture_v1.md` 是工程架构视角，按四层组织：意图识别与任务路由层、研判大脑 / 分析编排层、证据取数 / 平台手脚层、能力契约 / 安全治理层。

本文用另一套表达：大脑 → 手脚 → 证据 → 输出，并把安全防护层作为贯穿底座。两者不是互相替代，而是同一体系的两种表达。

## 两种视角的关系

- 四层架构 = 工程架构视角。
- 大脑 / 手脚 / 证据 / 输出 = 专家能力视角。
- 两者不是互相替代，而是面向不同受众的表达。
- 专家能力视角更适合汇报、复盘、组内分享。

## 专家能力主链路

用户问题
→ 大脑：意图识别、任务路由、研判编排、归因判断
→ 手脚：调用天狮、登录日志、档案中心、前端、设备、Hive
→ 证据：把平台返回标准化为 supporting / counter / missing / blockers
→ 输出：形成 evidence_summary、风险簇摘要、策略建议、case learning
→ 安全防护层贯穿全链路

## 大脑

大脑负责“怎么想、查什么、怎么归因”。

职责：

- 意图识别。
- 任务路由。
- 单用户多源证据编排。
- 批量风险分簇。
- 策略建议 / 举一反三。
- case learning / bad case 沉淀。
- 未来策略树理解。

对应能力：

| 能力 | 说明 |
|---|---|
| A 包：批量风险分簇 | 面向一批 user / case / did / event，做 L1 浅查、TOP 维度、频繁项、有向异常相关、代表样本和风险簇摘要 |
| B 包：多源证据编排 | 面向单用户 / 单事件综合研判，编排天狮、统一登录日志、档案中心等证据源 |
| 策略建议 / 举一反三 | 输出扩展锚点、灰度验证、误伤控制、监控指标和候选策略方向 |
| case learning | 通过 bad case、run log、regression、golden sample 防退化 |
| 未来 D 包：策略树理解 | 后续理解策略树、节点条件、命中路径、版本 / 实验 / 灰度 |

## 手脚

手脚负责“从哪里拿事实”。它从平台和数据源取证，输出 observation，不直接做最终风险定性。

对应能力：

| 手脚 / 数据源 | 说明 |
|---|---|
| C 包：天狮策略平台 | 策略平台只读取证能力 |
| `fastQueryHbase` | 策略命中概览 |
| `eventList` | 请求级 / 事件级细查 |
| 统一登录日志 | 登录、验证、token、三方登录链路 |
| 档案中心 | 账号画像、历史风险、状态、封禁、审核信息 |
| E 包：前端行为链路，后置 | 前端活跃、访问路径、行为序列、页面模块行为 |
| F 包：设备账号关联，后置 | 用户 ↔ 设备、设备风险、设备一致性、root / hook / 多开 / 模拟器 |
| DataAgent / Hive | 批量、跨天、历史聚合、离线指标、分母和 baseline |

## 证据

证据负责“把 raw data 变成可追溯、可比较、可合并的 evidence”。

证据层必须区分强证据、弱证据、反证、缺口和 blocker，避免把单一来源包装成最终结论。

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

典型边界：

- 天狮命中是 strategy evidence，不是最终作弊定性。
- 登录 token 成功可以是 nuance / counter evidence，但不是无风险证明。
- 档案中心历史封禁不能自动和今日事件合并为同一因果链。
- `no_data`、timeout、blocked、auth blocker 必须分别记录。

## 输出

输出负责“面向策略同学给出可读、可执行、不过度定性的结论”。

输出形态：

- `evidence_summary`
- `risk_assessment_summary`
- batch cluster summary
- `recommended_next_checks`
- strategy recommendation
- boundary notes
- case learning note
- run log / regression

输出要求：

- 先给结论，再给证据结构。
- 明确 supporting / counter / missing / blockers。
- 不用单源强证据给 definitive conclusion。
- 对策略建议标记 candidate / validation required，不自动上线。
- 对批量分析输出风险簇摘要、代表样本和补证计划，而不是逐个 case 堆叠。

## 安全防护层

安全不是最后一步，而是贯穿“大脑 → 手脚 → 证据 → 输出”的底座。

包含：

- capability registry。
- scene routing。
- contract。
- observation schema。
- smoke / regression。
- browser auth preflight。
- safety boundary。
- 敏感信息保护。
- 不自动处置。
- 不强判。
- 不越权。
- `no_data` 不当无风险。
- auth blocker 不当 `no_data`。

安全防护层要解决的是：Agent 能不能查、该不该查、怎么解释、哪些不能输出、什么时候必须降级、哪些结论不能下。

## 与四层架构的对应表

| 专家能力视角 | 四层架构对应 | 说明 |
|---|---|---|
| 大脑 | 意图识别与任务路由层 + 研判大脑 / 分析编排层 | 判断怎么想、查什么、怎么归因 |
| 手脚 | 证据取数 / 平台手脚层 | 查平台、取数据 |
| 证据 | observation schema + evidence summary | 标准化和合并证据 |
| 输出 | evidence summary / 风险簇摘要 / 策略建议 | 面向策略同学交付 |
| 安全防护 | 能力契约 / 安全治理层 | 贯穿全链路的护栏 |

## 推荐使用方式

- 工程对齐：先读 `computer_use_poc/dennis_agent_capability_architecture_v1.md`。
- 组内分享 / 复盘总结：先读本文。
- 具体能力索引：读 `computer_use_poc/capability_registry.md`。
- 路由细节：读 `computer_use_poc/scene_to_capability_routing.md`。
- 契约和边界：读各能力包 README、observation contract 和 smoke / regression。
