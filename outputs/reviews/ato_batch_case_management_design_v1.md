# ATO Batch Case Management Design v1

## 1. 本轮目标

本轮将 v2.4 ATO Data Agent-only pilot 从“单 case 试点”升级为“批量 ATO case 取证与回归管理”。

新增的是批量管理设计和模板，不调用 Data Agent，不新增真实 case，不修改核心 Skill。

## 2. 新增文件

| 文件 | 作用 |
|---|---|
| `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_case_schema_v1.md` | 定义批量 case 标准字段、枚举和证据边界 |
| `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_case_registry_template_v1.csv` | 批量 registry 模板，含 Case 001 / 003 / 006 示例行 |
| `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_case_import_rules_v1.md` | 定义从申诉 / 人工备注导入 case 的准入、清洗和去重规则 |
| `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_execution_status_tracker_v1.md` | 定义批量执行状态机和 SQL 级状态跟踪 |
| `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_result_summary_schema_v1.md` | 定义每个 case 最终证据摘要格式 |
| `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_sampling_strategy_v1.md` | 定义上百 case 的抽样策略 |
| `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/ato_batch_regression_selection_rules_v1.md` | 定义长期回归样例选择规则 |

## 3. 核心设计

批量链路：

```text
申诉 / 人工备注样本
→ case import
→ registry
→ minimum input validation
→ Data Agent question
→ SQL-only / execution status tracking
→ aggregate result summary
→ parser evidence
→ Dennis Agent interpretation
→ manual review
→ regression selection
```

## 4. 标准化内容

已标准化：

- 批量 case 字段。
- 最小输入校验。
- manual_note / user_claim_summary 的证据边界。
- SQL-only / pending_execution / execution_result_ready 状态。
- conclusion_support 枚举。
- result summary 输出结构。
- 上百 case 的抽样配比。
- 长期回归入选 / 退役规则。

## 5. Case 001 / 003 / 006 的使用方式

这 3 个既有真实 pilot case 作为模板和固定回归锚点：

| case_id | 角色 | 结论支持 |
|---|---|---|
| ATO_CASE_001_PASSWORD_KPN_RESWEEP | 密码登录型正例 | `data_supports_ato_suspicion` |
| ATO_CASE_003_QR_SCAN_GROUND_PROMO_RESWEEP | 扫码 / OAuth 型正例 | `data_supports_ato_suspicion` |
| ATO_CASE_006_UNCERTAIN_NO_CLEAR_EVIDENCE | 反例 / 证据不足 | `insufficient_support` |

它们用于：

- registry 示例行。
- 抽样 seed anchor。
- regression fixed cases。
- 证据边界和 must_not 校验。

## 6. 防误判规则

批量管理层继续保留 ATO pilot 的关键边界：

- 用户申诉不是事实。
- 人工备注是 golden hint，不是事实。
- SQL-only 是取证计划，不是证据。
- running / pending 不进入 evidence。
- no_permission / failed / timeout 必须降级。
- 无登录记录不能解释为无风险。
- 发布行为存在不等于 ATO 成立。
- 地区不一致不等于 ATO 成立。
- Data Agent provider_conclusion_hint 不等于最终人工定性。

## 7. 没有做什么

本轮没有：

- 调用 Data Agent。
- 新增或编造真实 case。
- 编造真实 API、表名、字段名或 SQL。
- 修改核心 Skill。
- 输出处罚、冻结、封禁、扣除或策略上线建议。

## 8. 后续建议

P0：
- 用 `ato_batch_case_registry_template_v1.csv` 承接第一批真实样本。
- 跑 import validation，先筛掉缺 user_id / time_window 的样本。
- 先选 20 个样本做批量试跑，其中必须包含正例、反例、权限边界和人工备注冲突样本。

P1：
- 将 SQL 执行状态自动沉淀到 tracker。
- 每个完成 case 生成 result summary。
- 从每轮结果中挑选长期回归样例。

P2：
- 当样本量超过 100 后，按 sampling_strategy 做分层抽样和回归集轮换。

## 9. 是否修改核心 Skill

未修改核心 Skill。本轮只新增批量管理设计文件和 review 文件。
