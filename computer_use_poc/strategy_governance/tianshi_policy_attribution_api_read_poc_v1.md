# Tianshi Policy Attribution API-read POC v1

## 1. 能力定位

本 POC 定位为“单事件策略归因 API-read”能力，用于解释一个具体 `eventId` 下，指定 `policyCode` / `policyVersion` 在该事件中的条件级命中情况，并通过策略树节点解析补齐节点级绑定归因。

当前状态：`full_p0_e2e_success`。

已验证能力：

- 事件详情读取。
- 事件特征快照读取。
- 策略版本列表读取。
- 策略树节点解析。
- 条件级策略归因。
- 节点级绑定策略归因。

边界：

- 这是单事件策略归因闭环，不是策略上线 / 下线评估系统。
- 策略归因不等于最终作弊定性。
- 不自动处置，不输出处罚建议。
- `updateUser` 只能作为追溯字段，不做责任归因。
- rcp 策略归因相关 REST API 本轮可通过 HTTP + SSO 直接调用，但该结论只适用于本次已验证的策略归因 API，不得泛化到所有 RCP 接口。

## 2. 验证输入

```yaml
eventType: USER_REGISTER_NEW
eventId: "5370247893355116990"
event_time: "2026-05-26 13:48:47 Asia/Shanghai"
queryTime: 1779774526479
policyTreeCode: USER_REGISTER_NEW
policyTreeVersion: 887
policyCode: BS_fake_account_register_thirdPlatformAll_bindphone
policyVersion: 5
resolved_policyTreeNodeCode: "53187346034508"
node_name: 主站三方注册强绑手机号
```

`queryTime` 必须使用事件详情中的精确 `_occurTime`，不能使用错误年份、粗略事件时间或当前时间替代。

## 3. 完整 6 步 API 链路

| Step | API | Method | Status | Purpose |
| --- | --- | --- | --- | --- |
| 1 | `/v2/rest/event/rcpEventDetail` | GET | success | 读取事件详情、实时反馈、错误码、生效策略、命中策略、精确 `_occurTime` |
| 2 | `/v2/rest/event/rcpEventFeatureList` | GET | success | 读取事件特征快照，当前返回 519 条特征 |
| 3 | `/v2/rest/pc/policy/getPolicyVersionListByEvent` | GET | success | 根据 event / policy context 获取策略版本 |
| 4 | `/v2/rest/pro/policyTree/queryProPolicyTree` | GET | success | 递归解析策略树，定位 `policyTreeNodeCode` |
| 5 | `/v2/rest/pc/policy/nodePolicyAttribution` | POST | success | 获取指定 policyCode / policyVersion 在该事件中的条件级归因 |
| 6 | `/v2/rest/pc/policy/nodeBindPolicyAttribution` | GET | success | 获取策略树节点绑定策略归因 |

## 4. API Contract Notes

### 4.1 rcpEventDetail

Purpose:

- 获取事件详情。
- 获取精确 `_occurTime`，作为后续 `queryTime`。
- 获取实时反馈、错误码、生效策略、命中策略。

Key input:

- `eventType`
- `eventId`
- `queryTime` if required by endpoint wrapper

Key returned fields:

- `_occurTime`
- `realTimeFeedback`
- `errorCode`
- `sideEffectOps`
- `effectivePolicy`
- `hitPolicies`

Observed:

- real-time feedback: 阻止
- error code: `217009`
- effective policy: `BS_fake_account_register_thirdPlatformAll_bindphone#5`
- hit policies include:
  - `BS_Register_nosense_captcha_all#5`
  - `BS_fake_account_register_thirdPlatformAll_bindphone#5`

Boundary:

- 实时反馈 / 错误码 / 命中策略是策略证据，不是最终作弊定性。

### 4.2 rcpEventFeatureList

Purpose:

- 获取事件特征快照。

Key input:

- `eventType`
- `eventId`
- `queryTime=1779774526479`
- `featureGroup=""`

Critical fix:

- `featureGroup` 应先传空字符串，不要传“主站特征 / 原始类 / 行为类”等中文分类名。
- `queryTime` 使用事件详情中的精确 `_occurTime`。

Observed:

- feature_count: 519
- feature groups include: `DERIVE`, `ORIG`, `COUNTER`, `SYS`, `DATASERV`, `OTHER`

Boundary:

- 不输出完整特征值原文。
- 输出字段名、分组分布、计数、少量脱敏 sample keys。
- feature list 空时才标记 `feature_snapshot_empty_or_unavailable`，但本轮已修复为 success。

### 4.3 getPolicyVersionListByEvent

Purpose:

- 获取事件关联策略版本上下文。

Key input:

- `eventType`
- `eventId`
- `policyCode`
- `policyVersion`
- `queryTime`

Key returned fields:

- `policyCode`
- `policyVersion`
- `versionFound`
- version metadata

Observed:

- policyCode: `BS_fake_account_register_thirdPlatformAll_bindphone`
- policyVersion: `5`
- version_found: true

Boundary:

- 策略版本存在只说明可归因，不说明策略一定合理或应上线。

### 4.4 queryProPolicyTree

Correct API:

`GET /v2/rest/pro/policyTree/queryProPolicyTree`

Incorrect API to avoid:

`/v2/rest/pc/policytree/getPolicyTreeByVersion`

Purpose:

- 读取策略树并递归定位策略树节点。
- 获取 `policyTreeNodeCode`。

Key input:

- `policyTreeCode=USER_REGISTER_NEW`
- `policyTreeVersion=887`
- query context as required by wrapper

Observed:

- node_name: `主站三方注册强绑手机号`
- resolved_policyTreeNodeCode: `53187346034508`
- node_code_source: recursive policy tree parse

Critical fix:

- `policyTreeNodeCode` 必须通过 `queryProPolicyTree` 解析。
- 不要用 `serial`、`policyCode` 或节点名称猜测。

Boundary:

- 策略树结构只用于定位节点和解释上下文，不等于策略治理建议。

### 4.5 nodePolicyAttribution

Purpose:

- 对指定策略在指定事件中的条件进行 true / false 归因。

Key input:

- `eventType`
- `eventId`
- `queryTime`
- `policyCode`
- `policyVersion`
- `isPolicyTreeExperiment` if required

Observed:

- attribution_status: success
- condition_count: 4
- true_condition_count: 4
- false_condition_count: 0

Boundary:

- 条件表达式可以摘要展示。
- 特征业务含义需要特征字典或人工解释。
- 条件全 true 支持该策略命中解释，不等于最终作弊定性。

### 4.6 nodeBindPolicyAttribution

Purpose:

- 在策略树节点上下文中，解释绑定策略和节点级命中情况。

Key input:

- `eventType`
- `eventId`
- `queryTime`
- `policyTreeCode`
- `policyTreeVersion`
- `policyTreeNodeCode=53187346034508`

Observed:

- attribution_status: success
- node_name: `主站三方注册强绑手机号`
- returned: `nodeName`, `conditionList`, `nodebindingPolicyList`
- effective policy found: `BS_fake_account_register_thirdPlatformAll_bindphone#5`
- target policy status: online and `result=true`

Boundary:

- node binding attribution completes strategy-tree node attribution for this event.
- It still does not imply final cheating classification or enforcement recommendation.

## 5. Observation Schema 草案

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
  feature_snapshot:
    status:
    feature_count:
    feature_group_distribution:
    sample_feature_keys:
    sensitive_fields_redacted:
  policy_tree_context:
    policy_tree_code:
    policy_tree_version:
    resolved_policy_tree_node_code:
    node_name:
    node_code_source:
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
  node_binding_attribution:
    attribution_status:
    node_name:
    condition_count:
    bound_policy_count:
    effective_policy_found:
    sample_bound_policies:
  evidence_strength:
  blockers:
  limitations:
```

## 6. 证据边界

- 策略归因能解释条件 true / false 和节点绑定策略命中。
- 策略归因不等于最终作弊定性。
- 策略归因不等于自动处置建议。
- 条件表达式可以摘要展示，但特征业务含义需要特征字典或人工解释。
- `feature list` 空不代表无特征、无风险或策略无依据；本轮已通过 `featureGroup=""` 和精确 `_occurTime` 修复。
- `updateUser` 只能作为追溯字段，不做责任归因。
- `auth blocker` / `permission blocker` 不得解释为 no_data。
- rcp 策略归因 REST API 可 HTTP + SSO 调用的结论仅限本次验证的 API，不泛化到所有 RCP 接口。

## 7. 踩坑规则 / Handbook Notes

| Pitfall | Correct rule |
| --- | --- |
| `featureGroup` 传中文分类名导致 feature list 空 | 先传 `featureGroup=""` |
| `queryTime` 使用错误年份或粗略时间 | 使用事件详情中的精确 `_occurTime` |
| 使用错误策略树接口 | 正确接口是 `/v2/rest/pro/policyTree/queryProPolicyTree` |
| 用 `serial` / `policyCode` 猜 `policyTreeNodeCode` | 必须递归解析策略树获取节点 code |
| 把 HTTP + SSO 能力泛化到所有 RCP 接口 | 只限已验证策略归因 API |
| 把 `updateUser` 当责任归因 | 只能作为追溯字段 |
| 把策略归因当最终作弊结论 | 只能作为策略证据，需结合业务证据 |

## 8. 当前结论

当前可以沉淀为：

`tianshi_single_event_policy_attribution_api_read_full_p0_e2e_success`

适合回答：

- “这个 eventId 为什么命中了这个策略？”
- “这个 policyCode 在这次事件里哪些条件为 true？”
- “该策略树节点下哪些绑定策略生效？”
- “策略归因证据能支持到什么程度？”

仍不适合回答：

- “该策略是否应该上线 / 下线？”
- “这个用户是否最终作弊？”
- “哪个策略开发者应负责？”
- “是否应自动处置？”
