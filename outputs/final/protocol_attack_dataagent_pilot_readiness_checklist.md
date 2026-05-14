# Protocol Attack Data Agent Pilot Readiness Checklist

试点名称：`protocol_attack_evidence_minimum_pilot_v1`

本清单用于试点前人工验收。当前阶段不调用真实 Data Agent，不定义真实 API，不编造真实表名、字段名或 SQL。

## 1. query_intent_schema_v2 完整性

验收项：

- [ ] 是否包含 `intent_id`、`intent_type`、`risk_question`、`target_evidence`。
- [ ] 是否明确主控 Skill：`protocol_attack_expert_skill`。
- [ ] 是否包含辅助 Skill：`cracked_app_expert_skill`、`account_security_expert_skill`、`group_control_expert_skill` 或其他必要 Skill。
- [ ] 是否包含最小输入：`user_id 或 device_id`、`api_name 或业务动作`、`time_window`。
- [ ] 是否包含 `required_data_domains`：前端行为域、后端数据域、设备信息域、策略引擎域。
- [ ] 是否包含 `field_types_needed`，且只使用抽象字段类型。
- [ ] 是否包含 `join_paths_needed`，且只使用抽象 join path。
- [ ] 是否包含 `quality_checks` 和 `downgrade_if`。
- [ ] 是否包含 `freshness_expectation`、`permission_boundary`、`manual_review_required`。
- [ ] 是否包含 `safety_boundary` 和 `next_query_intent_when_insufficient`。

验收结论：

- 通过条件：以上全部满足。
- 不通过处理：补齐 query_intent 后再进入 adapter。

## 2. dataagent_request 结构完整性

验收项：

- [ ] 是否包含 `request_id`。
- [ ] 是否包含 `source_query_intent_id`。
- [ ] 是否包含 `task_type`，协议补证首轮应为 `data_query`。
- [ ] 是否包含 `natural_language_question`。
- [ ] `natural_language_question` 是否明确“返回证据，不做最终风控定性”。
- [ ] 是否传递 `target_evidence`。
- [ ] 是否传递 `data_domains`。
- [ ] 是否传递 `field_types_needed`。
- [ ] 是否传递 `join_paths_needed`。
- [ ] 是否传递 `time_window` 和 `query_dimensions`。
- [ ] 是否传递 `expected_outputs`。
- [ ] 是否传递 `quality_checks`。
- [ ] 是否传递 `freshness_expectation`。
- [ ] 是否传递 `permission_boundary`。
- [ ] 是否传递 `safety_boundary`。

验收结论：

- 通过条件：`query_intent` 的关键字段没有在 request 转换中丢失。
- 不通过处理：修正 adapter 字段映射。

## 3. normalized_evidence 结构完整性

验收项：

- [ ] 是否包含 `evidence_id`。
- [ ] 是否包含 `source_query_intent_id`。
- [ ] 是否包含 `source_dataagent_request_id`。
- [ ] 是否包含 `status`。
- [ ] 是否包含 `evidence_type`。
- [ ] 是否包含 `applicable_skill`。
- [ ] 是否包含 `evidence_summary`。
- [ ] 是否包含 `key_findings`。
- [ ] 是否包含 `strong_evidence`、`medium_evidence`、`weak_evidence`。
- [ ] 是否包含 `counter_evidence`。
- [ ] 是否包含 `missing_evidence`。
- [ ] 是否包含 `quality_risks`。
- [ ] 是否包含 `freshness_notes`。
- [ ] 是否包含 `permission_notes`。
- [ ] 是否包含 `conclusion_support.level` 和 `conclusion_support.reason`。
- [ ] 是否包含 `next_query_intent`。
- [ ] 是否包含 `manual_review_required`。
- [ ] 是否包含 `raw_result_reference`，且不外泄敏感明细。

验收结论：

- 通过条件：能表达强/中/弱证据、反证、缺失证据、质量风险和结论支持等级。
- 不通过处理：修正 `normalized_evidence_schema_v1.md` 或 adapter normalization。

## 4. error/degrade policy 覆盖

必须覆盖以下状态：

- [ ] `partial`
- [ ] `failed`
- [ ] `no_permission`
- [ ] `timeout`
- [ ] `empty_result`
- [ ] `ambiguous_result`

降级要求：

- [ ] `partial`：不得明确判断，必须列缺失证据。
- [ ] `failed`：不得形成风险证据，必须输出失败原因和下一步。
- [ ] `no_permission`：不得解释为无风险，必须保留重放。
- [ ] `timeout`：不得解释为无异常，必须支持缩小范围或异步重试。
- [ ] `empty_result`：不得直接解释为无风险，必须校验权限、时间窗口、口径和数据质量。
- [ ] `ambiguous_result`：不得强结论，必须列竞争解释和下一步补证。

验收结论：

- 通过条件：所有异常状态均能降级，并禁止自动处罚、冻结、扣除、策略上线。

## 5. 是否防止“前端无日志直接判协议”

验收项：

- [ ] 是否明确“前端无日志”只能作为弱信号或补证触发。
- [ ] 是否要求结合后端请求、SDK 覆盖、请求环境一致性和接口序列。
- [ ] 是否要求排除埋点缺失、SDK 延迟、官方包问题和 join 口径问题。
- [ ] 是否要求排除破解包绕采集。
- [ ] 是否要求排除合法自动化或授权工具。
- [ ] 是否禁止因前端无日志直接拦截、处罚或上线协议策略。

验收结论：

- 通过条件：任何单独“前端无日志”场景最多输出 `证据不足`。

## 6. 反证覆盖

必须覆盖以下反证 / 转交路径：

- [ ] 破解包 / SDK 绕采集。
- [ ] 官方包埋点缺失。
- [ ] 前后端 join 口径问题。
- [ ] 合法自动化 / 授权工具。
- [ ] 群控真机可能性。

验收要求：

- [ ] 每个反证都有对应下一步 `query_intent` 或人工补证动作。
- [ ] 每个反证未闭合时，结论不得为 `明确协议`。
- [ ] 反证成立时，应能转其他 Skill 或数据质量修复流程。

## 7. 四档结论等级

结论等级必须明确：

- [ ] 明确协议。
- [ ] 高度疑似协议。
- [ ] 证据不足。
- [ ] 反向排除 / 转其他 Skill。

升级条件：

- [ ] 明确协议：无正常端链路、接口序列固化、SDK/token/device/ip/ua 异常闭合，且关键反证已排除。
- [ ] 高度疑似协议：链路冲突和请求异常明显，但仍缺少一到两个闭环证据。
- [ ] 证据不足：只有前端无日志、高频请求、后端请求上涨，或存在 partial/no_permission/empty_result/failed/timeout。
- [ ] 反向排除 / 转其他 Skill：破解包、官方包埋点、合法自动化、群控真机或 token 泄露更能解释。

## 8. 人工确认边界

必须人工确认：

- [ ] 策略上线。
- [ ] 策略扩量。
- [ ] 处罚。
- [ ] 冻结。
- [ ] 扣除。
- [ ] 封禁。
- [ ] 大规模限权。
- [ ] 影响商家、达人、MCN、机构、客服或授权工具的治理动作。

试点允许：

- [ ] 补证。
- [ ] 证据解释。
- [ ] 结论等级判断。
- [ ] 下一步补证建议。
- [ ] 治理建议草案。

试点禁止：

- [ ] 自动处置。
- [ ] 自动处罚。
- [ ] 自动扣除。
- [ ] 自动策略上线。

## 9. 审计与回放字段

必须记录：

- [ ] 用户问题。
- [ ] Skill 路由。
- [ ] `query_intent`。
- [ ] `dataagent_request`。
- [ ] `dataagent_response` 摘要。
- [ ] `normalized_evidence`。
- [ ] Dennis 结论。
- [ ] 人工最终判断。
- [ ] 是否回写 schema / join path / Skill。
- [ ] 权限风险。
- [ ] 数据质量风险。
- [ ] 是否触发人工确认。

必须支持回放：

- [ ] 权限补齐后重放。
- [ ] 数据质量修复后重放。
- [ ] 前后端 join 口径修复后重放。
- [ ] SDK 采集延迟修复后重放。
- [ ] schema / join path / threshold 升级后重放。

## 10. 内部平台接入前还需补充的真实信息

以下信息需由未来内部平台补充，本清单不编造：

- [ ] Data Agent 真实调用方式、认证和权限校验机制。
- [ ] `dataagent_request` 到真实平台请求的映射。
- [ ] 抽象数据域到真实数据资产的映射。
- [ ] 抽象字段类型到真实字段的映射。
- [ ] 抽象 join path 到真实 join key / join 逻辑的映射。
- [ ] 数据权限边界和审批流程。
- [ ] 数据脱敏、审计、留存和访问控制规则。
- [ ] `raw_result_reference` 的真实引用和回放机制。
- [ ] Data Agent 返回状态和错误码的真实枚举。
- [ ] 只读试点的可观测指标和验收样本池。

## 11. 是否可以进入只读试点

只读试点准入条件：

- [ ] query_intent 结构完整。
- [ ] dataagent_request 结构完整。
- [ ] normalized_evidence 结构完整。
- [ ] partial / failed / no_permission / timeout / empty_result / ambiguous_result 均有降级策略。
- [ ] “前端无日志直接判协议”被明确禁止。
- [ ] 破解包、官方包埋点、join 口径、合法自动化、群控真机反证均覆盖。
- [ ] 四档结论等级明确。
- [ ] 人工确认边界明确。
- [ ] 审计与回放字段明确。
- [ ] 内部平台真实映射待补项已列清。

建议判定：

```text
当前文档层设计：可以进入只读试点准备。
试点性质：只读补证与研判，不做自动处置。
进入真实平台前置条件：补齐真实权限、真实数据资产映射、真实字段映射、真实 join 逻辑、真实 Data Agent 调用方式和审计回放能力。
```
