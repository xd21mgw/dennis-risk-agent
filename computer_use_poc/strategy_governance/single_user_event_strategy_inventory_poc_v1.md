# Single User Event Strategy Inventory POC v1

## 1. 能力定位

`single_user_event_strategy_inventory` 是天狮策略平台的单用户多事件策略命中盘点能力草案。

目标是在一个 `source_id` 的一个时间窗内，从多个 event 中聚合：

- TOP 策略
- TOP 节点
- TOP 条件
- 策略共现模式
- 代表事件
- 治理发现

该能力用于风险感知增强和策略治理线索发现，不等于跨用户批量风险簇，也不输出用户级风险定性。

## 2. 已验证链路

本轮内部 Agent POC 已验证：

1. browser eventList
   - `source_id -> event_id` 列表
   - eventList browser same-origin 批量入口已打通。

2. HTTP + SSO rcpEventDetail
   - `event_id -> 事件详情`
   - 9 个事件中 8 个完成事件详情读取。

3. HTTP + SSO nodePolicyAttribution / nodeBindPolicyAttribution
   - 事件级条件归因和节点绑定策略归因。
   - 3 个事件完成完整策略归因：2 个阻止事件 + 1 个允许事件。

4. 聚合输出
   - `policy_topn`
   - `node_topn`
   - `condition_topn`
   - `policy_cooccurrence`
   - `representative_events`
   - `governance_findings`

## 3. POC 结果摘要

```yaml
poc_scope:
  source_id: 218368298
  date: 2026-05-26
  event_count: 9
  event_detail_success_count: 8
  attributed_event_count: 3

event_type_distribution:
  USER_REGISTER_NEW: 3
  LOGIN_AUDIT: 3
  ASYNC_LOGIN: 3

risk_decision_distribution:
  allow: 7
  block: 2

overall_result:
  strategy_hit_inventory_feasible: true
  can_support_risk_perception_enhancement: true
  ready_for_codex_schema_template: true
```

## 4. Observation Schema 草案

```yaml
single_user_event_strategy_inventory_observation:
  source_id:
  time_window:
    start:
    end:
    timezone:
  event_count:
  event_detail_success_count:
  attributed_event_count:
  event_type_distribution:
    USER_REGISTER_NEW:
    LOGIN_AUDIT:
    ASYNC_LOGIN:
  risk_decision_distribution:
    allow:
    block:
    verify:
    unknown:
  policy_topn:
    - policy_code:
      policy_version:
      hit_count:
      risk_decision_distribution:
      sample_event_refs:
  node_topn:
    - policy_tree_node_code:
      node_name:
      hit_count:
      bound_policy_count:
      sample_event_refs:
  condition_topn:
    - condition_key_or_expr_ref:
      true_count:
      false_count:
      sample_event_refs:
      business_meaning_status:
  policy_cooccurrence:
    - policy_codes:
      cooccur_count:
      sample_event_refs:
      interpretation_boundary:
  representative_events:
    - event_ref:
      event_type:
      risk_decision:
      effective_policy:
      attribution_status:
      reason_to_represent:
  governance_findings:
    - finding:
      supporting_aggregate:
      boundary:
      recommended_followup:
  missing_evidence:
    - event_detail_failed_or_skipped:
    - attribution_failed_or_skipped:
    - feature_snapshot_missing:
    - policy_tree_context_missing:
  limitations:
    - 单用户多事件盘点，不代表跨用户批量风险簇。
    - 策略命中是事件级结论，不是用户级风险定性。
    - TOP 策略 / 节点 / 条件只是风险感知线索。
  boundaries:
    - 高频策略不等于策略一定有效。
    - 高频节点不等于节点有问题。
    - 策略组合共现不等于团伙或攻击路径定性。
    - no_data / timeout / auth_blocker 不得解释为无风险。
    - updateUser / operator / bindingUser 只做追溯字段，不做责任归因。
    - 不输出敏感字段原值，不自动处置。
```

## 5. Answer Template 草案

```text
结论摘要：
本次只能说明该 source_id 在指定时间窗内的事件级策略命中和归因分布，可用于风险感知增强；不能直接给用户级风险定性或处置结论。

事件分布：
- event_count:
- event_detail_success_count:
- attributed_event_count:
- event_type_distribution:

反馈分布：
- allow:
- block:
- verify:
- unknown:

TOP 策略：
- policy_topn:
- 解释边界：高频策略不等于策略一定有效，也不代表用户最终风险成立。

TOP 节点：
- node_topn:
- 解释边界：高频节点不等于节点有问题，需要结合策略树、事件类型和样本分布复核。

TOP 条件：
- condition_topn:
- 解释边界：条件 true/false 是策略表达式层证据，业务含义需要特征字典或人工解释。

策略共现：
- policy_cooccurrence:
- 解释边界：策略组合共现不等于团伙、攻击路径或基础设施共用定性。

代表事件：
- representative_events:
- 说明为什么选择这些事件做后续人工复核或深挖。

治理发现：
- governance_findings:
- 推荐用于策略治理、回归、版本核对或风险感知增强的后续动作。

不能下的结论：
- 单用户多事件不等于跨用户批量风险簇。
- 策略命中是事件级结论，不是用户级风险定性。
- no_data / timeout / auth_blocker 不得解释为无风险。
- updateUser / operator / bindingUser 只做追溯字段，不做责任归因。
- 不自动处置、不写操作、不上线、不审批。

下一步建议：
- 如要判断用户风险，补用户画像、登录日志、设备、行为和内容证据。
- 如要进入跨用户风险感知，扩展到 multi_user_strategy_hit_inventory，增加 source_id / case_id 样本和稳定时间窗。
```

## 6. Validation Cases 草案

### Case 1: 单用户当天多事件盘点

- 输入：`source_id` + 当天时间窗。
- 预期：输出 event distribution、risk decision distribution、policy_topn、node_topn、condition_topn、representative_events。
- 失败标准：只输出单条事件详情，未做多事件聚合。

### Case 2: 同一用户既有阻止又有允许

- 输入：同一 `source_id` 的多个允许 / 阻止事件。
- 预期：分开展示 allow / block 分布，说明反馈不同不等于策略矛盾。
- 失败标准：把允许事件或阻止事件单独升级成用户级风险定性。

### Case 3: 策略共现但不同策略主导反馈

- 输入：多个 event 中策略共现，但 effective policy 或 risk decision 不完全一致。
- 预期：输出 `policy_cooccurrence` 和代表事件，说明共现只是线索。
- 失败标准：把共现直接写成攻击链、团伙或同一原因。

### Case 4: eventDetail 部分失败 / skipped

- 输入：部分 event 详情读取失败、timeout 或 skipped。
- 预期：记录 `event_detail_success_count`、`missing_evidence` 和 source gap。
- 失败标准：把失败 / skipped 当作无风险或无命中。

### Case 5: 允许事件无 effective_policy

- 输入：允许事件中没有明确 effective policy。
- 预期：保留事件级结论边界，允许事件可进入代表事件但不得强造 effective policy。
- 失败标准：猜测 policyCode 或把允许事件解释成无风险。

### Case 6: 不得输出用户级风险定性

- 输入：要求“这个用户是不是风险用户”。
- 预期：说明本能力只做单用户多事件策略盘点；用户级风险需补登录、设备、行为、内容、账号画像等多源证据。
- 失败标准：仅凭 TOP 策略 / TOP 节点 / TOP 条件给用户风险定性或处置建议。

## 7. 后续扩展

后续可以扩展为 `multi_user_strategy_hit_inventory`：

- 输入多个 `source_id` / `case_id`。
- 输出跨用户 TOP 策略、TOP 节点、TOP 条件、策略共现、风险簇候选。
- 需要更多 source_id、更稳定时间窗和跨用户归一化统计。
- 扩展后仍必须区分事件级策略证据、用户级风险证据和跨用户风险簇候选。
