# Non-register / Login Scene Deep Validation POC v1

## 1. POC 定位

本文档沉淀天狮策略平台非注册 / 登录场景深验证 POC。

目标：

- 验证 Dennis Agent 是否能从注册 / 登录扩展到直播 attach 和 ANTICRAWL。
- 识别哪些非注册 / 登录场景可以进入 runtime candidate，哪些仍只能作为资产候选。
- 补齐业务安全场景资产地图中 P0 场景的验证状态。

边界：

- 这不是用户风险研判。
- 这不是自动处置能力。
- 这不代表所有非注册 / 登录场景已上线。
- 不访问真实平台，不调用 DataAgent，不更新 release package。

## 2. live_attach 验证摘要

```yaml
scene_name: live_attach
event_type: SYNC_LIVE_ATTACH_REQUEST
fastQueryHbase: success
eventList:
  status: success
  event_count: 8
  blocked_count: 3
  allowed_count: 5
rcpEventDetail:
  status: partial
  allowed_event_detail: success
  blocked_event_detail: timeout_http_and_browser
getPolicyVersionListByEvent: success
nodePolicyAttribution: success
queryProPolicyTree:
  status: partial
  issue: only_policy_tree_version_returned_without_node_structure
getPolicyDetailByVersion:
  status: partial
  issue: fields_empty
validation_status: deep_validation_partial
runtime_candidate_status: beta_partial
```

核心结论：

- fastQueryHbase 成功发现 3 条阻止事件和 2 个 antibrush 策略。
- eventList browser 成功发现 8 个事件：3 阻止 + 5 允许。
- rcpEventDetail 对允许事件成功，对阻止事件 HTTP + browser 都 timeout。
- getPolicyVersionListByEvent 能返回 antibrush 策略版本。
- nodePolicyAttribution 对阻止事件成功，2 条策略均完成条件级归因，5 条件全 true。
- 归因路径可用于补足 queryProPolicyTree 节点结构为空的问题。
- attach 可作为非注册 / 登录 runtime candidate，但状态应为 partial candidate，不是 full success。

## 3. attach 策略归因路径

### BS_antibrush_attach_user_multi_loc_block_policy

归因路径：

```text
直播长连接建连请求同步接入事件
→ 业务安全
→ 直播人气防刷
→ 直播人气防刷策略
→ 用户位置频繁跳变拦截策略
```

### BS_antibrush_attach_not_same_startup_block_policy

归因路径：

```text
直播长连接建连请求同步接入事件
→ 业务安全
→ 直播人气防刷
→ 协议策略包节点
→ 启动参数不一致拦截策略
```

归因边界：

- 两条策略 `nodePolicyAttribution` 均 5 条件全 true。
- 这是条件级归因成功，不等于最终风险定性。
- `confidenceLevel=强` 不等于最终风险结论。

## 4. ANTICRAWL 家族状态

```yaml
scene_name: anti_crawler_antibrush
validation_status: candidate_only
current_source_id_hit_status: no_hit_on_2026_05_26_for_source_218368298
eventList_status: success_empty_result
confirmed_subtree_versions:
  - ANTICRAWL_LIVE
  - ANTICRAWL_BASE
  - ANTICRAWL_SEARCH
  - ANTICRAWL_COMMON
  - ANTICRAWL_RPC_SIGN
not_returned_or_unconfirmed:
  - ANTICRAWL
  - ANTICRAWL_PLATFORM_SYNC
  - LIVE_STREAM_ANTICRAWL
runtime_candidate_status: candidate_only
next_requirement: source_id_or_eventId_with_anticrawl_hit
```

结论：

- 当前 `source_id=218368298` 在 2026-05-26 当天无 ANTICRAWL 命中。
- eventList 查询成功但返回 0。
- queryProPolicyTree 可确认部分子树版本：`ANTICRAWL_LIVE`、`ANTICRAWL_BASE`、`ANTICRAWL_SEARCH`、`ANTICRAWL_COMMON`、`ANTICRAWL_RPC_SIGN`。
- `ANTICRAWL` 根节点 / `ANTICRAWL_PLATFORM_SYNC` / `LIVE_STREAM_ANTICRAWL` 无版本返回。
- ANTICRAWL 更像策略树家族，不是单一策略树。
- 下一步需要有反爬命中的 `source_id` 或 `eventId`。

## 5. 新工程发现

- `nodePolicyAttribution` 可作为 `queryProPolicyTree` 节点结构为空时的替代路径。
- fastQueryHbase 可作为非注册 / 登录场景命中发现入口。
- eventList 可用于补允许事件和 eventType 事件分布。
- 阻止事件 rcpEventDetail timeout 不应阻塞归因链路，只能标记 `event_detail_partial`。
- `getPolicyDetailByVersion` 对 antibrush 策略字段为空，不应解释为策略不存在。

## 6. Schema 草案

```yaml
non_register_login_scene_validation_observation:
  scene_name:
  event_type:
  fast_query_hbase_status:
  event_list_status:
  event_detail_status:
  policy_tree_status:
  policy_detail_status:
  attribution_status:
  sample_events:
    - event_ref:
      risk_decision:
      event_detail_status:
      attribution_status:
  sample_policies:
    - policy_code:
      policy_version:
      policy_detail_status:
      attribution_status:
  attribution_paths:
    - policy_code:
      path_nodes:
      condition_count:
      true_condition_count:
  validation_status:
  runtime_candidate_status:
  blockers:
  boundaries:
```

## 7. runtime candidate 建议

### live_attach

- 可进入 runtime candidate。
- 状态：`beta / partial`。
- 如果用户问“直播 attach 为什么被拦 / 直播长连接被拦”，可先走：
  1. fastQueryHbase
  2. eventList
  3. nodePolicyAttribution
- 阻止事件 detail timeout 时应输出 `event_detail_partial`，不阻断条件级归因。

### ANTICRAWL

- 不进入 runtime candidate。
- 状态：`candidate_only`。
- 如果用户问“反爬是否命中”，当前只能输出 query plan 或要求提供有反爬命中的 `source_id` / `eventId`。

## 8. 边界

- 本轮是场景深验证，不是风险研判。
- 策略命中不等于最终风险定性。
- attach 阻止事件 detail timeout 不等于 no_data。
- ANTICRAWL 当前用户无命中不等于无反爬历史。
- `confidenceLevel=强` 不等于最终定性。
- `updateUser` / `operator` / `owner` 只做追溯字段，不做责任归因。
- 不输出敏感字段原值。
- 不自动处置、不写操作、不上线、不审批。
- 不把 ANTICRAWL 注册为 runtime 能力。
