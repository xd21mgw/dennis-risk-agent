# Security Preflight Tool Call Request Contract

## 1. 目标

统一真实 capability 在调用 preflight evaluator 前必须构造的 `tool_call_request`。

目标：

- 降低字段缺失、字段命名不一致、scope 表达不一致导致的 `evaluator_error_like_issue`。
- 让每个 capability 在进入 evaluator 前有稳定输入。
- 明确模型只能提交 request，不能自己决定 `allow` / `deny` / `require_approval`。
- 为后续 shadow hook 接内部 Agent runtime 做输入契约准备。

非目标：

- 不接真实 runtime。
- 不接真实内部平台。
- 不调用真实 API。
- 不读取认证态。
- 不进入 enforce mode。

## 2. 标准字段定义

| 字段 | 类型 | 必填 | 示例 | 缺失时默认处理 | 安全含义 |
|---|---|---|---|---|---|
| `request_id` | string | 是 | `req_20260521_001` | 生成临时 id，并记录 `field_missing_warning` | 审计和回放主键 |
| `operator` | string | 是 | `dennis_cloud_agent` | `unknown_operator` + warning | 标识执行主体，不作为授权来源 |
| `user_input_summary` | string | 是 | `查询单用户登录异常摘要` | 空摘要 + warning | 只记录摘要，不记录敏感原文 |
| `normalized_intent` | string | 是 | `login_log_check` | `unknown_intent` + warning | 支持路由复核 |
| `scene` | string | 是 | `login_investigation` | `unknown_scene` + warning | 支持能力选择和审计分类 |
| `capability_name` | string | 是 | `login_log_read` | deny | 必须来自 policy / registry |
| `input_entities` | list<object> | 视场景必填 | `[{entity_type: user_id, ...}]` | require clarification 或 deny | 限定查询对象，防止泛化扩散 |
| `input_entity_count` | integer | 是 | `1` | 由 `input_entities` 计算；无法计算则 warning | 判断是否超默认范围 |
| `requested_fields` | list<string> | 是 | `login_summary,event_type_counts` | 只允许 safe summary | 字段级 deny / redact 判断 |
| `requested_scope` | string | 是 | `single_entity` | `unknown` => require_approval 或 deny | 范围级 allow / approval / deny 判断 |
| `requested_time_range` | string | 是 | `recent_7d` | `unknown_time_range` + warning | 识别超窗、长窗口、批量风险 |
| `direct_tool_requested_by_user` | boolean | 是 | `false` | 默认 `false` 但记录 warning | 标记用户是否试图直接指定底层工具 |
| `attempts_to_override_policy` | boolean | 是 | `false` | 默认 `false` 但记录 warning | 标记 prompt injection / 绕过规则 |
| `requested_raw_output` | boolean | 是 | `false` | 默认 `false` 但记录 warning | 标记 source response summary / full JSON 风险 |
| `source_agent` | string | 是 | `dennis_main_agent` | `unknown_source_agent` + warning | 标识 request 来源 |
| `runtime_mode` | string | 是 | `shadow_mode` | `unknown` => require_approval | 区分 dry_run / shadow / enforce |

## 3. requested_scope 标准枚举

| scope | 含义 | 默认处理 |
|---|---|---|
| `single_entity` | 单个用户、设备、request 或 source 的只读查询 | 可 allow，仍需字段检查 |
| `small_scope` | 小范围、明确边界的只读补证 | 可 allow 或 require_approval，取决于 capability |
| `multi_entity` | 多实体但非大批量查询 | require_approval |
| `batch` | 批量查询 | require_approval |
| `expansion` | 关联扩散，如用户到设备、设备到用户、多跳关系 | require_approval |
| `cross_platform` | 多平台串联读取 | require_approval |
| `system_modification` | 修改 Agent、规则、release、skill、routing | deny |
| `unknown` | 范围缺失或无法归类 | require_approval 或 deny |

原则：

- `single_entity` 不代表自动 allow，仍需检查字段、capability 和 prompt injection。
- `batch` / `expansion` / `cross_platform` 默认需要审批。
- `system_modification` 直接 deny。
- `unknown` 不可静默放行。

## 4. capability_name 标准化

`capability_name` 必须来自 `security_preflight_policy.yaml`。

未知 capability 一律：

- `decision=deny`
- `policy_flags=["unknown_capability"]`
- 记录 `unknown_capability_event`

禁止使用底层平台名直接作为 capability：

- `weapon_graphData_raw`
- `archives_any_url`
- `tianshi_free_query`
- `browser_execute_js`
- `api_any_url`

除非这些名称已经被登记为具体 capability，并且有明确输入、scope、字段和脱敏策略。

## 5. input_entities 标准结构

```yaml
input_entities:
  - entity_type: user_id / device_id / request_id / phone / ip / unknown
    entity_value:
    is_sensitive:
    source:
    confidence:
```

字段说明：

- `entity_type`：实体类型。
- `entity_value`：脱敏或原始受控值。审计输出中应优先引用化或脱敏。
- `is_sensitive`：手机号、IP、设备指纹等应标记为 true。
- `source`：user_input / prior_observation / entity_resolution / internal_agent。
- `confidence`：high / medium / low。

边界：

- 手机号 / IP 等敏感实体不能默认原文输出。
- 候选关联实体只能作为候选关系，不等于风险结论。
- `input_entities` 缺失时，不得伪造实体。

## 6. requested_fields 标准化

字段分类：

### safe_summary_fields

可在只读摘要中使用：

- `risk_summary`
- `account_status`
- `login_summary`
- `event_type_counts`
- `strategy_hit_summary`
- `device_risk_summary`
- `candidate_devices`
- `related_users_summary`
- `frontend_activity_summary`

### sensitive_fields

默认 `redaction_required` 或按 capability deny：

- `phone`
- `mobile`
- `ip`
- `device_id`
- `did`
- `user_agent`
- `device_fingerprint`
- `requestParam`
- `extraParam`

### prohibited_fields

永远禁止输出：

- `cookie`
- `token`
- `session`
- `authorization`
- `header`
- `browser_storage_state_marker`
- `system_prompt`
- `routing_prompt`
- `skill_prompt`

### raw_internal_fields

默认 deny：

- `raw_response`
- `source_result`
- `safe_json_summary`
- `raw_log_content`
- `raw_graph_payload`
- `arbitrary_url`
- `arbitrary_js`
- `raw_sql`
- `shell_command`

## 7. 各 capability 映射样例

### user_profile_read

```yaml
tool_call_request:
  capability_name: user_profile_read
  input_entities:
    - entity_type: user_id
      entity_value: user_123
      is_sensitive: true
      source: user_input
      confidence: high
  input_entity_count: 1
  requested_fields: [risk_summary, account_status]
  requested_scope: single_entity
```

### login_log_read

```yaml
tool_call_request:
  capability_name: login_log_read
  input_entities:
    - entity_type: user_id
      entity_value: user_123
      is_sensitive: true
      source: user_input
      confidence: high
  input_entity_count: 1
  requested_fields: [login_summary, event_type_counts]
  requested_scope: single_entity
  requested_time_range: recent_7d
```

### user_to_device_resolution

```yaml
tool_call_request:
  capability_name: user_to_device_resolution
  input_entities:
    - entity_type: user_id
      entity_value: user_123
      is_sensitive: true
      source: user_input
      confidence: high
  input_entity_count: 1
  requested_fields: [candidate_devices]
  requested_scope: single_entity
```

### device_to_user_resolution

```yaml
tool_call_request:
  capability_name: device_to_user_resolution
  input_entities:
    - entity_type: device_id
      entity_value: device_abc
      is_sensitive: true
      source: user_input
      confidence: high
  input_entity_count: 1
  requested_fields: [related_users_summary]
  requested_scope: single_entity
```

### device_risk_read

```yaml
tool_call_request:
  capability_name: device_risk_read
  input_entities:
    - entity_type: device_id
      entity_value: device_abc
      is_sensitive: true
      source: user_input
      confidence: high
  input_entity_count: 1
  requested_fields: [device_risk_summary]
  requested_scope: single_entity
```

### strategy_hit_read

```yaml
tool_call_request:
  capability_name: strategy_hit_read
  input_entities:
    - entity_type: request_id
      entity_value: request_xxx
      is_sensitive: false
      source: user_input
      confidence: high
  input_entity_count: 1
  requested_fields: [strategy_hit_summary]
  requested_scope: single_entity
  requested_time_range: bounded_window
```

### frontend_activity_read

```yaml
tool_call_request:
  capability_name: frontend_activity_read
  input_entities:
    - entity_type: user_id
      entity_value: user_123
      is_sensitive: true
      source: user_input
      confidence: high
  input_entity_count: 1
  requested_fields: [frontend_activity_summary]
  requested_scope: single_entity
```

### api_direct_read

```yaml
tool_call_request:
  capability_name: api_direct_read
  input_entities:
    - entity_type: user_id
      entity_value: user_123
      is_sensitive: true
      source: user_input
      confidence: high
  input_entity_count: 1
  requested_fields: [risk_summary]
  requested_scope: single_entity
```

说明：

- `api_direct_read` 必须绑定已登记 endpoint / payload shape。
- 不允许 `arbitrary_url`、`arbitrary_api`、`raw_header`、`safe_json_summary`。

### browser_dom_read

```yaml
tool_call_request:
  capability_name: browser_dom_read
  input_entities:
    - entity_type: user_id
      entity_value: user_123
      is_sensitive: true
      source: user_input
      confidence: high
  input_entity_count: 1
  requested_fields: [risk_summary]
  requested_scope: single_entity
```

说明：

- `browser_dom_read` 必须绑定已登记页面模块和 scoped selector。
- 不允许 `arbitrary_js`、`localStorage`、`cookie`、`browser_storage_state_marker`。

## 8. 缺失字段处理策略

| 缺失 / 错误 | 默认处理 |
|---|---|
| 缺 `request_id` | 生成临时 id，但记录 `field_missing_warning` |
| 缺 `capability_name` | deny |
| 缺 `requested_scope` | `unknown` => require_approval 或 deny |
| 缺 `requested_fields` | 只允许 safe summary |
| 缺 `input_entities` | 根据场景 require clarification 或 deny |
| `input_entities` 类型错误 | fail closed |
| `requested_fields` 类型错误 | fail closed |
| `runtime_mode` 缺失 | `unknown` => require_approval |
| 字段类型错误 | fail closed |

原则：

- 缺字段不能静默 allow。
- 缺实体不能伪造实体。
- 字段类型错误应进入 `evaluator_error_like_issue`。
- 进入 enforce mode 前，缺字段样例必须被 dry-run / shadow 测试覆盖。

## 9. 与 shadow metrics 的关系

- contract 是 runtime 接入前的输入规范。
- aggregator 是接入后的观测汇总。
- contract 质量越高，`evaluator_error_like_issue` 越少。
- 如果 runtime 生成的 request 不符合 contract，应优先修 request 构造层，而不是放宽 evaluator。
- shadow metrics 中 `evaluator_error_count` 和 `evaluator_error_like_issue_count` 是 contract 质量的直接反馈。

## 10. 当前边界

- 本文档只定义字段契约。
- 不改 `security_preflight_evaluator.py` 运行逻辑。
- 不接真实 runtime。
- 不接真实内部平台。
- 不进入 enforce mode。
