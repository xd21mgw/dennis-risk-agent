# 档案中心 Computer Use 只读执行 Playbook

本文是内部 Agent 执行档案中心只读查询时的运行时规范。它不是设计文档，也不是风险定性规则。

## 1. 当前能力范围

已支持：

- 档案中心 `userId` direct URL。
- saved state 复用。
- quick mode。
- focused_login_risk mode。
- P0 Tab deep-read。

不支持：

- 多平台。
- 多入参。
- 二级链接 validated。
- 批量查询。
- 自动风险定性。
- 处置、审批、导出、封禁、解封等任何写操作。

## 2. execution_mode 定义

### quick

用途：快速确认用户详情页是否可访问，以及用户信息 Tab 的基础结构。

读取：

- 用户信息 Tab。
- section 标题。
- 关键入口是否可见。
- 写操作按钮语义。

目标耗时：1-2 分钟。

### focused_login_risk

用途：账号安全、异常登录、ATO、协议上号、高危操作初筛。

读取：

- 用户信息 Tab。
- 用户分析 Tab。

用户分析要求：

- 必须记录实际页面 time_range。
- 必须先做 table_schema_probe。
- 如用于登录 / 高危操作研判，必须做 risk_event_scan。

目标耗时：3-5 分钟。

当前状态：

- structure extraction 已验证。
- risk_event_scan selector noise 已修复并 validated。
- 当前 validated 范围仅限档案中心 userId direct URL 的 focused_login_risk 只读派生观察，不代表自动风险定性。

### deep

用途：用户明确要求档案中心 P0 Tab 完整深读。

读取：

- 用户信息。
- 用户分析。
- 审核日志。
- 视频作品集。

目标耗时：5-7 分钟。

## 3. 用户分析 Tab 特殊规则

用户分析 Tab 不能默认按标准表格处理。

规则：

- 不要默认使用 `ant-table` 选择器。
- 档案中心用户分析表格可能使用 `ks-table__row`。
- 不要全页面直接 `querySelectorAll('.ks-table__row')`。
- 优先定位 active user_analysis tab container。
- 如果无法定位 active container，使用 row feature filter。
- 当前 active tab container 不可用时，row feature filter 是 validated fallback。
- selector noise 未修复时，`risk_event_scan.status` 只能写 `partial_validated_with_selector_noise`；row feature filter 修复成功后可写 `validated`。

## 4. row feature filter

只保留符合日志特征的行。

保留条件：

- 有时间格式。
- 有操作 URL path 或操作类型。
- 有操作结果。
- 有 APP 版本、IP 描述、设备字段之一。

排除条件：

- 平台操作。
- 直播功能。
- 电商功能。
- 行为封禁。
- 流量调控。
- 账户信息。
- 其他用户信息 Tab 中的非日志表格行。

## 5. table_schema_probe 与 risk_event_scan

### table_schema_probe

用途：字段结构探测。

规则：

- 只看表头 + 前 3 条样例结构。
- 字段值默认 redacted。
- 不用于风险判断。
- 不得基于 table_schema_probe 得出无风险、无异常或无行为结论。

### risk_event_scan

用途：登录 / 高危操作摘要。

必须输出：

- 操作类型分布。
- 成功失败分布。
- 登录方式序列。
- IP 一致性派生判断。
- 设备一致性派生判断。
- APP 版本一致性派生判断。
- 地理位置一致性派生判断。
- 第三方登录是否可见。
- 手机号 / 绑定事件是否可见。
- 关键事件序列。
- 可疑事件标记。
- 分页是否影响覆盖。
- coverage_limitations。

禁止：

- 输出 IP、设备 ID、手机号、open_id、token、请求参数、cookie、session、KIM code 等明文。
- 把 risk_event_scan observation 写成最终风险定性。

## 6. 敏感字段三层策略

### never_collect

不得读取、不得输出、不得沉淀：

- cookie。
- token。
- session。
- KIM code。
- password。
- access token / refresh token。
- 完整认证票据。

### runtime_readable_but_not_persisted

可在执行态用于风控派生判断，但不得明文沉淀：

- IP。
- 设备 ID / did / egid。
- 手机号。
- open_id。
- 第三方登录标识。
- APP 版本。
- 系统版本。
- 地理位置。
- 操作 URL path / result。

允许输出：

- redacted 标记。
- 计数。
- 分布。
- 一致性判断。
- 关键事件序列摘要。
- hash，如后续安全规范允许。

### persistable_structure

可沉淀：

- 字段名。
- 操作类型。
- 成功 / 失败。
- 时间范围。
- 表头。
- 分布。
- 计数。
- Tab / 模块名。

## 7. 统一 observation 输出

内部 Agent 必须输出以下结构：

```yaml
execution_mode:
actual_duration:
state_reuse_status:
tabs_observed:
selector_profile:
  table_structure:
  extraction_method:
  fallback_used:
  selector_noise:
    present:
    source:
    mitigation:
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
```

## 8. 禁止事项

禁止：

- 点击封禁、解封、打标、保存、提交、审批、导出、批量操作。
- 点击二级链接，除非后续专门验证。
- 输出操作者账号明文。
- 输出 token / cookie / session / KIM code。
- 输出 IP、设备 ID、手机号、open_id、请求参数等敏感明文。
- 把 observation 当成最终风险结论。
- 把 `partial_validated_with_selector_noise` 写成 `validated`。
- 把二级入口写成 validated。
- 把无结果解释为无风险。

## 9. focused_login_risk 标准 Prompt 模板

```text
请在档案中心执行 userId direct URL 只读查询，execution_mode=focused_login_risk。

输入：
- user_id: {user_id}
- target_url: {archives_center_userid_direct_url}

执行范围：
1. 使用已保存 state，直接打开 userId direct URL。
2. 如果 state 失效，停止并返回 state_reuse_status，不记录任何认证信息。
3. 只读取用户信息 Tab 和用户分析 Tab。
4. 用户分析 Tab 先做 table_schema_probe，再做 risk_event_scan。
5. 不要默认使用 ant-table 选择器；用户分析表格可能是 ks-table__row。
6. 不要全页面直接 querySelectorAll('.ks-table__row')。
7. 优先定位 active user_analysis tab container；如果失败，使用 row feature filter。
8. row feature filter 只保留有时间格式、操作 URL path 或操作类型、操作结果、APP 版本 / IP 描述 / 设备字段之一的日志行。
9. 排除平台操作、直播功能、电商功能、行为封禁、流量调控、账户信息等非日志表格行。

敏感字段策略：
- cookie、token、session、KIM code、password、access token、refresh token 永远 never_collect。
- IP、设备 ID、手机号、open_id、APP 版本、系统版本、地理位置、操作 URL path / result 可在执行态用于派生判断，但不得明文输出或沉淀。
- 只输出 redacted 标记、计数、分布、一致性判断、关键事件序列摘要。

输出 observation：
- execution_mode
- actual_duration
- state_reuse_status
- tabs_observed
- selector_profile
- risk_event_scan
- sensitive_runtime_evidence_policy
- readonly_safety_check

禁止：
- 不点击任何写操作按钮。
- 不点击二级链接。
- 不输出操作者身份明文。
- 不输出任何认证票据或敏感字段明文。
- 不输出最终风险定性。
- 如果 selector noise 仍存在，risk_event_scan.status 必须写 partial_validated_with_selector_noise，不能写 validated。
- 如果 row feature filter 已确认 selector_noise_present=false，可写 risk_event_scan.status=validated，但仍不得输出最终风险定性。
```
