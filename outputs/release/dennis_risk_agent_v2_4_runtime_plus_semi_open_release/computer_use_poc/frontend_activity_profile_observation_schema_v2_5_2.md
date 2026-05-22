# Frontend Activity Profile Observation Schema v2.5.2

## 1. 标准输出结构

```yaml
frontend_activity_profile_observation:
  platform: track_analysis
  module: 用户洞查 / 用户细查详情 / 用户属性及时长
  app_name:
  query_subject_type:
  query_subject_value:
  query_url:
  query_status:

  profile_card:
    user_id:
    register_time:
    active_days_bucket:
    fan_distribution:
    device_attributes:

  usage_duration:
    chart_present:
    time_range_detected:
    active_days_observed:
    total_usage_duration_observed:
    daily_usage_points_observed:
    peak_usage_day:
    peak_usage_duration:

  activity_judgement:
    has_frontend_activity_signal:
    activity_strength:
    judgement_reason:
    evidence_strength:
    evidence_limitations:

  next_evidence_to_collect:
    login_unified_log:
    device_sdk_profile:
    backend_action_log:
    frontend_event_sequence:
    data_agent_hive_check:

  raw_observation_reference:
    screenshot_path:
    url:
    captured_at:
```

## 2. 字段说明

| 字段 | 含义 | 注意事项 |
| --- | --- | --- |
| `app_name` | KUAISHOU / NEBULA | 其他 appName 后续扩展 |
| `query_subject_type` | userId / deviceId | 不支持批量 |
| `query_subject_value` | 查询对象 | 可保留目标对象值，但不得混入其他敏感对象 |
| `query_status` | loaded / no_result / permission_blocked / auth_blocked / failed | 页面加载失败不得解释为无活跃 |
| `active_days_bucket` | 月活跃天数或活跃天数区间 | 如果页面只展示分桶，按分桶记录 |
| `usage_duration` | 使用时长趋势和每日使用时长 | 只记录上方图表区域，不读下方行为序列 |
| `activity_strength` | none / weak / medium / strong / unknown | 只是前端活跃强度，不是真人强度 |
| `evidence_strength` | weak / medium / strong_for_activity_only | 只限定为活跃信号证据强度 |

## 3. 证据解释边界

必须保留：

- 有使用时长 / 活跃天数，只能说明存在前端活跃信号。
- 不能直接证明是真人操作。
- 不能直接证明是本人操作。
- 不能直接证明没有自动化、脚本、群控。
- 不能证明某个具体业务动作一定发生过。
- 如果要判断具体链路，需要行为序列、后端日志、登录日志、设备 SDK 共同补证。

## 4. next_evidence_to_collect 解释

| 补证项 | 用途 |
| --- | --- |
| `login_unified_log` | 确认登录链路、token、接口调用和时间点 |
| `device_sdk_profile` | 确认设备风险、SDK 采集和设备一致性 |
| `backend_action_log` | 确认具体业务动作是否发生 |
| `frontend_event_sequence` | 确认具体前端路径和事件序列 |
| `data_agent_hive_check` | 长周期或批量离线补证 |

## 5. 禁止解释

- 不得把前端活跃画像解释为完整行为链路。
- 不得把使用时长解释为真人必然存在。
- 不得把活跃强解释为无风险。
- 不得把活跃弱解释为一定异常。
- 不得把空结果解释为用户没有任何前端行为。
