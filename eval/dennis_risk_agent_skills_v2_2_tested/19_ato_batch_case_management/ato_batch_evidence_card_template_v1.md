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

## 3. Strong Evidence

强证据定义：命中后能明显区分 ATO / token 复用 / OAuth 滥用 / 新设备接管 / 本人操作等路径的证据。

| evidence | observed | supports | why_strong | boundary |
|---|---|---|---|---|
| 发布接口来源异常 | pending | token/OAuth/异地接管 | 可区分本人常用客户端 vs 异常 IP/UA/授权链路 | 需要发布审计确认 |
| token 使用链路异常 | pending | token/cookie 复用 | 可解释无新设备登录但发生发布 | API 直调不等于协议破解 |
| OAuth 新授权异常 | pending | OAuth 授权滥用 | 可区分普通登录态泄露和授权滥用 | 需要 scope、授权时间、使用链路 |

## 4. Medium Evidence

中证据定义：能增强判断，但不能单独定性。

| evidence | observed | supports | limitation |
|---|---|---|---|
| 登录失败后成功 | pending | 异常接管尝试 | 需确认设备/IP/时间一致性 |
| 设备环境异常 | pending | 设备侧风险补证 | 不能单独定性用户盗号 |
| 策略命中与异常时间接近 | pending | 风险链路一致 | 策略命中不等于最终作弊定性 |

## 5. Weak Evidence

弱证据定义：只能作为线索，不能单独影响结论。

| evidence | observed | why_weak |
|---|---|---|
| 用户申诉称非本人 | pending | 用户描述需要数据验证 |
| 人工备注疑似钓鱼 | pending | 备注不是事实证据 |
| 单次异地或单条异常 | pending | 缺上下文，误伤风险高 |

## 6. Counter Evidence

反证定义：支持正常、误伤或证据不足的材料。

| counter_evidence | observed | refutes_or_limits | boundary |
|---|---|---|---|
| 发布来源为常用设备和常用 IP | pending | 降低外部接管可能 | 仍需考虑本机被控 / 家庭共用 |
| 登录习惯连续稳定 | pending | 降低新设备盗号可能 | 超出在线日志窗口时不能作为强反证 |
| 无高危设备标签 | pending | 降低设备侧风险 | 字段缺失不等于无风险 |

## 7. Missing Evidence

| missing_item | why_needed | priority |
|---|---|---|
| 发布审计日志 | 判断具体发布来源 | P0 |
| token / refreshToken / passToken 使用链路 | 判断凭证复用 | P0 |
| OAuth / 第三方授权记录 | 判断授权滥用 | P1 |
| 离线 Hive 登录日志 | 在线登录日志超窗时补证 | P1 |
| 审核 / 封禁工单 | 区分发布原因与处置原因 | P2 |

## 8. Freshness Risk

- online_login_log_window_complete: true / false / unknown
- login_log_window_incomplete: true / false
- offline_hive_required: true / false
- event_time_outside_online_window: true / false
- note:

规则：异常时间超过在线登录日志可靠窗口时，no_data / 无 LOGIN 事件不能作为“无异常登录”的强反证。

## 9. Permission / Data Gap

| gap_type | status | handling |
|---|---|---|
| auth_blocked | pending | 进入缺口，不输出 no_data |
| permission_blocked | pending | 进入缺口，不输出无风险 |
| api_failed | pending | 进入缺口，保留重试建议 |
| partial_data | pending | 降级证据强度 |

## 10. Conclusion Support Level

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
