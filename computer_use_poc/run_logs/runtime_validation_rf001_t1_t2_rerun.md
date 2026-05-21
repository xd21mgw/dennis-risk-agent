# Runtime Validation RF-001 T1/T2 Rerun Summary

## 1. Execution Scope

- source: `internal_agent_returned_runtime_validation_summary`
- run_id: `runtime_validation_rf001_t1_t2_rerun`
- readonly_only: true
- dataagent_called: false
- real_platform_query_in_this_repo: false
- release_package_updated: false

本 run log 只同步真实 runtime wrapper 在补丁后的验证摘要，不在仓库中执行真实查询，不调用 DataAgent，不更新 release/dist。

## 2. RF-001 Fix Status

| item | status | note |
|---|---|---|
| `--from_timestamp` / `--to_timestamp` | fixed | 参数成对出现，支持 1-20 位纯数字毫秒时间戳 |
| 默认近 7 天窗口 | fixed | 未传 from/to 时使用近 7 天 reliable window |
| 时间窗口超限语义 | fixed | 标记 `over_reliable_window` / `login_log_window_incomplete` / `offline_hive_required` |
| user_login_unified_log URL 映射 | fixed | 有效 URL 补齐 `recallSource=2,0,1,3` |
| `code=10045` 误因归因 | fixed | 不再把缺失 recallSource 误判成单纯时间窗口问题 |

## 3. RF-001-b RecallSource Fix

真实 runtime 发现：

- `user_login_unified_log` 的 URL 必须包含 `recallSource=2,0,1,3`。
- 缺少该参数可能导致 API 返回 `code=10045`。
- 旧版 wrapper 的 URL 映射曾丢失该字段。
- 本轮真实 runtime 已补齐。

有效 URL 口径：

`https://user-center-workbench.corp.kuaishou.com/rest/unified/log/search?userId={USER_ID}&did=&query=&recallSource=2,0,1,3&from_timestamp={FROM_TS}&to_timestamp={TO_TS}`

## 4. T1 Rerun Result

- case: ATO 单 case readonly analysis
- status: PASS
- api_http_status: 200
- api_code: 0
- totalCount: 35
- api_full_result_loaded: true
- readonly_safety_check: passed
- dataagent_called: false

攻击链路摘要：

- quickLogin
- forceLogout
- byToken/logined 改密
- expireAllTokens
- 旧设备鉴权失败
- 风控踢登

说明：

- 已可构造完整 evidence card。
- 输出保持脱敏，不输出完整 IP / token / cookie / session。
- 不做处置。

## 5. T2 Rerun Result

- case: ATO batch summary
- status: PASS
- batch_level_summary: available
- dataagent_called: false
- auto_expansion: false

说明：

- 可基于已确认攻击模板输出 batch-level findings。
- 不自动扩量。
- 不调用 DataAgent。

## 6. Runtime Status Update

- RF-001: fixed
- RF-001-b recallSource missing: fixed
- T1: PASS / UNBLOCKED
- T2: PASS / UNBLOCKED
- next_validation_state: ready_for_next_semi_open_round

## 7. Safety Boundary

- `--target_url` 仍拒绝。
- 非法 `platform_key` 仍拒绝。
- `user_id` 注入仍拒绝。
- `from_timestamp` / `to_timestamp` 注入仍拒绝。
- 不输出 cookie / token / session / storageState / header。
- 不调用 DataAgent。
- 不做写操作。
- 不修改 release/dist。

## 8. Next Step

建议进入下一轮半开放测试，重点重跑：

- ATO 单 case readonly analysis。
- ATO batch summary。
- login_log 依赖链路场景的 end-to-end 只读验证。
- 继续确认缺少 `recallSource` 时的回归不再出现 `code=10045`。
