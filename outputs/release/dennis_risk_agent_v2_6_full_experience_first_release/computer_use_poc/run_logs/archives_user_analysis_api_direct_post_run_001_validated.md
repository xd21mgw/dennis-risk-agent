# 档案中心用户分析 API direct POST Run 001

## 1. 测试目标

验证档案中心“用户分析 / APP端核心操作日志”背后的 API direct POST 能否在已登录档案中心 browser session 内通过 same-origin fetch 直接读取，并替代 DOM selector 生成 `risk_event_scan`。

本 run log 仅沉淀内部 Agent 真实试跑结果。Codex 未访问内部平台。

## 2. 执行摘要

```yaml
run_id: archives_user_analysis_api_direct_post_run_001_validated
test_stage: v2.4.7.1
capability: user_analysis_core_logs_api
platform: archives_center
module: user_analysis_tab_app_core_operation_logs
endpoint: /v3/user/log/coreLogs/fetch
method: POST
execution_mode: api_direct_post_poc
actual_duration: ~3min
browser_session_used: true
same_origin_fetch: true
auth_exported: false
csrf_required: false
readonly_safety_check: PASSED
validation_result: passed
```

## 3. 验证结果

```yaml
api_direct_post_result:
  response_json_returned: true
  response_shape_detected: true
  data_totalCount_present: true
  data_dataList_present: true
  record_fields_match_dom_table_columns: true
  api_is_dom_table_data_source: true
  risk_event_scan_generated: true
```

## 4. 分页验证

```yaml
pagination:
  pagination_supported: true
  page_index_field: pageIndex
  page_size_field: pageSize
  total_count: 5
  page1_success: true
  page1:
    pageIndex: 1
    pageSize: 30
    dataList_length: 5
  page2_tested: true
  page2:
    pageIndex: 2
    dataList_length: 0
    totalCount: 5
  has_more: false
```

## 5. 响应字段

```yaml
top_level_fields:
  - result
  - currentTime
  - data
  - costTime
  - port
  - clientIp
  - host
  - message
data_fields:
  - totalCount
  - dataList
record_fields:
  - operateUri
  - time
  - operateType
  - operateResult
  - appVersion
  - userIpDesc
  - deviceId
  - photoInfo
  - requestParam
  - extraParam
```

## 6. 敏感字段策略

```yaml
sensitive_json_policy:
  requestParam_contains_sensitive_client_fingerprint: true
  extraParam_contains_sensitive_client_fingerprint: true
  extraParam_token_or_tokenId_visible: true
  requestParam_may_contain:
    - open_id
    - sig
    - refresh_token
    - egid
  raw_sensitive_value_output: false
  full_requestParam_persisted: false
  full_extraParam_persisted: false
  full_response_json_persisted: false
  credential_raw_value_output: false
```

本 run log 不记录真实 user_id、IP、deviceId、open_id、sig、token、tokenId、refresh_token、requestParam、extraParam、cookie、session、KIM code。

只记录字段名、字段存在性、计数、分布和派生特征。

## 7. 与 DOM 提取关系

```yaml
extraction_priority:
  default_priority_path: api_direct_post
  fallback_1: dom_scoped_js_eval
  fallback_2: row_feature_filter
  fallback_3: scoped_snapshot
dom_selector_risk_reduced:
  selector_noise: avoided
  dom_duplicate_rendering: avoided
  virtual_table_interference: avoided
```

## 8. 当前结论

```yaml
validation_status: archives_user_analysis_api_direct_post_validated
focused_login_risk_priority_path: api_direct_post
dom_extraction_fallback: available
core_skill_modified: false
release_package_updated: false
dataagent_boundary_changed: false
```
