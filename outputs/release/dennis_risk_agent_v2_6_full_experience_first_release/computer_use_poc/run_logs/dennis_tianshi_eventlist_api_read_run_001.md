# Dennis 天狮 eventList API-read Run 001

## 1. 测试目标

验证内部 Agent 是否能在已认证 rcp 浏览器会话中，通过 `POST /v2/rest/event/eventList` 对指定 `sourceId`、指定 eventType、小时间窗口做请求级 / 事件级只读细查。

本 run log 仅沉淀内部 Agent 真实试跑结果。Codex 未访问内部平台。

## 2. 执行摘要

```yaml
run_id: dennis_tianshi_eventlist_api_read_run_001
version: v2.5.9
test_type: tianshi_eventlist_api_read_poc
platform: tianshi_strategy_platform_rcp
capability: tianshi_eventlist_api_read
endpoint: /v2/rest/event/eventList
method: POST
source_id: "2740906395"
execution_env: cloud_internal_agent
auth_status: success
rcp_browser_logged_in: true
logged_in_user: 沐广武
logged_in_user_policy: 本次执行样例，不作为固定规则
query_window:
  start: "2026-05-20 13:06:00"
  end: "2026-05-20 14:06:00"
  timezone: Asia/Shanghai
  cross_day: false
readonly_safety_check: PASSED
```

## 3. 查询 eventType

```yaml
queried_event_types:
  - eventType: LOGIN_AUDIT
    meaning: app 端登录同步
    result: no_record_in_window
  - eventType: ASYNC_LOGIN
    meaning: app 端登录异步
    result: no_record_in_window
  - eventType: USER_REGISTER_NEW
    meaning: 注册同步
    result: 1_record_found
  - eventType: REGISTER_NEW
    meaning: 注册异步
    result: no_record_in_window
```

## 4. 结果摘要

```yaml
result_summary:
  LOGIN_AUDIT: no_record_in_window
  ASYNC_LOGIN: no_record_in_window
  USER_REGISTER_NEW: 1 record found
  REGISTER_NEW: no_record_in_window
```

## 5. USER_REGISTER_NEW 记录摘要

```yaml
extracted_event_summary:
  eventType: USER_REGISTER_NEW
  sourceId: "2740906395"
  eventId: "-4316721556172421683"
  occur_time: 1779256198744
  occur_time_cst: "2026-05-20 13:49:58"
  table_time: 1779256199876
  real_time_op: 允许
  error_code: 1
  side_effect_ops:
    - 向kafka发送log[sendProtoLogToKafka]
  userRegisterIp: "1.194.128.243"
  ipCity: 空
  openId_present: false
  deviceSignal: 空
  interpretation: 同步注册事件，实时反馈允许，无实际惩罚动作，仅 kafka 日志
```

## 6. 与 fastQueryHbase 的关系

```yaml
comparison_with_fastQueryHbase:
  fastQueryHbase:
    purpose: 按 sourceId + 时间窗口快速判断是否存在策略命中
    evidence_type: 策略命中证据概览
  eventList:
    purpose: 围绕具体 eventType、小时间窗口、具体请求字段做明细细查
    evidence_type: 请求级 / 事件级补证
  default_order:
    - 只问是否命中生产策略时优先 fastQueryHbase
    - 需要解释请求字段、实时反馈、错误码或 side effect 时补 eventList
```

## 7. Blockers

```yaml
blockers: []
```

## 8. Limitations

```yaml
limitations:
  - eventList no_data 不代表用户无风险或行为未发生
  - 非命中策略事件存在抽样
  - 命中策略事件 100% 记录
  - 登录事件在该时段无记录，可能需要查询用户实际活跃时段
  - 本次测试为只读验证，未进行任何写操作或数据修改
  - logged_in_user 仅作为本次执行样例，不作为固定规则
  - 不保存或输出 cookie / token / 完整 header
```

## 9. 当前结论

```yaml
validation_status: tianshi_eventlist_api_read_validated
eventlist_post_accessible: true
request_level_observation_ready: true
core_skill_modified: false
release_package_updated: false
dataagent_hive_boundary_changed: false
```
