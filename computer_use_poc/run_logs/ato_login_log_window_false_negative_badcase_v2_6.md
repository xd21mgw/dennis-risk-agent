# ATO Login Log Online Window False Negative Bad Case v2.6

## 1. Bad Case Background

```yaml
case_name: ato_login_log_online_window_false_negative
user_id: "290534602"
suspicious_event_time: "2026-05-12"
query_time: "2026-05-20"
domain: account_security
risk_type: ATO / abnormal_publish / possible_phishing_link
real_platform_query_by_codex: false
new_platform_hand_added: false
real_read_logic_changed: false
release_package_updated: false
```

用户描述：

- 前几天发现账号莫名发布作品，用户删除并联系工作人员。
- 用户查看登录设备显示只有本人登录。
- 之后账号因发布色情视频被封。
- 用户回忆曾在浏览器访问过“快手助力成功”链接。

内部 Agent 按 ATO 流程只读研判时，统一登录日志在线 API 查询 5/10~5/13，仅返回少量 token 刷新记录，并把“5/12 异常发布当天零登录记录 / 无异设备登录”写成反证或降级因素。

用户指出：统一登录日志在线 API 只有约 7 天窗口，5/12 已超出在线窗口；离线 Hive 中实际存在 5/12 登录数据。

## 2. Wrong Output Pattern

错误表达：

- “异常发布当天零登录记录。”
- “无异设备登录，因此不像盗号。”
- “登录设备只有本人，排除 ATO。”
- “在线 API 没有 LOGIN 事件，因此 data_does_not_support_ato。”

问题：

- 在线统一登录日志超过可靠窗口后可能缺失历史登录记录。
- API `no_data` / 少量 token 刷新 / 无 LOGIN 事件可能是假阴性。
- “用户设备页只有本人设备”也不能替代完整登录日志、发布审计和 token 链路。

## 3. Root Cause

```yaml
root_cause: online_login_log_reliable_window_limit
reliable_window_days: approximately_7_days
suspicious_event_out_of_window: true
online_login_log_may_be_false_negative: true
```

统一登录日志在线 API 存在时间窗口限制。超过在线可靠窗口的历史登录记录可能缺失，因此不能把在线 API 没查到登录行为当作强反证。

## 4. Correct Handling Rules

当 `suspicious_event_time` 超过统一登录日志在线可靠窗口时：

- 必须标记 `login_log_window_incomplete`。
- 必须标记 `offline_hive_required`。
- 必须标记 `online_login_log_may_be_false_negative`。
- 不允许输出“异常当天零登录记录”作为强反证。
- 不允许输出“无异设备登录”作为强反证。
- 不允许把“只有本人设备在线可见”直接当作强反证。
- ATO 结论最多为 `partial_support` 或 `insufficient_support`，除非补齐发布审计 / 离线登录日志 / token 使用链路。

## 5. Corrected Answer Wording

推荐表达：

```text
当前在线统一登录日志未观察到异常时间点的登录记录，但该异常时间已超过在线日志可靠窗口，因此该结果不能作为无异设备登录的强反证。

该窗口需要离线 Hive 登录日志或发布审计日志补证。

现有证据不足以闭合 ATO 链路，也不足以反向排除 ATO。

用户点击疑似助力链接 + 异常发布 + 在线日志窗口不完整，更适合标记为 partial_support，并优先补查发布审计与离线登录日志。
```

## 6. Follow-Up Evidence

优先补证：

1. 离线 Hive 登录日志。
2. 发布审计日志。
3. token 使用 / token 刷新 / passToken 相关链路。
4. 封禁 / 审核工单。

当前 Dennis Agent 默认不直接调用 DataAgent / Hive。本轮只标注：

```yaml
offline_hive_required: true
publish_audit_required: true
token_usage_required: true
```

## 7. Boundary

- 本 bad case 未确认盗号。
- 本 bad case 也不能被在线 API no_data 反向排除 ATO。
- 不新增平台手脚。
- 不修改真实读取逻辑。
- 不更新 release 包。
- 不更新 outputs/dist。
