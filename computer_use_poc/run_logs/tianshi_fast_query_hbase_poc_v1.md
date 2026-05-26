# Tianshi fastQueryHbase POC v1

## Goal

沉淀内部 Agent 对天狮策略平台 `fastQueryHbase` 的最新 POC 结果，并修正 `strategy_hit_inventory` 的推荐入口。

本轮只做本地文档沉淀：

- 不访问真实平台。
- 不调用 DataAgent。
- 不更新 release package。
- 不修改核心 Skill。
- 不提交 git。

## POC Result

```yaml
execution_mode: internal_agent_observation_summary
endpoint: GET /v2/rest/event/fastQueryHbase
access_mode: HTTP+SSO
result: PASS

request:
  eventTypeCodes: ""
  sourceIds: 218368298
  startTime: 1779724800512
  endTime: 1779787311130
  limit: 500

response_summary:
  data_count: 5
  fields:
    - sourceId
    - eventId
    - eventType
    - riskDecision
    - errorCode
    - hitTimestamp
    - hitProductionPolicy
    - hitProductionPolicies
    - hitPolicies
    - confidenceLevel
    - riskEventName
    - riskType
    - updateUser
    - deviceId
```

## Key Corrections

1. `fastQueryHbase` 不是 browser-only。
   - 它可以 HTTP + SSO 直连。

2. 之前失败原因是 `eventTypeCodes` 参数传错。
   - 不要传 `"BS,ANTICRAWL,ACTIVITY_ANTISPAM,ACCOUNT,FLOW_ANTISPAM"` 这类字符串枚举。
   - 应先传空字符串 `eventTypeCodes=""`，表示全事件类型。

3. `fastQueryHbase` 应作为 `strategy_hit_inventory` 的首选批量入口。
   - 用于用户维度策略命中概览。
   - 获取 `eventId` / `eventType` / `hitPolicies` / `riskDecision`。

4. `eventList` 降级为补查入口。
   - 用于 eventType 级明细补查。
   - 尤其用于允许事件、`ec=1` 事件和请求级字段补查。
   - 依赖 browser same-origin。

5. `rcpEventDetail` / 归因链路仍用于代表 event 深挖。
   - `rcpEventDetail` 负责单事件详情。
   - `nodePolicyAttribution` / `nodeBindPolicyAttribution` 负责条件级 / 节点级归因。

6. `hitTimestamp` 不能直接等同 rcpEventDetail `queryTime`。
   - USER_REGISTER_NEW 样本中 `hitTimestamp` 与 `_occurTime` 差约 50ms。
   - 代表 event 下钻时应优先使用事件详情中的 `_occurTime`。
   - 如只能使用 `hitTimestamp`，必须标记 `queryTime_source=hitTimestamp_approximate`。

## Newly Observed Event / Policies

```yaml
new_event_type:
  - SYNC_LIVE_ATTACH_REQUEST

new_policies:
  - BS_antibrush_attach_user_multi_loc_block_policy
  - BS_antibrush_attach_not_same_startup_block_policy
```

`SYNC_LIVE_ATTACH_REQUEST` 下钻 `rcpEventDetail` 时 HTTP timeout，应标记为 `event_detail_partial`，不得解释为无风险或无事件详情。

## Recommended Chain

1. fastQueryHbase HTTP + SSO
   - 用户维度命中概览。
   - 拿 `eventId` / `eventType` / `hitPolicies` / `riskDecision`。

2. eventList browser same-origin
   - eventType 级补查。
   - 允许事件、`ec=1` 事件、请求级字段补查。

3. rcpEventDetail HTTP + SSO
   - 代表 event 详情。

4. nodePolicyAttribution / nodeBindPolicyAttribution
   - 代表 event 条件级 / 节点级归因。

5. 聚合输出
   - `policy_topn`
   - `node_topn`
   - `condition_topn`
   - `policy_cooccurrence`
   - `representative_events`

## Boundaries

- 策略命中概览不等于最终风险定性。
- `confidenceLevel='强'` 不等于最终定性。
- `riskDecision=阻止` 是策略返回动作，不等于用户级风险结论或处置成功。
- `updateUser` / `operator` / `bindingUser` 只做追溯字段，不做责任归因。
- `sourceIp`、`deviceId`、用户标识等敏感或风控实体字段不得输出原值；按字段输出分层策略做摘要、safe_ref、计数或分布。
- `no_data` / timeout / auth_blocker 不得解释为无风险。

## Files Updated

- `computer_use_poc/strategy_governance/single_user_event_strategy_inventory_poc_v1.md`
- `computer_use_poc/capability_registry.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/smoke_tests.md`
- `computer_use_poc/README.md`
