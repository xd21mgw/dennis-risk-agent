# ATO Batch Case Schema v1

## 1. 目标

本文件定义 ATO / 盗号申诉批量 case 的标准字段，用于把单 case Data Agent-only 试点升级为批量取证、状态跟踪、证据摘要和长期回归管理。

边界：
- 不调用 Data Agent。
- 不定义真实 API、真实表名、真实字段名或真实 SQL。
- 不把用户申诉、人工备注、Data Agent provider_conclusion_hint 当作最终事实。
- 不自动处罚、冻结、封禁、扣除或上线策略。

## 2. 标准 Case 对象

```yaml
ato_batch_case:
  batch_id:
  case_id:
  source_row_id:
  user_id:
  sample_date:
  suspicious_event_time:
  time_window:
    start_time:
    end_time:
    reason:
  business_scene:
  target_api_or_action:
  user_claim_summary:
  manual_label:
  risk_category:
  risk_subcategory:
  manual_note:
  expected_skill:
  minimum_input_status:
  execution_status:
  dataagent_question_reference:
  sql_execution:
    sql_ids:
    completed_sql_count:
    pending_sql_count:
    failed_sql_count:
    permission_trimmed:
  evidence_summary:
    conclusion_support:
    provider_conclusion_hint:
    strong_evidence_summary:
    medium_evidence_summary:
    weak_evidence_summary:
    counter_evidence_summary:
    missing_evidence_summary:
    permission_notes:
    quality_risks:
    provider_limitations:
  manual_review:
    manual_review_required:
    reviewer:
    review_status:
    human_final_judgement:
  regression_metadata:
    regression_candidate:
    regression_type:
    long_term_regression:
    selected_reason:
    priority:
```

## 3. 必填字段

批量导入后至少需要：

- `case_id`
- `user_id`
- `sample_date`
- `time_window.start_time`
- `time_window.end_time`
- `business_scene`
- `target_api_or_action`
- `user_claim_summary` 或 `manual_note` 至少一个

缺 `user_id` 或 `time_window` 时：
- `minimum_input_status = blocked_by_missing_input`
- 不生成可执行 Data Agent question
- 不进入 parser / evidence 阶段
- 不输出 ATO 结论

## 4. 字段说明

| 字段 | 含义 | 注意事项 |
|---|---|---|
| `batch_id` | 批次 ID | 例如 `ato_v2_4_real_pilot`，不代表风险结论 |
| `case_id` | 内部 case 唯一标识 | 可复用历史 ATO_CASE_* |
| `source_row_id` | 来源表 / 标注表行标识 | 可为空，不写真实表名 |
| `user_id` | 取证实体标识 | Data Agent-only 试点的最小输入之一 |
| `suspicious_event_time` | 用户申诉或人工备注中的异常时间 | 不是事实，需要数据验证 |
| `time_window` | 查询窗口 | 第一轮建议不超过 7 天 |
| `user_claim_summary` | 用户申诉摘要 | 只作为线索，不进入强证据 |
| `manual_label` | 人工标注 | golden hint，不是最终事实 |
| `manual_note` | 人工备注 | KPN、已回扫、地推、钓鱼域名等都必须被数据验证 |
| `target_api_or_action` | 目标动作集合 | 登录、授权、token/session、发布、换绑、改密、找回等 |
| `execution_status` | 执行状态 | 见状态枚举 |
| `conclusion_support` | 证据支持等级 | 由 Dennis Agent 基于 evidence 输出，不是人工最终定性 |
| `provider_conclusion_hint` | Data Agent 结论性提示 | 只能作为 provider hint，不能替代 Dennis 判断 |

## 5. 枚举

### 5.1 minimum_input_status

- `ready`
- `blocked_by_missing_user_id`
- `blocked_by_missing_time_window`
- `blocked_by_missing_business_context`
- `blocked_by_missing_target_action`

### 5.2 execution_status

- `imported`
- `minimum_input_ready`
- `blocked_by_missing_input`
- `question_ready`
- `dataagent_submitted`
- `sql_only`
- `pending_execution`
- `execution_in_progress`
- `execution_partial`
- `execution_result_ready`
- `evidence_ready`
- `no_permission`
- `failed`
- `timeout`
- `manual_review_required`
- `manual_review_done`
- `archived`

### 5.3 conclusion_support

- `not_evaluated`
- `data_supports_ato_suspicion`
- `partial_support`
- `insufficient_support`
- `data_does_not_support_ato`

### 5.4 regression_type

- `positive_password_takeover`
- `positive_qr_oauth_takeover`
- `negative_or_insufficient_support`
- `phishing_no_resweep`
- `sms_oauth_token`
- `member_phishing_sms_code`
- `token_session_takeover`
- `sql_only_boundary`
- `no_permission_boundary`
- `data_conflict_boundary`
- `unknown`

## 6. 证据边界

- SQL-only / pending_execution 只能进入 `evidence_plan`，不能进入强 / 中证据。
- running 的 SQL 不进入 evidence。
- no_permission / partial / empty_result / failed 必须降级。
- 人工备注和用户申诉只进入弱证据或线索区。
- Data Agent-only 只能说明离线数据发现，不覆盖实时登录链路、实时设备指纹、token/session 生命周期和在线关系图谱。
