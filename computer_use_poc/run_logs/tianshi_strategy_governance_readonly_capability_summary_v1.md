# Tianshi Strategy Governance Readonly Capability Summary v1

## 1. 本轮目标

沉淀天狮策略平台“策略治理只读能力 v1”，整合四条已完成 full success 链路：

- 单事件策略归因链路
- 策略详情链路
- 策略树资产链路
- 策略发布记录链路

Execution boundary:

- real_platform_access=false
- dataagent_called=false
- release_package_updated=false
- core_skill_modified=false
- grafana_added=false
- feature_service_added=false
- write_action=false
- auto_enforcement=false
- final_risk_classification=false

## 2. 四链路状态

| Chain | Status | Core capability |
| --- | --- | --- |
| 单事件策略归因 | full_p0_e2e_success | 解释某次事件为什么命中 / 生效 |
| 策略详情 | full_success | 解释某条策略是什么、条件表达式、版本演进、绑定树 |
| 策略树资产 | full_success | 解释策略树结构、节点路径、节点绑定策略、全树策略 code |
| 策略发布记录 | full_success | 解释发布流程状态、实验 / 审批 / 灰度 / 上线 / 终止和版本变更 |

## 3. API Summary

### 单事件策略归因

- `GET /v2/rest/event/rcpEventDetail`
- `GET /v2/rest/event/rcpEventFeatureList`
- `GET /v2/rest/pc/policy/getPolicyVersionListByEvent`
- `GET /v2/rest/pro/policyTree/queryProPolicyTree`
- `POST /v2/rest/pc/policy/nodePolicyAttribution`
- `GET /v2/rest/pc/policy/nodeBindPolicyAttribution`

### 策略详情

- `POST /v2/rest/pro/policy/policySearch`
- `GET /v2/rest/pro/policy/getPolicyDetailByVersion`
- `GET /v2/rest/pro/policy/getPolicyAllVersion`
- `GET /v2/rest/pc/policyReview/getRelationPolicyTree`

### 策略树资产

- `GET /v2/rest/pro/policyTree/policyTreeList`
- `GET /v2/rest/pro/policyTree/queryProPolicyTree`
- `GET /v2/rest/pro/policyTree/queryBindingByNodeCode`
- `GET /v2/rest/pro/policyTree/getAllPolicyCodeByPage`

### 策略发布记录

- `GET /v2/rest/common/pipeline/selectInfo`
- `POST /v2/rest/common/pipeline/list`

## 4. Key Fixes / Boundaries

- `queryTime` 使用事件精确 `_occurTime`。
- `featureGroup` 传空字符串，不传中文分类名。
- `policyTreeNodeCode` 通过 `queryProPolicyTree` 递归解析，不猜。
- `pipeline/list` 中 `extrbB=policyCode` 是精确过滤参数。
- 策略版本号从 `businessUnionKey={policyCode}_{version}_{eventTypeCode}` 解析。
- `pipelineVersion` 是流程迭代版本，不是策略版本号。
- `updateUser` / `operator` / `createUser` / `bindingUser` 只做追溯字段，不做责任归因。
- 策略归因不等于最终作弊定性。
- 策略治理能力不做自动处置、不写操作、不上线、不审批。

## 5. 当前未做

- Grafana。
- 特征服务。
- 自动策略发布。
- 自动审批。
- 自动风险定性。
- release package 更新。
- 核心 Skill 修改。

## 6. 结论

建议标记：

`tianshi_strategy_governance_readonly_capability_v1`

该能力使天狮从策略命中查询扩展为策略详情 + 策略树资产 + 单事件策略归因 + 策略发布记录的 readonly governance loop。
