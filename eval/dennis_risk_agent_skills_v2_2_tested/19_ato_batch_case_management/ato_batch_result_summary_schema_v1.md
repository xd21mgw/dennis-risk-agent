# ATO Batch Result Summary Schema v1

## 1. 目标

定义每个 ATO batch case 完成取证后的标准结果摘要，方便批量横向比较、人工复核、长期回归筛选和后续能力沉淀。

## 2. 标准结果摘要

```yaml
ato_case_result_summary:
  case_id:
  batch_id:
  execution_status:
  dataagent_provider_status:
  sql_execution_summary:
    total_sql_count:
    success_count:
    empty_result_count:
    pending_count:
    failed_count:
    no_permission_count:
    permission_trimmed_fields:
  data_findings:
  speculation_notes:
  strong_evidence:
  medium_evidence:
  weak_evidence:
  counter_evidence:
  missing_evidence:
  permission_notes:
  quality_risks:
  provider_limitations:
  provider_conclusion_hint:
  conclusion_support:
    level:
    reason:
    boundary:
  dennis_agent_interpretation:
    current_max_conclusion:
    why_not_final_manual_judgement:
    next_action:
  manual_review:
    manual_review_required:
    review_focus:
    human_final_judgement:
  regression_metadata:
    regression_candidate:
    regression_type:
    must_have:
    must_not:
    evidence_snapshot_path:
```

## 3. 结论等级

| level | 含义 | 使用边界 |
|---|---|---|
| `data_supports_ato_suspicion` | 数据支持 ATO / 账号接管嫌疑 | 不是最终人工盗号定性 |
| `partial_support` | 局部支持，但链路未闭合 | 必须列缺口 |
| `insufficient_support` | 证据不足 | 不能强判，也不能反向断言无风险 |
| `data_does_not_support_ato` | 数据不支持 ATO | 仅在正常行为链路较完整且关键反证充分时使用 |
| `not_evaluated` | 未进入 evidence | SQL-only、pending、blocked 时使用 |

## 4. 证据摘要写法

强证据应满足：
- 来自执行结果或明确聚合摘要。
- 能闭合 ATO 关键链路的一部分。
- 与反证和质量风险共同解释。

弱证据包括：
- 用户申诉文本。
- 人工备注。
- 未被数据验证的来源线索。
- SQL 生成计划。
- 只有发布行为但无登录态接管链路。

反证必须保留：
- 登录环境与历史一致。
- 无 OAuth / 扫码 / token/session 接管。
- 无换绑 / 改密 / 找回。
- 无盗号 / 钓鱼 / 密码泄露 / 短信泄露标签。
- 疑点可被本人行为解释。

## 5. 样例摘要

### ATO_CASE_001_PASSWORD_KPN_RESWEEP

```yaml
case_id: ATO_CASE_001_PASSWORD_KPN_RESWEEP
execution_status: evidence_ready
conclusion_support:
  level: data_supports_ato_suspicion
  reason: 密码登录、新设备、风控命中、异常登录后发布行为和登录发布链路共同支持账号接管嫌疑。
  boundary: KPN / 已回扫是人工备注，不是数据事实；内容和部分策略参数存在权限缺口。
regression_type: positive_password_takeover
```

### ATO_CASE_003_QR_SCAN_GROUND_PROMO_RESWEEP

```yaml
case_id: ATO_CASE_003_QR_SCAN_GROUND_PROMO_RESWEEP
execution_status: evidence_ready
conclusion_support:
  level: data_supports_ato_suspicion
  reason: OAuth/扫码授权、Web 新设备、Token 生成、stealAccount 策略命中、发布设备一致和发布后删除共同支持扫码/OAuth 型账号接管嫌疑。
  boundary: 山东德州和已回扫未被离线表验证；发布内容与实时扫码流程仍缺失。
regression_type: positive_qr_oauth_takeover
```

### ATO_CASE_006_UNCERTAIN_NO_CLEAR_EVIDENCE

```yaml
case_id: ATO_CASE_006_UNCERTAIN_NO_CLEAR_EVIDENCE
execution_status: evidence_ready
conclusion_support:
  level: insufficient_support
  reason: 无异常登录、无 OAuth/扫码、无 token/session 接管、无盗号标签；存在疑点但可被正常行为解释。
  boundary: 无登录记录不能解释为无风险；仍需实时链路和人工复核。
regression_type: negative_or_insufficient_support
```

## 6. 禁止行为

- 禁止把 `provider_conclusion_hint` 写成最终人工定性。
- 禁止因为 SQL 执行完成就自动关闭 case。
- 禁止丢弃反证、权限限制和质量风险。
- 禁止输出处罚、冻结、封禁、扣除或策略上线建议。
