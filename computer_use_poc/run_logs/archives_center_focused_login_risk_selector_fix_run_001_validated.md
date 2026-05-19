# Archives Center Focused Login Risk Selector Fix Run 001

## 1. 测试目标

验证档案中心 `focused_login_risk` 模式下，用户分析 Tab 的 `risk_event_scan` 是否可以通过 row feature filter 修正 selector noise，并稳定生成只读、脱敏的派生摘要。

## 2. 执行摘要

```yaml
execution_mode: focused_login_risk
scan_type: risk_event_scan_selector_fix
actual_duration: 63s
table_structure: ks-table__row
extraction_method: row_feature_filter
active_tab_container_used: false
row_feature_filter_used: true
selector_noise_present: false
selector_noise_mitigation: row feature filter
raw_mixed_rows: 32
filtered_log_candidate_rows: 10
deduped_log_rows: 5
risk_event_scan:
  status: validated
readonly_safety_check: PASSED
```

## 3. 关键发现

1. active tab container 定位失败，因为档案中心不使用标准 `aria-selected` / `tabpanel` 结构。
2. row feature filter fallback 有效。
3. row feature filter 通过时间格式、`/rest/` URL、操作类型、操作结果、APP 版本 / IP / 设备字段等特征保留日志行。
4. 已成功排除用户信息 Tab 的平台操作、直播功能、电商功能、行为封禁、流量调控、账户信息等非日志表格行。
5. DOM 中同一日志行可能重复渲染，需要 dedupe。

## 4. 敏感字段策略

本轮符合敏感字段三层策略：

- 执行态可读 IP、设备、手机号、open_id、APP 版本、地理位置等字段，用于生成派生特征。
- 不输出 IP、设备 ID、手机号、open_id、token、请求参数、cookie、session、KIM code、操作者身份等敏感明文。
- 事件序列只保留派生摘要，不输出敏感原文。

## 5. 当前结论

```yaml
current_status: validated
validated_scope: focused_login_risk risk_event_scan selector fix
automatic_risk_judgement_completed: false
```

本轮可标记为 `focused_login_risk risk_event_scan validated`。

边界：

- 只代表档案中心 `userId` direct URL 下的只读派生观察能力已验证。
- 不代表自动风险定性完成。
- 不代表多平台、多入口或二级链接能力已验证。

## 6. 下一步

将 dedupe 逻辑内置到 eval 脚本中：

- 在 row feature filter 后计算 dedupe key。
- 记录 raw candidate rows、filtered rows、deduped rows。
- 将重复原因写入 `dedupe_policy.duplicate_reason`。

