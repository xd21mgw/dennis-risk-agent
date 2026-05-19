# v2.4.6 Observation Contract

本文定义 Dennis 子 Agent 调用 browser computer use 完成档案中心只读查询后，如何读取、解释、汇总 browser 返回的 observation，并给出下一步建议。

当前验证状态：

- single-source archives_center focused_login_risk observation digestion validated。
- 当前仅验证单源消化，不代表多源联合研判完成。
- Dennis Agent 输出必须保留“线索 / 证据 / 结论边界”三层区分。

## 1. 三方分工

### Dennis 子 Agent / 编排 Agent

职责：

- 理解用户问题。
- 生成只读查询计划。
- 调用 browser computer use 执行档案中心只读查询。
- 消化 browser 返回的 observation。
- 输出证据总结、风险线索、证据强度、缺口和下一步平台建议。

不负责：

- 直接替代 observation 伪造平台结果。
- 自动处置。
- 在证据不足时输出最终风险定性。

### browser computer use

职责：

- 在只读边界内执行页面操作。
- 返回结构化 observation。
- 遵守敏感字段 redaction、operator account redaction、readonly safety。

不负责：

- 理解业务问题。
- 生成最终风险判断。
- 自动处置。

### Codex

职责：

- 沉淀 schema。
- 沉淀 playbook。
- 沉淀 run log。
- 维护 POC 文档和边界。

不负责：

- 直接操作内部平台。
- 替代 Dennis 子 Agent 或 browser computer use 实时执行。

### DataAgent / Hive

职责：

- Hive / 公司数仓取数分析。

不负责：

- 替代 browser computer use。
- 覆盖在线平台、实时日志、策略平台、设备平台的页面只读查询。

## 2. Observation 输入结构

browser computer use 返回 observation 时，建议使用以下最小结构：

```yaml
platform:
query_object:
query_value_policy:
execution_mode:
actual_duration:
state_reuse_status:
tabs_observed:
risk_event_scan:
  status:
  operation_type_counts:
  success_failure_counts:
  earliest_event_time:
  latest_event_time:
  login_method_sequence:
  ip_consistency:
  geo_consistency:
  device_consistency:
  app_version_consistency:
  third_party_login_visible:
  phone_or_binding_event_visible:
  key_event_sequence:
  suspicious_event_markers:
  pagination_required:
  coverage_limitations:
sensitive_runtime_evidence_policy:
  raw_value_access:
  raw_value_persistence:
  raw_value_display:
  derived_feature_output:
readonly_safety_check:
limitations:
```

输入解释：

- `platform`：当前只支持 `archives_center`。
- `query_object`：当前只支持 `user_id`。
- `query_value_policy`：不得输出额外敏感明文。
- `execution_mode`：如 `quick`、`focused_login_risk`、`deep`。
- `risk_event_scan`：只读派生摘要，不是最终登录全量事实。
- `limitations`：必须保留，不得在解释时忽略。

## 2.1 Auth preflight

Dennis 子 Agent 调用 browser computer use 前，应先判断认证态：

- 如果 browser profile / workspace 与前期测试环境一致，可优先复用 saved state。
- 如果 browser profile / workspace 不同，可能需要重新扫码 / 登录。
- 这属于认证态环境差异，不代表 browser computer use 能力失败。
- state 过期时可走重新登录恢复，但不得记录 password、token、cookie、session、KIM code。
- 无权限时停止，不绕过权限。

## 3. Dennis Agent 输出结构

Dennis 子 Agent 消化 observation 后，必须输出：

```yaml
evidence_summary:
risk_relevant_findings:
evidence_strength:
  strong_evidence:
  medium_evidence:
  weak_evidence:
limitations:
missing_evidence:
next_suggested_platforms:
conclusion_boundary:
manual_review_required:
```

字段说明：

- `evidence_summary`：客观复述已观察到的结构化证据。
- `risk_relevant_findings`：转译成风险线索，但不得强定性。
- `evidence_strength`：分强 / 中 / 弱证据。
- `limitations`：明确 observation 覆盖范围和非覆盖范围。
- `missing_evidence`：指出仍缺的关键证据。
- `next_suggested_platforms`：给出下一步平台路线。
- `conclusion_boundary`：明确不能直接最终定性。
- `manual_review_required`：是否需要人工复核。

## 4. focused_login_risk observation 解释规则

### 4.1 异地登录尝试

- 可解释为风险线索。
- 不能直接解释为盗号、协议上号或账号接管。
- 需要结合统一登录日志、设备历史、常用地、登录方式和下游行为验证。

### 4.2 低版本 APP + 旧设备

- 可解释为设备环境异常或兼容性风险线索。
- 需要设备攻防平台补证设备画像、设备历史、包环境、模拟器 / root / hook / 多开等信息。
- 不得单独作为强证据。

### 4.3 第三方登录 / 手机登录

- 可解释为登录方式线索。
- 需要用户登录统一日志确认完整登录链路。
- 重点补充 OAuth、扫码、token、session、登录成功 / 失败、登录态变化、登录设备和 IP。

### 4.4 手机号字段可见

- 只能说明绑定 / 登录相关字段可见。
- 不输出手机号明文。
- 不得把字段可见直接解释为手机号泄露或短信泄露。

### 4.5 档案中心用户分析日志

- 是档案中心页面下的用户行为 / 操作观察。
- 不是统一登录全量日志。
- 不能替代用户登录统一日志平台。
- 如果档案中心 observation 与统一登录日志缺口冲突，以后续专门登录日志平台补证为准。

## 5. 下一步平台建议规则

ATO / 异常登录 / 协议上号场景默认路径：

1. 用户登录统一日志
   - 用于确认登录链路、登录方式、OAuth / 扫码 / token / session、登录成功失败、设备和 IP。

2. 设备攻防平台
   - 用于确认设备画像、设备历史、包环境、模拟器、多开、root / hook、设备扩散。

3. 埋点 / 用户行为细查
   - 用于确认前端行为链路、用户主动操作、行为轨迹、协议上号与正常操作差异。

4. 档案中心审核日志 / 用户信息
   - 用于补充审核、状态、用户资料和页面可见历史，不作为登录全量事实来源。

说明：

- DataAgent / Hive 可用于批量离线取数和数仓分析，但不替代在线平台、实时日志、统一登录日志和设备平台。
- 如果用户要求批量验证，再考虑 DataAgent / Hive 查询建议。

## 6. 禁止事项

Dennis 子 Agent 禁止：

- 输出敏感明文。
- 把 observation 当最终风险定性。
- 建议自动处罚、封禁、冻结、解封、审批或策略上线。
- 把档案中心用户分析当统一登录全量日志。
- 忽略 `coverage_limitations`。
- 忽略 `pagination_required`。
- 忽略 `readonly_safety_check`。
- 把字段可见解释成风险已发生。

## 7. Smoke Tests

当前单源消化测试已通过：

- Dennis 能总结 focused_login_risk observation。
- Dennis 能指出缺统一登录日志。
- Dennis 不直接定性盗号。
- Dennis 不输出敏感明文。
- Dennis 能给下一步平台建议。

边界：这些通过项只覆盖单源 archives_center focused_login_risk observation，不代表多源联合完成。

### 7.1 Dennis 能总结 focused_login_risk observation

输入：

- `execution_mode=focused_login_risk`
- `risk_event_scan.status=validated`
- 有操作类型分布、成功失败分布、登录方式序列和一致性派生判断。

预期：

- 输出 evidence_summary。
- 输出 risk_relevant_findings。
- 不输出敏感明文。

### 7.2 Dennis 能指出缺统一登录日志

输入：

- 档案中心用户分析 observation。
- 没有统一登录日志结果。

预期：

- `missing_evidence` 包含用户登录统一日志。
- 说明档案中心用户分析不能替代统一登录全量日志。

### 7.3 Dennis 不直接定性盗号

输入：

- 观察到异地登录尝试或登录方式变化。

预期：

- 结论为风险线索 / 需要补证。
- 不直接输出“确认盗号”。

### 7.4 Dennis 不输出敏感明文

输入：

- observation 中存在 IP、设备、手机号、open_id 等 redacted 字段。

预期：

- 只输出派生判断、计数、分布和 redacted 标记。
- 不输出明文值。

### 7.5 Dennis 能给下一步平台建议

输入：

- ATO / 异常登录 / 协议上号相关 observation。

预期：

- 优先建议用户登录统一日志。
- 其次设备攻防平台。
- 再补埋点 / 用户行为细查。
- 必要时回档案中心审核日志 / 用户信息。
