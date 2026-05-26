# Tianshi Strategy Governance Readonly Capability v1

## 1. 能力定位

这是天狮策略平台的“策略体系治理只读能力 v1”，不是自动处置能力。

目标是把天狮策略平台从“策略命中查询”升级为可用于策略治理的 readonly evidence platform：

- 策略详情
- 策略树资产
- 单事件策略归因
- 策略发布记录

它服务三个方向：

- 规模化：把人工点平台查策略，变成标准 API-read + observation。
- 风险感知增强：后续可统计高频生效策略、高频节点、高频条件、策略组合、策略版本变更后的命中变化。
- 策略体系治理：让策略可解释、可复盘、可回归，减少单证据强判和策略误读。

边界：

- 只读。
- 不写操作。
- 不上线策略。
- 不审批策略。
- 不自动处置。
- 不做最终作弊定性。
- 不输出敏感字段原值。

## 2. 四条链路总览

### 2.1 策略详情链路

回答：

> 这条策略是什么？

输入：

- `policyCode`
- `policyVersion`

输出：

- 策略基础信息
- 条件表达式
- 版本历史
- 绑定树
- 上线 / 下线信息

关键边界：

- 条件表达式不等于完整业务因果解释。
- `createUser` / `updateUser` 只做追溯字段，不做责任归因。
- `status=2` 上线不等于每次事件都生效。

### 2.2 策略树资产链路

回答：

> 这条策略挂在哪棵树、哪个节点？

输入：

- `policyTreeCode`
- `policyTreeVersion`
- `policyTreeNodeCode`

输出：

- 策略树结构
- 节点路径
- 节点绑定策略
- 全树策略 code

关键边界：

- 策略树资产不等于某次事件实际命中路径。
- `policyTreeList` 不适合精确查找，`queryProPolicyTree` 才是精确入口。
- `getRelationPolicyTree` 返回的 `policyTreeVersion` 可能是绑定时版本，不等于当前运行版本。

### 2.3 单事件策略归因链路

回答：

> 这次事件为什么命中 / 生效？

输入：

- `eventType`
- `eventId`
- `queryTime`
- `policyCode`
- `policyVersion`

输出：

- 事件详情
- 特征快照
- 策略版本
- 策略树节点
- 条件级归因
- 节点级归因

关键边界：

- 策略归因不等于最终作弊定性。
- 不做自动处置。
- 条件表达式需要结合特征字典或人工解释。
- `updateUser` 只做追溯字段，不做责任归因。

### 2.4 策略发布记录链路

回答：

> 这条策略经历了哪些发布 / 灰度 / 上线 / 终止流程？

输入：

- `policyCode`
- `statusCode`
- `createUser`
- `pageInfoRequest`

输出：

- 流程状态枚举
- 发布记录
- 版本变更
- 上线验收状态

关键边界：

- 发布记录用于版本和变更追溯，不等于风险定性。
- `operator` / `createUser` / `updateUser` 只做追溯字段，不做责任归因。
- `pipelineVersion` 是流程迭代版本，不是策略版本号。
- 策略版本号应从 `businessUnionKey={policyCode}_{version}_{eventTypeCode}` 解析。

## 3. 已验证 API 清单

### 3.1 策略详情

| API | Method | Purpose |
| --- | --- | --- |
| `/v2/rest/pro/policy/policySearch` | POST | 策略搜索 |
| `/v2/rest/pro/policy/getPolicyDetailByVersion` | GET | 指定版本策略详情 |
| `/v2/rest/pro/policy/getPolicyAllVersion` | GET | 策略版本历史 |
| `/v2/rest/pc/policyReview/getRelationPolicyTree` | GET | 策略绑定树关系 |

### 3.2 策略树资产

| API | Method | Purpose |
| --- | --- | --- |
| `/v2/rest/pro/policyTree/policyTreeList` | GET | 策略树列表 / 粗筛 |
| `/v2/rest/pro/policyTree/queryProPolicyTree` | GET | 精确读取策略树结构 |
| `/v2/rest/pro/policyTree/queryBindingByNodeCode` | GET | 节点级绑定策略列表 |
| `/v2/rest/pro/policyTree/getAllPolicyCodeByPage` | GET | 全树策略 code 列表 |

### 3.3 单事件策略归因

| API | Method | Purpose |
| --- | --- | --- |
| `/v2/rest/event/rcpEventDetail` | GET | 事件详情与 `_occurTime` |
| `/v2/rest/event/rcpEventFeatureList` | GET | 事件特征快照 |
| `/v2/rest/pc/policy/getPolicyVersionListByEvent` | GET | 事件关联策略版本 |
| `/v2/rest/pro/policyTree/queryProPolicyTree` | GET | 策略树节点解析 |
| `/v2/rest/pc/policy/nodePolicyAttribution` | POST | 条件级归因 |
| `/v2/rest/pc/policy/nodeBindPolicyAttribution` | GET | 节点级绑定归因 |

### 3.4 策略发布记录

| API | Method | Purpose |
| --- | --- | --- |
| `/v2/rest/common/pipeline/selectInfo` | GET | 流程状态枚举 / 筛选项 |
| `/v2/rest/common/pipeline/list` | POST | 发布 / 灰度 / 上线 / 终止记录 |

## 4. 关键参数规范

| Topic | Rule |
| --- | --- |
| `queryTime` | 使用事件精确 `_occurTime` |
| `featureGroup` | 先传空字符串，不传中文分类名 |
| `policyTreeNodeCode` | 通过 `queryProPolicyTree` 递归解析，不猜 |
| `policyTreeList` | 不适合精确查找，只做列表 / 粗筛 |
| `queryProPolicyTree` | 策略树精确入口 |
| `queryBindingByNodeCode` | 节点级策略列表 |
| `getAllPolicyCodeByPage` | 全树策略 code 列表 |
| `getRelationPolicyTree.policyTreeVersion` | 可能是绑定时版本，不等于当前运行版本 |
| `pipeline/list.extrbB` | `policyCode` 精确过滤参数 |
| `statusCode` | 可按流程状态过滤，如 `001=已上线验收通过`、`000=已终止`、`202=实验中` |
| `businessUnionKey` | 格式为 `{policyCode}_{version}_{eventTypeCode}`，策略版本号从这里解析 |
| `pipelineVersion` | 流程迭代版本，不是策略版本号 |

## 5. Observation Schema 草案

### 5.1 policy_detail_observation

```yaml
policy_detail_observation:
  policy_context:
    policy_code:
    policy_version:
    status:
    event_type_code:
  policy_definition:
    condition_expression_summary:
    punish_summary:
    feature_refs:
  version_history:
    version_count:
    latest_version:
    version_change_summary:
  relation_policy_tree:
    tree_count:
    tree_refs:
    policy_tree_version_boundary:
  evidence_strength:
  limitations:
```

### 5.2 policy_tree_asset_observation

```yaml
policy_tree_asset_observation:
  policy_tree_context:
    policy_tree_code:
    policy_tree_version:
    tree_name:
  node_context:
    policy_tree_node_code:
    node_name:
    node_path_summary:
  binding_policies:
    bound_policy_count:
    sample_policy_codes:
  all_policy_codes:
    total_count:
    page_coverage:
  evidence_strength:
  limitations:
```

### 5.3 policy_attribution_observation

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

### 5.4 policy_release_record_observation

```yaml
policy_release_record_observation:
  query_context:
    policy_code:
    status_code:
    create_user:
    page_info_request:
  status_dictionary:
    status_code:
    status_name:
  release_records:
    record_count:
    business_union_keys:
    parsed_policy_versions:
    pipeline_versions:
    status_distribution:
    experiment_or_gray_summary:
  version_trace:
    latest_policy_version:
    terminal_records:
    online_acceptance_records:
  evidence_strength:
  limitations:
```

## 6. 关键边界

- 策略详情可以展示条件表达式，但不等于完整业务因果解释。
- 策略树资产不等于某次事件实际命中路径。
- 策略归因不等于最终作弊定性。
- 发布记录不等于风险定性。
- `status=2` 上线不等于每次事件都生效。
- `proPolicyPunishList` 为空不代表无惩罚，惩罚可能在节点绑定层。
- v2 / v3 已终止表示发布流程中止，不代表策略资产不存在。
- `createUser` / `updateUser` / `bindingUser` / `operator` 只做追溯字段，不做责任归因。
- 敏感字段不输出原值。
- 不自动处置、不写操作、不上线、不审批。

## 7. 与三个价值目标关系

### 7.1 规模化

把人工点平台查策略，变成标准 API-read + observation：

- 固定输入字段。
- 固定 API 链路。
- 固定 observation schema。
- 固定证据边界。

### 7.2 风险感知增强

后续可在只读和脱敏前提下统计：

- 高频生效策略。
- 高频节点。
- 高频条件。
- 策略组合。
- 策略版本变更后的命中变化。

这些统计需要后续明确 DataAgent / Hive 或离线聚合边界；本能力本身不执行批量取数。

### 7.3 策略体系治理

让策略可解释、可复盘、可回归：

- 从“命中了某策略”扩展到“策略是什么、挂在哪里、为何在本事件生效、经历过哪些发布流程”。
- 降低单证据强判。
- 降低策略误读。
- 支持后续治理复盘材料和 regression case 沉淀。

## 8. 当前结论

四条链路均已达到 full success 文档沉淀状态：

- strategy_detail_chain: full_success
- policy_tree_asset_chain: full_success
- single_event_policy_attribution_chain: full_p0_e2e_success
- policy_release_record_chain: full_success

本能力建议标记为：

`tianshi_strategy_governance_readonly_capability_v1`
