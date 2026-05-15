# ATO Batch Sampling Strategy v1

## 1. 目标

面对上百个 ATO / 盗号申诉 case，抽样目标不是只找正例，而是覆盖手法、边界、反例、状态异常和人工备注偏差，提升 Dennis Agent 的抗过拟合能力。

## 2. 抽样维度

按以下维度分层：

- 风险类型：密码泄露、钓鱼、扫码/OAuth、短信泄露、token/session、未知。
- 人工标签：是、否、不确定。
- Data Agent 状态：execution_result_ready、sql_only、partial、no_permission、failed、empty_result。
- 结论支持：data_supports_ato_suspicion、partial_support、insufficient_support、data_does_not_support_ato。
- 链路类型：登录后发布、授权后 Web 新设备、token/session 异常、找回 / 改密 / 换绑、只有发布无登录。
- 情报一致性：人工备注与数据一致、部分一致、冲突、无法验证。
- 权限缺口：无缺口、内容字段缺失、策略 params 缺失、实时链路缺失。

## 3. 第一批 100 case 建议配比

| 类型 | 占比 | 目标 |
|---|---:|---|
| 清晰正例 | 25% | 覆盖密码、扫码/OAuth、短信、钓鱼、token/session |
| 证据不足 / 反例 | 25% | 验证不因申诉、发布、地区不一致强判 |
| 局部支持 / 链路不闭合 | 20% | 验证 partial_support 边界 |
| 权限 / SQL 状态边界 | 15% | 覆盖 sql_only、no_permission、empty_result、failed |
| 人工备注冲突样本 | 10% | 纠正“已回扫 / 地推 / 来源域名”等未验证线索 |
| 新手法 / 低频类型 | 5% | 保留探索空间 |

## 4. 周期抽样建议

每周抽 20 个：

- 5 个清晰正例。
- 5 个证据不足 / 反例。
- 4 个局部支持。
- 3 个权限或 SQL 状态边界。
- 2 个人工备注冲突。
- 1 个新手法或异常样本。

## 5. 优先进入真实取证的样本

优先：
- user_id 和 time_window 齐备。
- 用户描述与人工备注指向明确手法。
- 与历史固定回归类型不同。
- 人工备注和数据可能冲突。
- 涉及新设备、OAuth、扫码、token/session、发布链路。

暂缓：
- 缺 user_id。
- 无可推导 time_window。
- 重复 case。
- 只有用户申诉、无任何异常时间或动作。
- 触及暂不支持的数据域且无法脱敏。

## 6. Seed Anchor

长期保留以下 3 个种子样本作为抽样锚点：

| case_id | 类型 | 价值 |
|---|---|---|
| ATO_CASE_001_PASSWORD_KPN_RESWEEP | 密码登录型正例 | 验证密码登录 + 新设备 + 风控命中 + 发布链路 |
| ATO_CASE_003_QR_SCAN_GROUND_PROMO_RESWEEP | 扫码/OAuth 型正例 | 验证 OAuth/扫码 + Web 新设备 + token + 发布链路 |
| ATO_CASE_006_UNCERTAIN_NO_CLEAR_EVIDENCE | 反例 / 证据不足 | 验证不因申诉、发布、地区不一致强判 |

## 7. 抽样质量检查

每轮抽样后检查：

- 是否至少包含 1 个反例。
- 是否至少包含 1 个权限或状态边界样本。
- 是否覆盖至少 3 种风险子类。
- 是否保留人工备注冲突样本。
- 是否避免全是同类正例导致过拟合。
