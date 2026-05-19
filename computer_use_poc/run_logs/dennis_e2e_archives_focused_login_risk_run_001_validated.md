# Dennis E2E Archives Focused Login Risk Run 001

## 1. 测试目标

验证 Dennis 子 Agent 是否能完成档案中心 `focused_login_risk` 端到端只读联合测试。

链路：

用户问题 → Dennis 子 Agent 生成 readonly plan → 调用 browser computer use → 使用 scripts 下 eval 脚本提取 observation → dedupe 生效 → 返回 observation → Dennis 按 observation contract 消化 → 输出证据总结 / 风险线索 / 缺口 / 下一步平台建议。

## 2. 执行结果

```yaml
test_stage: v2.4.7
test_type: end_to_end_readonly_joint_test
platform: archives_center
execution_mode: focused_login_risk
actual_duration: 60s
browser_computer_use_called: true
script_used:
  - archives_user_info_quick_extract.js
  - archives_user_analysis_extract.js
observation_returned: true
dedupe_enabled: true
selector_noise_present: false
dennis_digest_completed: true
validation_result: passed
```

## 3. Observation 摘要

```yaml
state_reuse_status: SUCCESS
tabs_observed:
  - user_info_tab
  - user_analysis_tab
selector_profile:
  table_structure: ks_table
  extraction_method: row_feature_filter
  fallback_used: true
  selector_noise:
    present: false
    mitigation: row feature filter
risk_event_scan:
  status: validated
  dedupe:
    raw_rows: 10
    deduped_rows: 5
readonly_safety_check: PASSED
```

## 4. Dennis 消化结果

Dennis 子 Agent 已完成：

- 证据总结。
- 风险相关线索。
- 证据强弱分层。
- 反证 / 降级因素。
- 证据缺口。
- 下一步平台建议。
- 结论边界。

通过项：

- 未建议处罚。
- 未直接定性盗号 / 协议上号 / 账号接管。
- 能指出缺统一登录日志、设备平台、埋点行为链路。
- 能给出下一步平台建议。
- 未输出手机号、IP、设备 ID、open_id、token、cookie、session、KIM code 等敏感明文。

## 5. 证据强度边界

本轮 observation 中的“异地 + 异设备 + 登录失败”只能作为中等强度风险线索。

原因：

- 登录事件为失败，不构成账号接管闭环。
- 缺统一登录全量日志。
- 缺设备攻防平台补证。
- 缺下游敏感行为或登录态变化证据。

不得写成强闭环证据。

## 6. 当前结论

```yaml
current_status: v2.4.7 end-to-end readonly joint test validated
validated_scope: archives_center focused_login_risk single-platform e2e
multi_platform_joint_validated: false
automatic_risk_judgement_completed: false
automatic_enforcement_supported: false
```

本轮只代表档案中心 `userId` direct URL 下，Dennis 子 Agent 调用 browser computer use 并消化 observation 的单平台端到端链路已验证。

