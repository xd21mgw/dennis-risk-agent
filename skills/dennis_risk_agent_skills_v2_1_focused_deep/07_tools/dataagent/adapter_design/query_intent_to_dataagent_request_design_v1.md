# Query Intent To DataAgent Request Design v1

## 0. 定位

本文件设计未来内部平台如何把 Dennis 风控 Agent 生成的 `query_intent_schema_v2` 转换为抽象 `dataagent_request`。

当前阶段：

- 不调用真实 Data Agent。
- 不定义真实 API、认证、接口路径或请求参数。
- 不编造真实表名、字段名、SQL、看板、数据集、实验或画像标签。
- 只定义未来 adapter 的字段映射、约束生成和返回类型预期。

## 1. 输入

输入为 `query_intent_schema_v2.md` 定义的标准对象：

```yaml
query_intent:
  intent_id:
  intent_type:
  risk_question:
  target_evidence:
  applicable_skill:
  minimum_inputs:
  required_data_domains:
  optional_data_domains:
  field_types_needed:
  join_paths_needed:
  query_dimensions:
  time_window:
  expected_outputs:
  quality_checks:
  freshness_expectation:
  permission_boundary:
  manual_review_required:
  safety_boundary:
  next_query_intent_when_insufficient:
```

## 2. 输出

输出为未来内部平台可消费的抽象请求对象：

```yaml
dataagent_request:
  request_id: "<adapter 生成的请求标识，不代表真实 API id>"
  source_query_intent_id: "<query_intent.intent_id>"
  task_type: "<见第 4 节>"
  natural_language_question: "<面向 Data Agent 的自然语言问题>"
  target_evidence: "<要补齐的风险证据>"
  data_domains:
    required:
      - "<required_data_domains>"
    optional:
      - "<optional_data_domains>"
  field_types_needed:
    identity_and_account: []
    device_and_network: []
    session_and_chain: []
    activity_and_channel: []
    risk_and_strategy: []
    relation_network: []
  join_paths_needed:
    - "<抽象 join path id>"
  time_window:
    baseline:
    observation:
    granularity:
  query_dimensions:
    entities: []
    group_by: []
    compare_with: []
    joins: []
  constraints:
    minimum_inputs:
      required: []
      optional: []
      missing: []
    no_real_table_or_field_names: true
    no_sql_execution_required_by_denisside: true
    must_return_quality_status: true
    must_return_missing_evidence: true
    must_return_counter_evidence: true
  expected_outputs:
    metric_outputs: []
    evidence_outputs: []
    quality_outputs: []
    returned_type_expected: []
  quality_checks:
    required: []
    downgrade_if: []
  freshness_expectation:
  permission_boundary:
  safety_boundary:
    false_positive_risks: []
    prohibited_actions: []
```

## 3. 字段映射关系

| query_intent 字段 | dataagent_request 字段 | 转换规则 |
|---|---|---|
| `intent_id` | `source_query_intent_id` | 原样传递 |
| `intent_type` | `task_type` | 先按第 4 节映射，无法确定时进入 `data_query` |
| `risk_question` | `natural_language_question` | 与目标证据、约束、反证要求合并生成 |
| `target_evidence` | `target_evidence` | 原样传递 |
| `applicable_skill` | `natural_language_question` / 审计字段 | 在问题中说明主控 Skill 和解释边界 |
| `minimum_inputs` | `constraints.minimum_inputs` | 原样传递，`missing` 不得由 adapter 自行假设 |
| `required_data_domains` | `data_domains.required` | 原样传递 |
| `optional_data_domains` | `data_domains.optional` | 原样传递 |
| `field_types_needed` | `field_types_needed` | 原样传递，只能是抽象字段类型 |
| `join_paths_needed` | `join_paths_needed` | 原样传递，只能是抽象 join path |
| `time_window` | `time_window` | 原样传递 |
| `query_dimensions` | `query_dimensions` | 原样传递，不写真 join key |
| `expected_outputs` | `expected_outputs` | 结构化拆分为 metric/evidence/quality 输出 |
| `quality_checks` | `quality_checks` | 原样传递，作为 Data Agent 返回质量状态的要求 |
| `freshness_expectation` | `freshness_expectation` | 原样传递，未来平台决定可满足程度 |
| `permission_boundary` | `permission_boundary` | 原样传递，未来平台做权限判断 |
| `safety_boundary` | `safety_boundary` | 原样传递，禁止自动处罚等动作 |

## 4. task_type 分类

`task_type` 是 adapter 给未来 Data Agent 的任务语义，不代表真实 API 名称。

必须支持：

- `data_query`：泛化取数、指标分布、趋势、样本摘要。
- `table_search`：按数据域或字段类型寻找候选数据资产。
- `table_summary`：解释候选数据资产的结构、口径、分区、血缘或质量限制。
- `dashboard_analysis`：分析看板、趋势、异常归因。
- `dataset_analysis`：分析数据集维度、占比、周同比、漏斗、归因等。
- `sql_generation`：生成抽象查询方案或未来 SQL 需求，不在 Dennis 侧执行。
- `sql_diagnosis`：解释或诊断用户提供的 SQL，不用于风控最终定性。
- `abtest_analysis`：分析实验组间差异、CUPED、DiD、推全风险、异常检测。
- `profile_tag_search`：检索画像标签、解释标签口径。
- `audience_package_design`：设计人群圈选条件或分群包需求。
- `permission_or_lineage_check`：检查权限、数据血缘、任务状态或数据质量风险。

推荐映射：

| intent_type | 默认 task_type | 说明 |
|---|---|---|
| `protocol_frontend_backend_join` | `data_query` | 需要前后端链路、SDK、请求环境联查 |
| `sdk_bypass_or_cracked_app_check` | `data_query` | 需要设备、SDK、版本/签名语义联查 |
| `group_control_dispatch_check` | `data_query` | 需要设备团组、行为路径、收益聚集 |
| `token_reuse_or_account_takeover_check` | `data_query` | 需要账号、token、设备、敏感动作 |
| `activity_black_industry_or_low_quality_check` | `dataset_analysis` | 需要活动参与、奖励、后验质量分析 |
| `channel_attribution_hijacking_check` | `dataset_analysis` | 需要渠道链路和后验分析 |
| `anti_crawler_asset_leakage_check` | `data_query` | 需要资产访问链路和主体聚集 |
| `traffic_diversion_chain_check` | `data_query` | 需要目标获取、触达、承接链路 |
| `legal_operation_matrix_check` | `data_query` | 需要授权主体、工具、范围、审计链路 |
| `strategy_effect_and_false_positive_review` | `dashboard_analysis` | 需要策略效果、误伤、业务指标 |
| `batch_case_commonality_check` | `dataset_analysis` | 需要批量样本共性和业务上下文 |
| 指标异常且包含 `metric_anomaly_business_context_join` | `dashboard_analysis` | 先做指标和业务上下文归因 |

若用户明确提供看板、数据集、AB、画像或权限问题，adapter 可覆盖默认映射为对应 task_type。

## 5. natural_language_question 生成规则

`natural_language_question` 面向 Data Agent，必须保留风险语义和证据边界。

生成模板：

```text
请基于以下抽象数据域和字段类型，验证风险问题：[risk_question]。
目标证据：[target_evidence]。
主控 Skill：[primary_skill]，辅助 Skill：[auxiliary_skills]。
请围绕 required_data_domains、field_types_needed、join_paths_needed 和 time_window 返回指标摘要、证据摘要、反证、缺失证据和质量风险。
不要直接给出风控最终定性，不要触发处罚、冻结、扣除或策略上线。
```

要求：

- 必须包含 `risk_question`。
- 必须包含 `target_evidence`。
- 必须明确“返回证据，不做最终风控定性”。
- 必须说明反证需求，例如埋点缺失、合法矩阵、业务活动、实验、版本、数据质量。
- 不得写真实表名、字段名、SQL 或 API。

## 6. constraints 生成规则

`constraints` 从 `minimum_inputs`、`quality_checks`、`safety_boundary` 和全局禁止行为生成。

固定约束：

- `no_real_table_or_field_names: true`
- `no_sql_execution_required_by_denisside: true`
- `must_return_quality_status: true`
- `must_return_missing_evidence: true`
- `must_return_counter_evidence: true`
- `must_not_make_final_risk_judgement: true`
- `must_not_trigger_governance_action: true`

动态约束：

- 若 `minimum_inputs.missing` 非空，要求返回 `missing_evidence`。
- 若 `quality_checks.downgrade_if` 包含权限、partial、failed，要求返回可执行降级原因。
- 若 `safety_boundary.prohibited_actions` 非空，原样传递给 Data Agent 和审计层。

## 7. expected_outputs 生成规则

`expected_outputs` 应由 `query_intent.expected_outputs` 和 `interpretation_notes` 合成。

必须要求返回：

- `metric_outputs`：指标、趋势、分布、比例、样本摘要。
- `evidence_outputs`：可支持强/中/弱证据和反证的摘要。
- `quality_outputs`：覆盖率、口径、延迟、权限、样本偏差。
- `missing_evidence`：当前无法返回或缺失的证据项。
- `returned_type_expected`：预期返回类型列表。

## 8. quality_checks 传递规则

`quality_checks.required` 和 `quality_checks.downgrade_if` 必须原样传递。

adapter 不解释质量规则，只要求 Data Agent 返回：

- 覆盖是否完整。
- 是否存在口径差异。
- 是否存在权限不足。
- 是否存在数据延迟或 SLA 风险。
- 是否存在样本偏差。
- 哪些质量风险会导致 Dennis Agent 降级结论。

## 9. freshness_expectation 传递规则

`freshness_expectation` 原样传递。未来平台应返回可满足程度：

- `matched`：满足预期。
- `weaker_than_expected`：只能返回更慢数据。
- `unknown`：无法判断。

若实际新鲜度弱于预期，normalized_evidence 必须记录 `freshness_notes`，结论不得强行升级。

## 10. permission_boundary 传递规则

`permission_boundary` 原样传递给未来平台。

adapter 不绕过权限，不申请权限，不导出敏感明细。未来平台应返回：

- `allowed`
- `permission_limited`
- `no_permission`
- `pending_approval`

权限不足不得被解释为无风险。

## 11. safety_boundary 传递规则

`safety_boundary.false_positive_risks` 和 `safety_boundary.prohibited_actions` 必须原样传递。

任何返回结果都不得自动触发：

- 处罚。
- 冻结。
- 扣除。
- 封禁。
- 策略上线。
- 批量人群处置。

## 12. 不同 returned_type 的预期

| returned_type | 预期内容 | Dennis 解释边界 |
|---|---|---|
| `sql` | 查询语义、候选查询计划或未来 SQL 草案 | 返回 SQL 不等于已经查到结果 |
| `table_summary` | 候选资产语义、字段类型、口径、质量限制 | 只能说明可能数据来源 |
| `dashboard_analysis` | 指标趋势、异常分解、业务上下文 | 看板趋势不等于风险事实 |
| `dataset_analysis` | 分布、占比、周同比、漏斗、后验质量 | 数据集结果需结合反证 |
| `abtest_analysis` | 实验组差异、方法、异常、推全风险 | 实验差异不等于攻击 |
| `profile_tags` | 标签口径、标签候选、适用边界 | 风险画像不等于事实标签 |
| `audience_package` | 人群圈选条件、范围、限制 | 不得直接用于处罚人群 |
| `error` | 失败原因 | 必须降级 |
| `partial` | 部分结果和缺失项 | 不得明确判断 |
| `no_permission` | 权限限制 | 不得解释为无风险 |

## 13. 不支持真实 API / 表名 / 字段名说明

本设计文件只定义 adapter 抽象：

- 不定义真实 Data Agent API。
- 不定义认证、URL、接口路径、参数名。
- 不定义真实数据表、真实字段、分区或 SQL。
- 不定义真实看板、实验、画像标签或人群包。
- 真实映射由未来内部平台在权限、审计和数据治理框架内补充。
