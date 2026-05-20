# User ↔ Device Entity Resolution Contract v2.6.0

## 1. Request Schema

```yaml
user_device_entity_resolution_request:
  original_question:
  detected_intent:
  input_entities:
    - entity_type: userId / deviceId / did / deviceceid
      raw_value:
      normalized_value:
      confidence:
  required_entity:
    entity_type:
    required_by_hand:
    required_reason:
  resolution_direction:
    value: user_to_device / device_to_user / none
    reason:
  preferred_resolution_hand:
    hand_name: weapon_graphData
    reason:
```

方向规则：

- `user_to_device`: `groupKey=USER_ID`, `dimKey=DEVICE_ID`
- `device_to_user`: `groupKey=DEVICE_ID`, `dimKey=USER_ID`

Device SDK `riskData` 不作为本轮 entity resolution source，只作为 `next_route` 的设备补证 hand。

## 2. Result Schema

```yaml
user_device_entity_resolution_result:
  status:
    value: resolved / partial / missing_required_entity / too_many_candidates / no_translation_needed / graphdata_error / auth_required / permission_denied / no_related_entity / no_direct_relation / missing_device_id / no_related_user / missing_user_id / parse_error
    reason:
  source_hands_used:
    - hand_name:
      purpose:
      endpoint:
      method:
  graph_data_request:
    productName:
    groupValue:
    searchLevel:
    groupKey:
    dimKey:
  graph_data_parse_summary:
    center_entity:
    center_entity_type:
    center_relation_detail:
    direct_edge_count:
    candidate_count:
    parse_notes:
  candidate_devices:
    - device_id:
      device_id_type:
      source_hand:
      relation_type:
      confidence:
      time_range:
      weight:
      tags:
      color:
      relation_detail:
      rank:
      rank_reason:
      evidence_summary:
  candidate_users:
    - user_id:
      source_hand:
      relation_type:
      confidence:
      time_range:
      weight:
      tags:
      color:
      relation_detail:
      rank:
      rank_reason:
      evidence_summary:
  selected_entity:
    entity_type:
    value:
    selection_reason:
  next_route:
    target_hand:
    required_input:
    answer_boundary:
  safety_boundary:
    no_bulk_overreach:
    max_candidates:
    sensitive_fields_excluded:
    risk_conclusion_not_allowed:
```

## 3. graphData Request Direction

### user_to_device

```yaml
graph_data_request:
  productName: KWAI_PROD
  groupValue: "{userId}"
  searchLevel: 2
  groupKey: USER_ID
  dimKey: DEVICE_ID
```

解析：

- 中心节点：`key={userId}`, `type=USER_ID`
- 候选设备：`type=DEVICE_ID`
- 直接边：`source={userId}`, `target=DEVICE_ID`
- `relation_type=USER_ID_TO_DEVICE_ID`

### device_to_user

```yaml
graph_data_request:
  productName: KWAI_PROD
  groupValue: "{deviceId}"
  searchLevel: 2
  groupKey: DEVICE_ID
  dimKey: USER_ID
```

解析：

- 中心节点：`key={deviceId}`, `type=DEVICE_ID`
- 候选用户：`type=USER_ID`
- 直接边：`source={deviceId}`, `target=USER_ID`
- `relation_type=DEVICE_ID_TO_USER_ID`

## 4. Status 语义

| status | 含义 | 后续动作 |
|---|---|---|
| `resolved` | 找到可用于后续 hand 的实体 | 进入 `next_route.target_hand` |
| `partial` | 找到候选，但置信度或覆盖不足 | 输出候选和缺口，必要时让用户缩小范围 |
| `missing_required_entity` | 没找到目标 hand 必需实体 | 返回 `missing_device_id / missing_user_id` |
| `too_many_candidates` | 候选过多，不适合默认深查 | 返回 top candidates 或要求缩小范围 |
| `no_translation_needed` | 输入实体已满足目标 hand 入参 | 直接进入目标 hand |
| `graphdata_error` | graphData 返回 `code != 0` 或 `msg != success` | 返回错误摘要，不继续风险判断 |
| `auth_required` | 认证失效、跳登录、无有效 cookie | 提示需要重新认证态 |
| `permission_denied` | 权限不足或接口返回无权限 | 提示当前账号无 graphData / 关联图谱权限 |
| `no_related_entity` | `data` 为空或 `pointInfoMap` 为空 | 说明当前条件下未见关联实体，不解释为无风险 |
| `no_direct_relation` | `relationEdgeList` 为空但 `pointInfoMap` 有节点 | 说明未见直接关联边，保留节点摘要，不做风险定性 |
| `missing_device_id` | `user_to_device` 未解析出 `DEVICE_ID` 候选 | 返回缺少设备实体，不能调用 Device SDK |
| `no_related_user` | `device_to_user` 未解析出 `USER_ID` 候选 | 返回未见关联用户，不解释为设备干净 |
| `missing_user_id` | 后续账号 hand 需要 userId 但未解析出 | 返回缺少用户实体 |
| `parse_error` | 返回结构变化、关键字段缺失、无法解析 | 保留 raw_summary，要求人工复核 |

## 4.1 graphData Error Semantics

```yaml
graphData_error_semantics:
  code_not_zero_or_msg_not_success:
    status: graphdata_error
    next_action: return_error_summary
  auth_expired_or_redirect_to_login:
    status: auth_required
    next_action: 提示需要重新认证态
  permission_denied:
    status: permission_denied
    next_action: 提示当前账号无 graphData / 关联图谱权限
  data_empty:
    status: no_related_entity
  pointInfoMap_empty:
    status: no_related_entity
  relationEdgeList_empty:
    status: no_direct_relation
  user_to_device_no_DEVICE_ID:
    status: missing_device_id
  device_to_user_no_USER_ID:
    status: no_related_user / missing_user_id
  candidates_exceed_max:
    status: too_many_candidates
    next_action: 返回 top candidates，要求缩小范围，不默认批量深查
  response_shape_changed_or_required_field_missing:
    status: parse_error
    next_action: 保留 raw_summary，要求人工复核
```

边界：

- `no_related_entity`、`no_direct_relation`、`missing_device_id`、`no_related_user` 都不能解释为无风险。
- `auth_required` / `permission_denied` 是执行阻断，不是数据结论。
- `parse_error` 不能降级成无结果；必须明确结构异常和待人工复核。
- `too_many_candidates` 不能触发默认批量深查。

## 5. Safety Boundary

```yaml
safety_boundary:
  no_bulk_overreach: true
  max_candidates: 3
  sensitive_fields_excluded:
    - token
    - session
    - cookie
    - authorization
    - precise_location
  risk_conclusion_not_allowed: true
```

说明：

- Entity Resolution 只做候选实体转译，不做风险定性。
- 默认最多给出少量 top candidates，不做批量滥查。
- graphData 的 `relationDetail / weight / tags / color` 只用于摘要和排序，不直接作为最终风险定性。
- 如果需要批量用户设备关系，应进入 DataAgent / Hive 查询建议，而不是展开在线 hand 批量调用。
- 档案中心用户分析 API 只能作为 supplement source，不作为主入口。

## 6. Example: userId → deviceId

```yaml
user_device_entity_resolution_request:
  original_question: 用户 123456 有没有 hook / frida 风险？
  detected_intent: device_environment_risk_check
  input_entities:
    - entity_type: userId
      raw_value: "123456"
      normalized_value: "123456"
      confidence: high
  required_entity:
    entity_type: deviceId
    required_by_hand: device_sdk_api_direct_readonly_hand
    required_reason: Device SDK hand 需要 deviceId / did / deviceceid
  resolution_direction:
    value: user_to_device
    reason: 用户输入 userId，但目标 hand 需要 deviceId
  preferred_resolution_hand:
    hand_name: weapon_graphData
    reason: v2.6.0 user_to_device 主入口
```

## 7. Example: deviceId → userId

```yaml
user_device_entity_resolution_request:
  original_question: 设备 ANDROID_xxx 关联哪些用户？
  detected_intent: device_related_user_check
  input_entities:
    - entity_type: deviceId
      raw_value: ANDROID_xxx
      normalized_value: ANDROID_xxx
      confidence: high
  required_entity:
    entity_type: userId
    required_by_hand: archives_center_hand / user_login_log_hand
    required_reason: 后续如需账号画像或登录链路，需要 userId
  resolution_direction:
    value: device_to_user
    reason: 用户输入 deviceId，但问题要求关联用户
  preferred_resolution_hand:
    hand_name: weapon_graphData
    reason: v2.6.0 device_to_user 主入口
```
