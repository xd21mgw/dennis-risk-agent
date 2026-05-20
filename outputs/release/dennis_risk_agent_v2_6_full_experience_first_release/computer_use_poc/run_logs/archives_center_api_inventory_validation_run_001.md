# Archives Center API Inventory Validation Run 001

```yaml
run_id: archives_center_api_inventory_validation_run_001
test_stage: v2.4.7.2
platform: archives_center
execution_mode: api_inventory_validation_poc
validation_status: api_inventory_validation_passed

candidate_api_count: 28
success_count: 24
failed_count: 3
partial_count: 5

auth_exported: false
sensitive_raw_values_output: false
write_operation_called: false
batch_full_crawl: false
risk_classification_generated: false
readonly_safety_check: PASSED
```

## 1. 测试目标

验证档案中心除已验证「用户分析 / APP端核心操作日志」`/v3/user/log/coreLogs/fetch` 外的核心候选 API，判断哪些接口可以在已登录档案中心 browser session 中作为 API direct read 路径替代 DOM / selector 读取。

本轮只做 API inventory validation，不做风险定性，不做批量全量抓取，不导出认证态。

## 2. 已验证可完整替代 DOM 的接口

### 用户信息首页

```yaml
home_info:
  - method: GET
    endpoint: /archives/user/home/info
    validation_status: validated
    api_can_replace_dom: true
```

### 负向 / 标签 / 风险 / 处罚状态

```yaml
negative_label_risk_punish:
  - method: POST
    endpoint: /v3/user/negative/report
    validation_status: validated
    api_can_replace_dom: true
  - method: POST
    endpoint: /v3/user/negative/unInterested
    validation_status: validated
    api_can_replace_dom: true
  - method: GET
    endpoint: /v3/user/risk/info
    validation_status: validated
    api_can_replace_dom: true
  - method: POST
    endpoint: /archives/user/home/getUserLabel
    validation_status: validated
    api_can_replace_dom: true
  - method: GET
    endpoint: /archives/user/home/getUserShopInfo
    validation_status: validated
    api_can_replace_dom: true
  - method: POST
    endpoint: /archives/draco/getPunishStatus
    validation_status: validated
    api_can_replace_dom: true
```

### 审核日志新版

```yaml
review_log:
  - method: POST
    endpoint: /v3/user/log/reviewLogs/fetch
    validation_status: validated
    api_can_replace_dom: true
```

### 用户分析统计矩阵

```yaml
user_analyze_summary:
  - method: POST
    endpoint: /v3/user/analyze/fetch
    validation_status: validated
    api_can_replace_dom: true
```

### 视频作品集 / 视频详情

```yaml
photo_gallery_and_detail:
  - method: POST
    endpoint: /v3/user/gallery/photo/top
    validation_status: validated
    api_can_replace_dom: true
  - method: POST
    endpoint: /v3/user/gallery/photo/list
    validation_status: validated
    api_can_replace_dom: true
    pagination: pageIndex/pageSize/totalCount
  - method: POST
    endpoint: /v3/photo/profile
    validation_status: validated
    api_can_replace_dom: true
  - method: POST
    endpoint: /v3/photo/meta
    validation_status: validated
    api_can_replace_dom: true
  - method: POST
    endpoint: /v3/photo/report/aggregate
    validation_status: validated
    api_can_replace_dom: true
  - method: POST
    endpoint: /archives/photo/home/userAutonomy
    validation_status: validated
    api_can_replace_dom: true
```

### 直播作品集

```yaml
live_gallery:
  - method: POST
    endpoint: /v4/archives/gallery/live/list
    validation_status: validated
    api_can_replace_dom: true
    pagination: page/count/total
```

### 粉丝 / 关注

```yaml
relations:
  - method: POST
    endpoint: /v3/user/profile/relation/fans/list
    validation_status: validated
    api_can_replace_dom: true
    pagination: pageIndex/pageSize/totalCount
  - method: POST
    endpoint: /v3/user/profile/relation/follow/list
    validation_status: validated
    api_can_replace_dom: true
    pagination: pageIndex/pageSize/totalCount
```

### 收藏 / 合集

```yaml
collect_and_collection:
  - method: POST
    endpoint: /v3/user/collect/photo/list
    validation_status: validated
    api_can_replace_dom: true
    pagination: page/count/totalCount
  - method: POST
    endpoint: /archives/photo/collection/getCollectionList
    validation_status: validated
    api_can_replace_dom: true
    pagination: page/size/totalCount
```

### 同设备关联用户

```yaml
same_device_users:
  - method: POST
    endpoint: /archives/user/search/device
    type: 0
    validation_status: partial
    api_success: true
    mapping_status: mapping_pending_validation
  - method: POST
    endpoint: /archives/user/search/device
    type: 1
    validation_status: partial
    api_success: true
    mapping_status: mapping_pending_validation
```

说明：same_device type=0/type=1 接口成功，但业务语义映射 pending，不能写死为同设备登录 / 同设备注册。

## 3. Partial 接口

```yaml
partial_apis:
  - endpoint: auditLogOptions / getLogOption
    validation_status: partial
    partial_scope: option_structure_only
    boundary: 只验证筛选项结构，非数据列表
  - endpoint: /v3/user/collect/music/searchOption
    method: GET
    validation_status: partial
    partial_scope: filter_option_structure_only
    boundary: 只验证筛选项，未验证实际数据列表
  - endpoint: /v3/user/collect/folder/searchOption
    method: GET
    validation_status: partial
    partial_scope: filter_option_structure_only
    boundary: 只验证筛选项，未验证实际数据列表
  - endpoint: /archives/user/search/device
    method: POST
    type: 0
    validation_status: partial
    partial_scope: api_success_but_business_mapping_pending
  - endpoint: /archives/user/search/device
    method: POST
    type: 1
    validation_status: partial
    partial_scope: api_success_but_business_mapping_pending
```

## 4. 失败接口

```yaml
failed_apis:
  - method: POST
    endpoint: /archives/user/home/auditLog
    failure_reason: needs_punishId_or_required_param
    boundary: 单 userId 不足
  - method: POST
    endpoint: /archives/draco/getLabelLog
    failure_reason: needs_punishId_or_required_param
    boundary: 单 userId 不足
  - method: GET
    endpoint: /archives/report/countFlatted
    failure_reason: result_500_or_extra_param_required
    boundary: 可能需要额外参数或权限
```

失败接口不得写成可用；partial 接口不得写成 fully validated。

## 5. 分页支持验证

```yaml
pagination_validated:
  - endpoint: /v3/user/gallery/photo/list
    fields: pageIndex/pageSize/totalCount
  - endpoint: /v4/archives/gallery/live/list
    fields: page/count/total
  - endpoint: /v3/user/profile/relation/fans/list
    fields: pageIndex/pageSize/totalCount
  - endpoint: /v3/user/profile/relation/follow/list
    fields: pageIndex/pageSize/totalCount
  - endpoint: /v3/user/collect/photo/list
    fields: page/count/totalCount
  - endpoint: /archives/photo/collection/getCollectionList
    fields: page/size/totalCount
```

分页 guardrail：

- 未覆盖全部分页前必须标记 `partial_coverage=true`。
- 本轮不做批量全量抓取。
- API 可分页不代表允许默认拉全量。

## 6. 安全边界

本轮未输出：

- 手机号明文。
- IP 明文。
- deviceId 明文。
- open_id 明文。
- sig 明文。
- token / tokenId / refresh_token 明文。
- 完整 `requestParam`。
- 完整 `extraParam`。
- 完整 response JSON。
- 关联用户 ID / 昵称 / device 明文。
- cookie / session / KIM code / authorization。

只允许沉淀字段名、计数、分布、状态、分页 profile、validation status、派生特征和 redaction 标记。

## 7. 当前结论

档案中心核心 API inventory validation 通过。

```yaml
validation_result: passed
recommended_status: v2.4.7.2 archives center API inventory validation passed
default_read_strategy:
  - API direct read
  - DOM scoped JS eval fallback
  - row feature filter fallback
  - scoped snapshot fallback
```

该结论不代表：

- 自动风险定性完成。
- 多平台联合完成。
- 失败接口可用。
- partial 接口 fully validated。
- same_device type 业务语义已确定。
- 允许批量全量抓取。
