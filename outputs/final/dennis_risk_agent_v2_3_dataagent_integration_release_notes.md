# Dennis Risk Agent v2.3 DataAgent Integration Release Notes

## 1. 本版本目标

本版本围绕两条主线交付：

1. 将 Dennis 风控 Agent 的核心 Skill 推进到 v2.3 executable-deep 结构，增强边界判断、反证、治理闭环和自评标准。
2. 新增 Data Agent 抽象层，打通 `query_intent -> dataagent_request -> dataagent_response -> normalized_evidence -> Dennis解释` 的未来内部平台接入路径。

当前版本仍处于设计和回归验证阶段：

- 不调用真实 Data Agent。
- 不定义真实 API。
- 不编造真实表名、字段名或 SQL。
- 不自动处罚、冻结、扣除或上线策略。

## 2. Skill 层完成情况

已完成的 v2.3 executable-deep 方向：

- 补充 `skill_execution_contract_v2_3.md`。
- 补充 `executable_skill_template_v2_3.md`。
- 补充 `executable_skill_quality_rubric_v2_3.md`。
- 升级/增强核心领域和攻击 Skill 的执行型结构、边界判断、反证和治理闭环。
- 新增 `legal_operation_matrix_playbook_v2_3.md`，用于合法商家、达人、MCN、机构、客服、授权工具等批量运营边界判断。
- 升级 `cracked_app_expert_skill.md`，明确破解包不是协议，但会制造“像协议”的端侧证据缺失。
- 补强导流截流、真人众包、合法矩阵、协议、群控、账号安全、活动/流量反作弊等交叉边界。

重点边界增强：

- 前端无日志不能直接判协议。
- 高频/聚集不能直接判群控。
- 低钱效不能直接判黑产。
- 外网跟价不能直接判接口被爬。
- 合法矩阵不能一刀切当群控或协议。
- 直播间用户被站外添加优先看导流截流链路，不默认反爬或协议。

## 3. Data Agent 抽象层完成情况

新增 Data Agent 能力画像和工具抽象层：

- `dataagent_capability_profile_v1.md`
- `dataagent_tool_contract_v1.md`
- `risk_evidence_to_dataagent_query_map_v1.md`
- `dataagent_result_interpretation_rules_v1.md`
- `dataagent_conclusion_thresholds_v1.md`
- `dataagent_mock_response_schema_v1.md`
- `dataagent_migration_notes_v1.md`

新增数据源配置层：

- `configs/data_domains_v1.md`
- `configs/evidence_sources_v1.md`
- `configs/field_dictionary_template_v1.md`
- `configs/query_intent_to_data_source_map_v1.md`
- `configs/permission_boundaries_v1.md`
- `configs/data_freshness_and_quality_rules_v1.md`
- `configs/query_intent_schema_v2.md`
- `configs/data_join_paths_v1.md`

新增 batch case 共性分析抽象：

- `batch_case_commonality_contract_v1.md`
- `batch_case_commonality_query_map_v1.md`
- `batch_case_cluster_interpretation_rules_v1.md`
- `batch_case_governance_playbook_v1.md`
- `batch_case_mock_regression_cases_v1.md`

## 4. query_intent 规划层回归结果

已完成多轮不查数回归：

- 3 case query_intent 生成测试。
- 10 case 历史高频/复杂 case 回归。
- schema 小回写后 4 个薄弱 case 复跑。
- 8 个扩展 case 回归。

关键结果：

- `query_intent_schema_v2` 可稳定表达风险问题、目标证据、数据域、字段类型、join path、质量检查、新鲜度、权限边界、人工确认和下一步补证。
- `data_join_paths_v1` 已补充：
  - `legal_operation_matrix_authorization_join`
  - `metric_anomaly_business_context_join`
- 12 case 规划层回归后，query_intent 结构可支持未来 adapter 设计。

典型覆盖场景：

- 协议前后端链路。
- 破解包 / SDK 绕采集。
- token 泄露 / 登录态复用。
- 撞库 / ATO。
- 群控真机。
- 渠道抢量 / 归因劫持。
- 活动低质 / 活动黑产。
- 直播间截流 / 站外添加。
- 合法矩阵。
- DAU/DNU 指标异常。
- 策略误伤与效果复盘。

## 5. adapter mock closed-loop 结果

新增 adapter 设计层：

- `adapter_design/query_intent_to_dataagent_request_design_v1.md`
- `adapter_design/dataagent_response_normalization_v1.md`
- `adapter_design/normalized_evidence_schema_v1.md`
- `adapter_design/dataagent_error_and_degrade_policy_v1.md`
- `adapter_design/audit_and_replay_design_v1.md`

完成 5 case mock closed-loop 回归：

- AC-003：协议判定，前端无日志。
- AC-004：群控真机爬取。
- AS-001：token 泄露 / 登录态复用。
- ACT-003：渠道抢量 / 归因劫持。
- AC-009：DAU/DNU 指标异常但缺攻击证据。

验证结果：

- `5/5` 完成 `query_intent -> dataagent_request -> mock dataagent_response -> normalized_evidence -> Dennis解释`。
- 覆盖 `partial`、`success`、`no_permission`、`ambiguous_result`、`empty_result`。
- `partial / no_permission / empty_result / ambiguous_result` 均能降级。
- `success` 也不会自动升级为明确判断，仍受缺失证据和反证约束。

## 6. 协议攻击最小试点设计

新增最小试点设计：

- `pilot_design/protocol_attack_evidence_minimum_pilot_v1.md`

试点目标：

- 验证“前端无日志 / 后端有请求”是否支持协议攻击判断。
- 通过 adapter 调用未来 Data Agent，补齐协议攻击证据链。
- 排除破解包绕 SDK、官方包埋点缺失、前后端 join 口径问题、合法自动化工具、群控真机可能性。

试点流程：

1. Dennis Agent 生成 `query_intent_schema_v2`。
2. adapter 转 `dataagent_request`。
3. 未来 Data Agent 返回 `dataagent_response`。
4. adapter 转 `normalized_evidence`。
5. Dennis Agent 做证据解释。
6. 输出结论等级和下一步补证。

## 7. 试点前验收清单

新增交付文件：

- `outputs/final/protocol_attack_dataagent_pilot_readiness_checklist.md`

清单覆盖：

- `query_intent_schema_v2` 完整性。
- `dataagent_request` 完整性。
- `normalized_evidence` 完整性。
- `partial / failed / no_permission / timeout / empty_result / ambiguous_result` 降级策略。
- 防止“前端无日志直接判协议”。
- 破解包、官方包埋点、join 口径、合法自动化、群控真机反证。
- 四档结论等级。
- 人工确认边界。
- 审计与回放字段。
- 内部平台接入前需补真实信息。
- 是否可以进入只读试点。

当前文档层结论：

- 可以进入只读试点准备。
- 真实平台前仍需补齐权限、数据资产映射、字段映射、join 逻辑、Data Agent 调用方式和审计回放能力。

## 8. 当前限制

当前版本仍有限制：

- 尚未接入真实 Data Agent。
- 尚未定义真实 API、认证、接口路径或错误码。
- 尚未映射真实表名、真实字段名、真实 join key。
- 尚未验证真实权限、数据质量、性能和 SLA。
- `normalized_evidence` 仍基于 mock closed-loop 设计验证。
- Skill 层有多处 v2.3 演进改动，最终入包前建议做一次针对性 review。
- 工作区存在一个编辑器临时文件，不应纳入最终包：`outputs/reviews/.dataagent_adapter_mock_closed_loop_5_case.md.swp`。

## 9. 内部平台接入前需补充的信息

内部平台侧需要补充：

- Data Agent 真实调用方式、认证和权限校验机制。
- `dataagent_request` 到真实平台请求的映射。
- 抽象数据域到真实数据资产的映射。
- 抽象字段类型到真实字段的映射。
- 抽象 join path 到真实 join key / join 逻辑的映射。
- 返回状态、错误码、权限状态和质量状态的真实枚举。
- `raw_result_reference` 的真实引用、脱敏、留存和回放机制。
- 人工确认、审批、审计、申诉和回滚流程。
- 只读试点样本池、验收指标和回归基线。

## 10. 下一步建议

建议分三步推进：

1. 先做只读试点：
   - 以协议攻击补证为第一个场景。
   - 只做取证、归一化和解释，不做自动治理。
   - 样本优先选择“前端无日志 / 后端有请求”的历史 case。

2. 再做 adapter 最小实现：
   - 实现 `query_intent -> dataagent_request` 转换。
   - 实现 `dataagent_response -> normalized_evidence` 转换。
   - 实现 `partial / no_permission / empty_result / ambiguous_result` 降级。
   - 实现审计和回放记录。

3. 最后扩展试点：
   - 群控补证试点。
   - token 泄露试点。
   - 渠道抢量试点。
   - 导流截流试点。
   - 策略误伤和效果复盘试点。
