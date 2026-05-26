# Tianshi Strategy Governance Validation Cases v1

## 1. Purpose

This document defines acceptance test cases for Tianshi Strategy Governance Readonly Capability v1.

The goal is no longer to validate whether APIs are reachable. The goal is to validate whether the capability can answer real strategy governance questions with correct evidence structure and boundaries.

Covered full-success chains:

1. Strategy detail.
2. Policy tree asset.
3. Single-event policy attribution.
4. Policy release records.

Execution boundary for all cases:

- Do not access real platforms in this text validation.
- Do not call DataAgent.
- Do not update release package.
- Do not modify core Skill.
- Do not output sensitive raw values.
- Do not write / approve / publish / enforce policy.

## 2. Global Boundaries

Every case must preserve:

- Strategy attribution is not final cheating classification.
- Strategy detail condition expression is not complete business-causality explanation.
- Policy tree asset is not the actual hit path for a specific event.
- Release records are not risk classification.
- `status=2` online does not mean the policy is effective for every event.
- `createUser` / `updateUser` / `bindingUser` / `operator` are trace fields, not responsibility attribution.
- Sensitive fields must not be output as raw values.
- No automatic enforcement, write operation, publishing, or approval.

## 3. Validation Cases

### Case 1: Single-event Policy Attribution

user_question:

> eventType=USER_REGISTER_NEW, eventId=5370247893355116990, policyCode=BS_fake_account_register_thirdPlatformAll_bindphone, policyVersion=5。请解释这次事件为什么被阻止、哪个策略生效、哪些条件成立。

expected_intent:

- single_event_policy_attribution

expected_capabilities:

- policy_attribution_observation
- event_detail_read
- event_feature_snapshot_read
- policy_version_lookup
- policy_tree_node_resolution
- condition_attribution
- node_binding_attribution

expected_api_chain:

- `GET /v2/rest/event/rcpEventDetail`
- `GET /v2/rest/event/rcpEventFeatureList`
- `GET /v2/rest/pc/policy/getPolicyVersionListByEvent`
- `GET /v2/rest/pro/policyTree/queryProPolicyTree`
- `POST /v2/rest/pc/policy/nodePolicyAttribution`
- `GET /v2/rest/pc/policy/nodeBindPolicyAttribution`

expected_observation_fields:

- `event_context.event_type`
- `event_context.event_id`
- `event_context.query_time_ms`
- `event_context.real_time_feedback`
- `event_context.error_code`
- `event_context.effective_policy`
- `feature_snapshot.feature_count`
- `feature_snapshot.feature_group_distribution`
- `policy_tree_context.resolved_policy_tree_node_code`
- `policy_tree_context.node_name`
- `condition_attribution.condition_count`
- `condition_attribution.true_condition_count`
- `node_binding_attribution.effective_policy_found`

expected_answer_structure:

1. One-line conclusion.
2. Event context.
3. Effective / hit policy summary.
4. Feature snapshot summary.
5. Condition attribution summary.
6. Node binding attribution summary.
7. Missing evidence / limitations.
8. Boundary statement.

must_include_boundaries:

- Strategy attribution is not final cheating classification.
- Conditions true explain policy hit, not complete business causality.
- Do not output raw feature values.
- No automatic enforcement.

pass_criteria:

- Correctly identifies the effective policy.
- Explains condition-level attribution and node-level binding attribution.
- Uses exact event `_occurTime` as `queryTime`.
- Mentions `featureGroup=""` feature snapshot fix.
- Preserves all required boundaries.

fail_criteria:

- Treats policy attribution as final cheating proof.
- Omits node binding attribution.
- Outputs raw feature values.
- Recommends automatic punishment / approval / publish action.

### Case 2: Strategy Detail Explanation

user_question:

> policyCode=BS_fake_account_register_thirdPlatformAll_bindphone, policyVersion=5。请解释这条策略是什么、条件表达式是什么、当前版本是多少。

expected_intent:

- policy_detail_explanation

expected_capabilities:

- policy_detail_observation
- policy_search
- policy_detail_by_version
- policy_all_version
- relation_policy_tree

expected_api_chain:

- `POST /v2/rest/pro/policy/policySearch`
- `GET /v2/rest/pro/policy/getPolicyDetailByVersion`
- `GET /v2/rest/pro/policy/getPolicyAllVersion`
- `GET /v2/rest/pc/policyReview/getRelationPolicyTree`

expected_observation_fields:

- `policy_context.policy_code`
- `policy_context.policy_version`
- `policy_context.status`
- `policy_definition.condition_expression_summary`
- `policy_definition.punish_summary`
- `version_history.version_count`
- `version_history.latest_version`
- `relation_policy_tree.tree_refs`
- `relation_policy_tree.policy_tree_version_boundary`

expected_answer_structure:

1. Policy identity.
2. Version / status.
3. Condition expression summary.
4. Punish / action summary.
5. Version history.
6. Related policy tree summary.
7. Boundary statement.

must_include_boundaries:

- Condition expression is not complete business-causality explanation.
- `createUser` / `updateUser` are trace fields, not responsibility attribution.
- `status=2` online does not mean effective for every event.
- Sensitive fields redacted.

pass_criteria:

- Explains policy at version 5.
- Separates policy definition from actual event hit.
- Does not overinterpret condition expression.
- Does not attribute responsibility to creator/updater.

fail_criteria:

- Claims the strategy proves user cheating.
- Treats condition expression as complete causality.
- Uses `createUser` / `updateUser` to assign blame.
- Outputs sensitive raw fields.

### Case 3: Policy Tree Asset

user_question:

> policyTreeCode=USER_REGISTER_NEW, policyTreeVersion=887, targetNodeName=主站三方注册强绑手机号。请解释该节点在策略树中的路径、绑定策略数、目标策略状态、全树策略数量。

expected_intent:

- policy_tree_asset_explanation

expected_capabilities:

- policy_tree_asset_observation
- policy_tree_precise_read
- node_binding_policy_list
- all_policy_code_list

expected_api_chain:

- `GET /v2/rest/pro/policyTree/policyTreeList`
- `GET /v2/rest/pro/policyTree/queryProPolicyTree`
- `GET /v2/rest/pro/policyTree/queryBindingByNodeCode`
- `GET /v2/rest/pro/policyTree/getAllPolicyCodeByPage`

expected_observation_fields:

- `policy_tree_context.policy_tree_code`
- `policy_tree_context.policy_tree_version`
- `policy_tree_context.tree_name`
- `node_context.policy_tree_node_code`
- `node_context.node_name`
- `node_context.node_path_summary`
- `binding_policies.bound_policy_count`
- `binding_policies.sample_policy_codes`
- `all_policy_codes.total_count`
- `all_policy_codes.page_coverage`

expected_answer_structure:

1. Tree identity.
2. Node path summary.
3. Node binding policy count.
4. Target policy status in node binding list.
5. Full-tree policy code coverage.
6. Boundary statement.

must_include_boundaries:

- Policy tree asset is not actual hit path for a specific event.
- `policyTreeList` is not the precise entry; `queryProPolicyTree` is.
- Binding policy status does not prove every event hits the policy.
- Sensitive fields redacted.

pass_criteria:

- Uses `queryProPolicyTree` as precise tree read.
- Uses `queryBindingByNodeCode` for node-level policy list.
- Uses `getAllPolicyCodeByPage` for full-tree policy code list.
- Does not confuse asset structure with event attribution.

fail_criteria:

- Claims tree asset proves the event hit path.
- Uses only `policyTreeList` as precise lookup.
- Omits node binding list.
- Outputs sensitive raw values.

### Case 4: Policy Release Records

user_question:

> policyCode=BS_fake_account_register_thirdPlatformAll_bindphone。请解释这条策略 v2-v5 的发布/终止/上线记录，并说明 businessUnionKey 和 pipelineVersion 应该怎么理解。

expected_intent:

- policy_release_record_explanation

expected_capabilities:

- policy_release_record_observation
- pipeline_status_dictionary
- pipeline_record_list
- policy_version_parse

expected_api_chain:

- `GET /v2/rest/common/pipeline/selectInfo`
- `POST /v2/rest/common/pipeline/list`

expected_observation_fields:

- `query_context.policy_code`
- `query_context.status_code`
- `status_dictionary.status_code`
- `status_dictionary.status_name`
- `release_records.record_count`
- `release_records.business_union_keys`
- `release_records.parsed_policy_versions`
- `release_records.pipeline_versions`
- `release_records.status_distribution`
- `version_trace.latest_policy_version`
- `version_trace.terminal_records`
- `version_trace.online_acceptance_records`

expected_answer_structure:

1. Release record summary.
2. Status dictionary explanation.
3. v2-v5 version timeline.
4. `businessUnionKey` parsing rule.
5. `pipelineVersion` boundary.
6. Boundary statement.

must_include_boundaries:

- Release records are not risk classification.
- `pipeline/list.extrbB=policyCode` is exact filter.
- Policy version must be parsed from `businessUnionKey={policyCode}_{version}_{eventTypeCode}`.
- `pipelineVersion` is process iteration version, not policy version.
- Operator / createUser / updateUser are trace fields, not responsibility attribution.

pass_criteria:

- Correctly uses `extrbB=policyCode`.
- Correctly parses version from `businessUnionKey`.
- Does not misuse `pipelineVersion`.
- Explains statusCode boundary such as `001`, `000`, `202`.

fail_criteria:

- Treats release record as risk conclusion.
- Treats `pipelineVersion` as policy version.
- Assigns responsibility to operator / creator.
- Recommends automatic approval / rollback / publish.

### Case 5: Integrated Strategy Governance

user_question:

> eventType=USER_REGISTER_NEW, eventId=5370247893355116990, policyCode=BS_fake_account_register_thirdPlatformAll_bindphone。请从策略详情、策略树资产、单事件归因、发布记录四个角度解释这次事件为什么被阻止，并说明边界。

expected_intent:

- integrated_strategy_governance_explanation

expected_capabilities:

- policy_detail_observation
- policy_tree_asset_observation
- policy_attribution_observation
- policy_release_record_observation

expected_api_chain:

- Strategy detail:
  - `POST /v2/rest/pro/policy/policySearch`
  - `GET /v2/rest/pro/policy/getPolicyDetailByVersion`
  - `GET /v2/rest/pro/policy/getPolicyAllVersion`
  - `GET /v2/rest/pc/policyReview/getRelationPolicyTree`
- Policy tree asset:
  - `GET /v2/rest/pro/policyTree/policyTreeList`
  - `GET /v2/rest/pro/policyTree/queryProPolicyTree`
  - `GET /v2/rest/pro/policyTree/queryBindingByNodeCode`
  - `GET /v2/rest/pro/policyTree/getAllPolicyCodeByPage`
- Single-event attribution:
  - `GET /v2/rest/event/rcpEventDetail`
  - `GET /v2/rest/event/rcpEventFeatureList`
  - `GET /v2/rest/pc/policy/getPolicyVersionListByEvent`
  - `POST /v2/rest/pc/policy/nodePolicyAttribution`
  - `GET /v2/rest/pc/policy/nodeBindPolicyAttribution`
- Release records:
  - `GET /v2/rest/common/pipeline/selectInfo`
  - `POST /v2/rest/common/pipeline/list`

expected_observation_fields:

- `policy_detail_observation.policy_context`
- `policy_tree_asset_observation.node_context`
- `policy_attribution_observation.event_context`
- `policy_attribution_observation.condition_attribution`
- `policy_attribution_observation.node_binding_attribution`
- `policy_release_record_observation.release_records`
- `policy_release_record_observation.version_trace`

expected_answer_structure:

1. One-line integrated answer.
2. Policy detail view.
3. Policy tree asset view.
4. Single-event attribution view.
5. Release record view.
6. Evidence strength and gaps.
7. Governance boundary.

must_include_boundaries:

- Strategy attribution is not final cheating classification.
- Strategy detail condition expression is not complete business causality.
- Policy tree asset is not actual hit path by itself.
- Release records are not risk classification.
- `status=2` online does not mean every event is affected.
- `createUser` / `updateUser` / `bindingUser` / `operator` are not responsibility attribution.
- No sensitive raw output.
- No automatic enforcement / write / publish / approval.

pass_criteria:

- Uses all four observation views.
- Separates “what the strategy is”, “where it is mounted”, “why this event hit”, and “how it was released”.
- Produces a governance-grade answer without overclaiming.
- Explicitly states all required boundaries.

fail_criteria:

- Collapses all evidence into “user is cheating”.
- Treats policy tree asset as actual hit path without event attribution.
- Treats release record as risk proof.
- Outputs sensitive raw fields.
- Recommends automatic enforcement, publish, approval, rollback, or owner blame.

## 4. Validation Summary

Expected result:

- case_count: 5
- strategy_detail_chain_covered: true
- policy_tree_asset_chain_covered: true
- single_event_policy_attribution_chain_covered: true
- policy_release_record_chain_covered: true
- critical_boundaries_covered: true

This document is a validation design artifact only. It does not call real APIs, does not call DataAgent, and does not update release packages.
