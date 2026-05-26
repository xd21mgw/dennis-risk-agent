# Tianshi Policy Attribution API-read POC v1

## 1. 能力定位

本 POC 定位为“单事件策略归因 API-read”能力，用于解释一个具体 `eventId` 下，指定 `policyCode` / `policyVersion` 在该事件中的条件级命中情况。

当前状态是 `partial_success`，不是完整策略树闭环：

- 已能读取事件详情、策略版本列表和条件级归因。
- 已能支持轻量策略归因证据：说明某策略在某次事件中哪些条件为 true / false。
- 尚不能支持完整策略树节点绑定归因，因为缺少 `policyTreeNodeCode`。
- 不自动处置，不做最终作弊定性。

## 2. 验证输入

```yaml
eventType: USER_REGISTER_NEW
eventId: "5370247893355116990"
event_time: "2026-05-26 13:48:47 Asia/Shanghai"
policyTreeCode: USER_REGISTER_NEW
policyTreeVersion: 887
policyCode: BS_fake_account_register_thirdPlatformAll_bindphone
policyVersion: 5
queryTime_rule: use event occurrence timestamp in milliseconds
```

`queryTime` 必须使用事件发生时间的毫秒时间戳，不能使用错误年份或当前时间替代。

## 3. 已验证 API

| API | Method | Status | Purpose |
| --- | --- | --- | --- |
| `/v2/rest/event/rcpEventDetail` | GET | success | 读取事件详情、实时反馈、错误码、生效策略、命中策略 |
| `/v2/rest/pc/policy/getPolicyVersionListByEvent` | GET | success | 根据 event / policy context 获取策略版本 |
| `/v2/rest/pc/policy/nodePolicyAttribution` | POST | success | 获取指定 policyCode / policyVersion 在该事件中的条件级归因 |

关键观察：

- `rcpEventDetail` 可返回实时反馈为阻止、错误码 `217009`、生效策略 `BS_fake_account_register_thirdPlatformAll_bindphone#5`。
- 命中策略包含 `BS_Register_nosense_captcha_all#5` 和 `BS_fake_account_register_thirdPlatformAll_bindphone#5`。
- `nodePolicyAttribution` 返回条件级归因，本次 4 个条件全部为 true。

## 4. Partial / Blocked API

| API | Method | Status | Blocker / Boundary |
| --- | --- | --- | --- |
| `/v2/rest/event/rcpEventFeatureList` | GET | partial | 返回空 data，标记 `feature_snapshot_empty_or_unavailable` |
| `/v2/rest/pc/policy/nodeBindPolicyAttribution` | GET | blocked | 缺少 `policyTreeNodeCode` |
| policyTree API | GET / POST | blocked | HTTP 直连 403；可能需要 browser 二次认证或额外权限 |

边界：

- `feature_snapshot_empty_or_unavailable` 不代表无特征、无风险或策略无依据。
- `nodeBindPolicyAttribution` blocked 不影响轻量条件归因，但影响完整节点级归因。
- policyTree API blocked 是权限 / 认证 / 参数缺口，不得解释为 no_data。

## 5. 输入字段

| field | type | required | notes |
| --- | --- | --- | --- |
| `eventType` | string | yes | 事件类型，例如 `USER_REGISTER_NEW` |
| `eventId` | string | yes | 单事件 ID |
| `queryTime` | integer ms timestamp | yes | 使用事件发生时间毫秒戳 |
| `region` | string | optional | 视接口参数要求填写 |
| `policyCode` | string | yes | 目标策略 code |
| `policyVersion` | integer | yes | 目标策略版本 |
| `isPolicyTreeExperiment` | boolean | optional | 视策略归因 API 参数要求填写 |

## 6. Observation Schema 草案

```yaml
policy_attribution_observation:
  event_context:
    event_type:
    event_id:
    query_time_ms:
    real_time_feedback:
    error_code:
    side_effect_ops:
    effective_policy:
    hit_policies:
  policy_context:
    policy_code:
    policy_version:
    version_found:
  condition_attribution:
    attribution_status:
    condition_count:
    true_condition_count:
    false_condition_count:
    sample_conditions:
      - condition_expression_summary:
        attribution_result:
        evidence_type: policy_condition_attribution
  feature_snapshot:
    status:
    feature_count:
    blocker:
  node_binding_attribution:
    status:
    blocker:
    missing_required_params:
  evidence_strength:
  blockers:
  limitations:
```

## 7. 证据边界

- 策略归因能解释条件 true / false。
- 策略归因不等于最终作弊定性。
- 条件表达式可以展示为摘要，但特征业务含义需要特征字典或人工解释。
- `feature list` 空不代表无特征、无风险或策略无依据。
- `nodeBindPolicyAttribution` blocked 不影响轻量条件归因，但影响完整节点级归因。
- `updateUser` 只能作为追溯字段，不做责任归因。
- `auth blocker` / `permission blocker` 不得解释为 no_data。
- 策略返回阻止 / 验证是策略动作证据，不代表自动处置结论或最终治理建议。

## 8. 下一步缺口

| Gap | Why it matters | Next step |
| --- | --- | --- |
| 稳定获取 `policyTreeNodeCode` | `nodeBindPolicyAttribution` 需要该参数 | 从策略树详情、页面上下文或其他接口验证参数来源 |
| 策略树详情 API 403 | 阻塞完整策略树理解 | 验证 browser 二次认证或额外权限路径 |
| `nodeBindPolicyAttribution` 成功样例 | 需要闭环节点级绑定归因 | 补一个带 `policyTreeNodeCode` 的 readonly 样例 |
| 特征字段业务含义 | 条件表达式需要解释能力 | 关联特征字典或人工策略说明 |
| 完整策略树理解 | 当前只是轻量条件归因 | 先补齐节点绑定，再决定是否进入完整策略树理解能力 |

## 9. 当前结论

当前可以沉淀为：

`tianshi_single_event_policy_condition_attribution_api_read_partial_success`

适合回答：

- “这个 eventId 为什么命中了这个策略？”
- “这个 policyCode 在这次事件里哪些条件为 true？”
- “策略归因证据能支持到什么程度？”

不适合回答：

- “完整策略树路径是什么？”
- “该策略是否应该上线 / 下线？”
- “这个用户是否最终作弊？”
- “哪个策略开发者应负责？”
