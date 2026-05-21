# ATO Batch Evidence Card Template v1

## 1. 定位

本模板用于单个 ATO / 盗号申诉 case 的证据卡生成。证据卡只表达证据支持程度，不输出最终事实定性，不触发处置。

## 2. Case Summary

| 字段 | 内容 |
|---|---|
| case_id |  |
| user_id |  |
| device_id |  |
| event_time |  |
| abnormal_action |  |
| user_claim |  |
| source_channel |  |
| initial_risk_hint |  |
| current_status |  |

## 3. Evidence Source Metadata

每条证据都必须记录来源。没有来源追踪的内容只能作为线索或 model inference，不能作为 strong evidence。

source_type 枚举建议：

- `internal_platform_api`
- `browser_dom_read`
- `screenshot_manual_read`
- `dataagent_hive`
- `manual_input`
- `model_inference`
- `historical_doc`

### 3.1 evidence_source

| 字段 | 内容 |
|---|---|
| source_name |  |
| source_type | internal_platform_api / browser_dom_read / screenshot_manual_read / dataagent_hive / manual_input / model_inference / historical_doc |
| source_tool_or_hand |  |
| source_platform |  |
| collected_at |  |
| evidence_time_range |  |
| raw_reference | internal_safe_reference_only |

### 3.2 source_quality

| 字段 | 内容 |
|---|---|
| freshness_status | fresh / stale / over_reliable_window / unknown |
| freshness_risk | none / low / medium / high |
| permission_status | success / partial / permission_blocked / auth_blocked / unknown |
| reliability_level | high / medium / low / model_inference_only |

### 3.3 normalized_evidence source trace

```yaml
normalized_evidence:
  - evidence_id:
    evidence_name:
    evidence_value:
    evidence_strength:
    source_query_intent_id:
    source_dataagent_request_id:
    source_name:
    source_type:
    source_tool_or_hand:
    source_platform:
    collected_at:
    evidence_time_range:
    raw_result_reference:
    freshness_notes:
    permission_notes:
```

边界：

- `model_inference` 不能当作原始证据。
- `manual_input` 不能单独支撑 strong conclusion。
- stale / partial / blocked source 必须在 evidence card 中显式可见。
- raw_reference / raw_result_reference 只能是内部安全引用，不得包含 cookie / token / session / header 或敏感原文。

## 4. Strong Evidence

强证据定义：命中后能明显区分 ATO / token 复用 / OAuth 滥用 / 新设备接管 / 本人操作等路径的证据。

| evidence | observed | supports | why_strong | evidence_source | source_quality | boundary |
|---|---|---|---|---|---|---|
| 发布接口来源异常 | pending | token/OAuth/异地接管 | 可区分本人常用客户端 vs 异常 IP/UA/授权链路 | source metadata required | source quality required | 需要发布审计确认 |
| token 使用链路异常 | pending | token/cookie 复用 | 可解释无新设备登录但发生发布 | source metadata required | source quality required | API 直调不等于协议破解 |
| OAuth 新授权异常 | pending | OAuth 授权滥用 | 可区分普通登录态泄露和授权滥用 | source metadata required | source quality required | 需要 scope、授权时间、使用链路 |

## 5. Medium Evidence

中证据定义：能增强判断，但不能单独定性。

| evidence | observed | supports | evidence_source | source_quality | limitation |
|---|---|---|---|---|---|
| 登录失败后成功 | pending | 异常接管尝试 | source metadata required | source quality required | 需确认设备/IP/时间一致性 |
| 设备环境异常 | pending | 设备侧风险补证 | source metadata required | source quality required | 不能单独定性用户盗号 |
| 策略命中与异常时间接近 | pending | 风险链路一致 | source metadata required | source quality required | 策略命中不等于最终作弊定性 |

## 6. Weak Evidence

弱证据定义：只能作为线索，不能单独影响结论。

| evidence | observed | evidence_source | source_quality | why_weak |
|---|---|---|---|---|
| 用户申诉称非本人 | pending | manual_input | low / manual_input_only | 用户描述需要数据验证 |
| 人工备注疑似钓鱼 | pending | manual_input | low / manual_input_only | 备注不是事实证据 |
| 单次异地或单条异常 | pending | source metadata required | source quality required | 缺上下文，误伤风险高 |

## 7. Counter Evidence

反证定义：支持正常、误伤或证据不足的材料。

| counter_evidence | observed | refutes_or_limits | evidence_source | source_quality | boundary |
|---|---|---|---|---|---|
| 发布来源为常用设备和常用 IP | pending | 降低外部接管可能 | source metadata required | source quality required | 仍需考虑本机被控 / 家庭共用 |
| 登录习惯连续稳定 | pending | 降低新设备盗号可能 | source metadata required | source quality required | 超出在线日志窗口时不能作为强反证 |
| 无高危设备标签 | pending | 降低设备侧风险 | source metadata required | source quality required | 字段缺失不等于无风险 |

## 8. Missing Evidence

| missing_item | why_needed | priority |
|---|---|---|
| 发布审计日志 | 判断具体发布来源 | P0 |
| token / refreshToken / passToken 使用链路 | 判断凭证复用 | P0 |
| OAuth / 第三方授权记录 | 判断授权滥用 | P1 |
| 离线 Hive 登录日志 | 在线登录日志超窗时补证 | P1 |
| 审核 / 封禁工单 | 区分发布原因与处置原因 | P2 |

## 9. Freshness Risk

- online_login_log_window_complete: true / false / unknown
- login_log_window_incomplete: true / false
- offline_hive_required: true / false
- event_time_outside_online_window: true / false
- note:

规则：异常时间超过在线登录日志可靠窗口时，no_data / 无 LOGIN 事件不能作为“无异常登录”的强反证。

## 10. Permission / Data Gap

| gap_type | status | handling |
|---|---|---|
| auth_blocked | pending | 进入缺口，不输出 no_data |
| permission_blocked | pending | 进入缺口，不输出无风险 |
| api_failed | pending | 进入缺口，保留重试建议 |
| partial_data | pending | 降级证据强度 |

## 11. Conclusion Support Level

可选值：

- strong_support
- partial_support
- insufficient_support
- counter_evidence_present
- not_evaluated

填写模板：

- conclusion_support_level:
- reason:
- key_supporting_evidence:
- key_counter_evidence:
- key_missing_evidence:
- manual_review_required: true

边界：该字段只表示“当前证据是否支持 ATO 假设”，不是“已确认盗号”。
