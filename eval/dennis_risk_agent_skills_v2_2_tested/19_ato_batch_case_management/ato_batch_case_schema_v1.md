# ATO Batch Case Schema v1

## 1. 目标

本文件定义 ATO / 盗号申诉批量 case 的标准字段，用于把单 case Data Agent-only 试点升级为批量取证、状态跟踪、证据摘要和长期回归管理。

边界：
- 不调用 Data Agent。
- 不定义真实 API、真实表名、真实字段名或真实 SQL。
- 不把用户申诉、人工备注、Data Agent provider_conclusion_hint 当作最终事实。
- 不自动处罚、冻结、封禁、扣除或上线策略。

## 2. 标准 Case 对象

本轮最小闭环面向 5-20 个 ATO / 盗号申诉 case 的半自动归因，不依赖真实 DataAgent 或内部平台查询。标准字段优先服务 case 标准化、证据卡聚合、模式总结、缺口识别和策略方向建议。

### 2.1 最小闭环标准字段

| 字段 | 类型 | 是否必填 | 含义 | 边界 |
|---|---|---:|---|---|
| `case_id` | string | 是 | 批量 case 唯一标识 | 只作管理 ID，不代表风险结论 |
| `user_id` | string | 是 | 脱敏或受控用户实体 | 不输出真实敏感明文 |
| `device_id` | string | 否 | 脱敏或受控设备实体 | 可为空；缺失时进入 missing evidence |
| `event_time` | datetime/string | 是 | 用户申诉或人工记录中的异常时间 | 需要后续数据验证，不是事实结论 |
| `abnormal_action` | string | 是 | 异常动作，如发布、关注、换绑、改密、登录验证 | 只描述现象 |
| `user_claim` | string | 否 | 用户申诉摘要 | 弱证据或线索，不作为强证据 |
| `source_channel` | string | 否 | 来源渠道，如客服、申诉、人工抽样、历史回归 | 不代表可信等级 |
| `available_evidence` | list/string | 否 | 当前已有证据摘要 | 仅记录已知材料，不伪造查询结果 |
| `missing_evidence` | list/string | 否 | 仍缺的关键证据 | 用于后续补证计划 |
| `initial_risk_hint` | string | 否 | 初始风险线索，如疑似钓鱼、token 复用、OAuth 滥用 | 只是 hint，不是结论 |
| `current_status` | enum/string | 是 | 当前处理状态 | 见状态枚举 |
| `manual_label` | string | 否 | 人工标签或 golden hint | 不替代 Dennis 证据判断 |
| `confidence` | enum/string | 否 | 当前置信度 | 建议 low / medium / high / unknown |
| `notes` | string | 否 | 附加备注 | 不放敏感原文 |

最小闭环 YAML 形式：

```yaml
ato_batch_case_minimum:
  case_id:
  user_id:
  device_id:
  event_time:
  abnormal_action:
  user_claim:
  source_channel:
  available_evidence:
    - evidence_item:
  missing_evidence:
    - missing_item:
  initial_risk_hint:
  current_status:
  manual_label:
  confidence:
  notes:
```

### 2.2 扩展跟踪对象

以下对象保留早期 DataAgent-only 试点的扩展字段，用于需要更细状态管理、SQL 结果跟踪或长期回归时使用。当前最小闭环不要求填满这些字段。

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

最小闭环批量导入后至少需要：

- `case_id`
- `user_id`
- `event_time`
- `abnormal_action`
- `current_status`
- `user_claim`、`available_evidence`、`notes` 至少一个

缺 `user_id`、`event_time` 或 `abnormal_action` 时：
- `minimum_input_status = blocked_by_missing_input`
- 不生成事实查询计划
- 不进入 parser / evidence 阶段
- 不输出 ATO 结论

如需要进入早期 DataAgent-only 扩展跟踪，还需要：

- `sample_date`
- `time_window.start_time`
- `time_window.end_time`
- `business_scene`
- `target_api_or_action`

DataAgent 仍只作为 Hive / 数仓取数分析能力，不是默认万能数据底座。

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

- 批量分析当前是半自动归因，不是自动策略上线系统。
- 5-20 个 case 的聚合结论只能输出模式假设、缺口和候选策略方向，不能直接给自动处罚或上线结论。
- 单 case 的 evidence card 必须区分 strong / medium / weak / counter / missing evidence。
- 跨 case 聚集只能说明“相似模式”或“候选攻击路径”，不能直接等同黑产团伙或 ATO 已确认。
- 异常发布时间超过在线登录日志可靠窗口时，在线 no_data 只能作为数据缺口，不能作为“无异常登录”的强反证。
- SQL-only / pending_execution 只能进入 `evidence_plan`，不能进入强 / 中证据。
- running 的 SQL 不进入 evidence。
- no_permission / partial / empty_result / failed 必须降级。
- 人工备注和用户申诉只进入弱证据或线索区。
- Data Agent-only 只能说明离线数据发现，不覆盖实时登录链路、实时设备指纹、token/session 生命周期和在线关系图谱。
