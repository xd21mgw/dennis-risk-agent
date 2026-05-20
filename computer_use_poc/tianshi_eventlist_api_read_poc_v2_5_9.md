# v2.5.9 天狮 eventList API-read 请求级细查手脚

## 1. 能力定位

`tianshi_eventlist_api_read` 是 Dennis Agent 的天狮策略平台 / rcp 请求级只读补证手脚。

它不是泛化的“大盘事件列表查询”，而是在已认证 rcp 浏览器会话中，通过 `POST /v2/rest/event/eventList` 对某个 `sourceId`、某类 `eventType`、较小时间窗口内的具体请求 / 具体事件进行细查。

适合回答的问题是：

- 某个具体注册 / 登录 / 风控事件在天狮侧有没有请求级记录。
- 某个 eventType 在小窗口内的实时反馈动作、错误码、副作用动作是什么。
- `fastQueryHbase` 已经给出策略命中概览，但还需要看请求字段明细。

本手脚仍然只读，不做策略配置变更、处置、审批、封禁、解封或自动风险定性。

## 2. 与 fastQueryHbase 的关系

| 能力 | 查询方式 | 主要作用 | 适用阶段 |
|---|---|---|---|
| `fastQueryHbase` | sourceId + 时间窗口 | 快速判断是否存在生产策略命中 | 策略命中证据概览 |
| `eventList` | sourceId + eventType + 小时间窗口 | 查看具体请求 / 事件字段、实时反馈、错误码、副作用动作 | 请求级 / 事件级补证 |
| 页面读取 | 浏览器页面只读 | API-read 不可用时兜底 | fallback |

默认顺序：

1. 用户只问“是否命中生产策略”时，优先 `fastQueryHbase`。
2. `fastQueryHbase` 不足以解释请求字段细节时，再补 `eventList API-read`。
3. 用户问“大范围统计、趋势、历史聚合”时，不使用 `eventList`，优先 DataAgent / Hive 或要求缩小窗口。

## 3. 适用场景

- 细查某次具体请求。
- 查看某个 eventType 明细。
- 查看注册事件字段。
- 查看登录事件字段。
- 查看实时反馈动作。
- 查看错误码、side effect、是否有实际惩罚动作。
- 对 `fastQueryHbase` 的命中概览做请求级补证。

## 4. 不适用场景

- 大盘事件列表查询。
- 大窗口历史全量统计。
- 趋势分析、分布统计、批量样本归因。
- 替代 DataAgent / Hive 做离线聚合。
- 替代用户登录统一日志、档案中心、前端埋点或设备 SDK。
- 只靠 eventList 输出最终风险定性。

## 5. 账号 eventType 枚举

同步事件：

| eventType | 含义 |
|---|---|
| `LOGIN_AUDIT` | app 端登录 |
| `LOGIN_AUDIT_FROM_WEB` | web 端登录 |
| `USER_REGISTER_NEW` | 所有注册 |

异步事件：

| eventType | 含义 |
|---|---|
| `ASYNC_LOGIN` | app 端登录 |
| `ASYNC_WEB_LOGIN` | web 端登录 |
| `REGISTER_NEW` | 所有注册 |

推荐组合：

| 用户问题 | 推荐 eventType |
|---|---|
| app 登录细查 | `LOGIN_AUDIT` + `ASYNC_LOGIN` |
| web 登录细查 | `LOGIN_AUDIT_FROM_WEB` + `ASYNC_WEB_LOGIN` |
| 注册细查 | `USER_REGISTER_NEW` + `REGISTER_NEW` |

## 6. 查询窗口规则

`eventList` 查询窗口原则上尽量小。

- 优先围绕已知事件时间点前后扩展，例如前后 5-15 分钟。
- 原则上不能跨天。
- 如果用户给的是“今天”，Dennis Agent 应先基于已有证据定位具体时间段，再发起 eventList 细查。
- 不建议直接从 00:00 查到当前时间，除非没有更细时间线索。
- 如必须查较长窗口，应分段查询，并在 observation 中注明分段。
- 跨天查询必须拆分为按天或更小窗口，不允许默认跨天一次查。

## 7. 抽样与记录完整性规则

- 命中策略的事件会 100% 记录。
- 非命中策略的事件存在抽样。
- 查到命中策略事件，是强策略证据。
- 未查到非命中事件，不代表该请求没有发生。
- `eventList` 不适合用来估算非命中请求全量规模。
- `eventList` 的 `no_data` 只能说明该查询条件下未见记录，不能代表用户无风险、行为未发生或链路无请求。

## 8. POST 接口信息

```yaml
endpoint:
  method: POST
  url: https://rcp.corp.kuaishou.com/v2/rest/event/eventList?_t=<timestamp_ms>
auth_requirement:
  browser_context: 已认证 rcp 浏览器会话
  cookie_or_token_output: forbidden
readonly: true
```

认证边界：

- `eventList API-read` 依赖已认证 rcp 浏览器上下文。
- 不保存或输出 cookie / token / 完整 header。
- 401 / 403 / redirect_to_login 必须归为 auth blocker，不得解释为 no_data。

## 9. 请求体模板

字段名以内部 Agent 已验证请求为准，后续如平台字段变化，应更新 playbook / run log。

```yaml
eventlist_api_read_request:
  sourceIds:
    - "<source_id>"
  eventType: "<event_type>"
  startTime: "YYYY-MM-DD HH:mm:ss"
  endTime: "YYYY-MM-DD HH:mm:ss"
  timezone: Asia/Shanghai
  cross_day: false
  pagination:
    pageNo:
    pageSize:
  readonly_boundary:
    write_action_allowed: false
    credential_header_output_allowed: false
```

硬性约束：

- `sourceIds` 不能为空。
- `sourceIds` 为空时不得作为用户级证据。
- `startTime` / `endTime` 必须是同一天 Asia/Shanghai 字符串，除非明确分段。
- 不输出完整 request header。

## 10. 返回解析规则

```yaml
eventlist_api_read_response:
  query_status:
  auth_status:
  event_list_count:
  pagination:
  tableHeaderList_present:
  eventList_present:
  extracted_events:
    max_items: 3
```

解释：

- API 成功返回时，`query_status=success`。
- `event_list_count=0` 只能说明该查询条件下未见事件。
- `event_list_count>0` 时，最多保留 3 条 `extracted_events` 样例。
- `weaponDataMap` / `weaponDecodeDataWeapon` 只做摘要，不全文落盘，避免字段过重。

## 11. 事件字段抽取规则

标准抽取字段：

```yaml
extracted_event:
  eventType:
  sourceId:
  eventId:
  occur_time:
  occur_time_cst:
  table_time:
  real_time_op:
  error_code:
  side_effect_ops:
  userRegisterIp:
  ipCity:
  openId_present:
  deviceSignal:
  interpretation:
```

字段策略：

- IP、设备、openId、deviceSignal 等可用于执行态研判，但长期文档只保留必要摘要。
- cookie / token / header / 认证凭据永不落盘。
- `weaponDataMap` / `weaponDecodeDataWeapon` 如果字段很多，只保留字段名、关键摘要和是否存在，不保存全文。

## 12. Observation schema

```yaml
tianshi_eventlist_api_read_observation:
  platform: tianshi_strategy_platform_rcp
  capability: tianshi_eventlist_api_read
  query_type: eventList
  endpoint: /v2/rest/event/eventList
  source_id:
  execution_env:
  auth_status:
  logged_in_user_policy: sample_only_not_rule
  query_window:
    start:
    end:
    timezone: Asia/Shanghai
    cross_day:
    segmentation:
  queried_event_types:
    - eventType:
      sync_or_async:
      meaning:
      query_status:
      event_list_count:
  result_summary:
  extracted_events:
    max_items: 3
    fields:
      - eventType
      - sourceId
      - eventId
      - occur_time
      - occur_time_cst
      - table_time
      - real_time_op
      - error_code
      - side_effect_ops
      - userRegisterIp
      - ipCity
      - openId_present
      - deviceSignal
      - interpretation
  sampling_and_completeness:
    hit_policy_events_recorded_100_percent:
    non_hit_policy_events_sampled:
    no_data_interpretation:
  blockers:
  limitations:
  readonly_safety_check:
```

## 13. 边界说明

- `eventList no_data` 不代表用户无风险。
- `eventList no_data` 不代表行为未发生。
- 非命中策略事件存在抽样。
- 命中策略事件 100% 记录。
- 登录事件在某个时段无记录，可能需要查询用户实际活跃时段。
- 该手脚不替代 `fastQueryHbase`，而是补充请求级 / 事件级字段细查。
- 该手脚不替代 DataAgent / Hive、统一登录日志、档案中心、设备 SDK、前端埋点。
- 不允许 sourceIds 为空时作为用户级证据。
- 不允许默认跨天查询。
- 不保存或输出 cookie / token / 完整 header。
- `logged_in_user` 只能作为 run log 样例，不是固定规则。

## 14. 当前状态

```yaml
version: v2.5.9
capability: tianshi_eventlist_api_read
status: validated_by_internal_agent_run_001
core_skill_modified: false
release_package_updated: false
dataagent_hive_boundary_changed: false
```
