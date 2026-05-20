# User ↔ Device Entity Resolution Routing Rules v2.6.0

## 1. 规则 1：输入 userId，问题意图是设备环境风险

示例：

- “用户 123456 有没有 hook 风险？”
- “这个用户是不是改机设备？”
- “这个用户有没有 frida / root / jailbreak？”
- “这个用户像不像群控设备？”

处理：

```yaml
rule_id: user_to_device_for_device_risk
input_entity: userId
intent: device_environment_risk
first_route: user_to_device_entity_resolution
first_hand: weapon_graphData
graphData_params:
  productName: KWAI_PROD
  groupValue: "{userId}"
  searchLevel: 2
  groupKey: USER_ID
  dimKey: DEVICE_ID
parse:
  center_node: key={userId}, type=USER_ID
  candidate_nodes: type=DEVICE_ID
  direct_edges: source={userId}, target=DEVICE_ID
second_route_after_resolved: device_sdk_api_direct_readonly_hand
if_no_device_id: missing_device_id
if_multiple_devices:
  rank_by:
    - relationEdgeList 直接相连
    - relationDetail 风险提示
    - weight
    - 档案中心用户分析 API 近期关联设备补充排序
  default_bulk_deep_check: false
```

禁止：

- 在没有 deviceId / did / deviceceid 的情况下直接调用 Device SDK hand。
- 直接把 userId 填入 Device SDK hand 的 deviceId 入参。
- 把 Device SDK riskData 当成 user_to_device 主入口。
- 候选设备过多时默认批量深查。

## 2. 规则 2：输入 deviceId，问题意图是关联用户

示例：

- “这个设备关联了哪些用户？”
- “这个设备有没有关联封禁账号？”
- “这个 deviceId 是谁在用？”
- “这个设备是不是账号团伙节点？”

处理：

```yaml
rule_id: device_to_user_for_related_users
input_entity: deviceId / did / deviceceid
intent: related_user_check
first_route: device_to_user_entity_resolution
first_hand: weapon_graphData
graphData_params:
  productName: KWAI_PROD
  groupValue: "{deviceId}"
  searchLevel: 2
  groupKey: DEVICE_ID
  dimKey: USER_ID
parse:
  center_node: key={deviceId}, type=DEVICE_ID
  candidate_nodes: type=USER_ID
  direct_edges: source={deviceId}, target=USER_ID
output:
  - related_user_ids
  - primary_user_id
  - recent_user_id
  - graph_summary
answer_boundary:
  - 关联关系不是风险定性
  - 关联封禁账号是风险线索，不等于当前账号一定作弊
```

可摘要：

- 关联用户数
- 封禁用户数
- 状态异常数
- 社交封禁数
- 最近注册数

## 3. 规则 3：输入 userId，问题本身是登录流水

示例：

- “这个用户最近登录失败原因是什么？”
- “这个用户为什么登录失败？”
- “这个用户最近登录记录是什么？”

处理：

```yaml
rule_id: user_login_log_no_entity_resolution
input_entity: userId
intent: login_flow_or_failure
entity_resolution_needed: false
route_to: user_login_log_hand
graphData_called: false
device_sdk_called: false
```

说明：

- 这类问题的目标 hand 本身支持 userId。
- 不需要先做 user_to_device。
- graphData 不应调用，除非用户同时追问设备关联关系或设备风险。

## 4. 规则 4：输入 deviceId，问题是设备画像 / 设备环境风险

示例：

- “这个 deviceId 有没有 hook / frida？”
- “这个设备是否 root？”
- “这个设备有没有 proxy / simulator / repack 风险？”

处理：

```yaml
rule_id: direct_device_sdk_for_device_profile
input_entity: deviceId / did / deviceceid
intent: device_profile_or_environment_risk
entity_resolution_needed: false
route_to: device_sdk_api_direct_readonly_hand
graphData_called: false
answer_boundary:
  - 设备侧补证
  - 不单独最终定性
```

说明：graphData 不应作为第一步，除非用户问“关联用户 / 谁在用 / 团伙节点”。

## 5. 规则 5：候选过多

处理：

```yaml
rule_id: too_many_candidates_guardrail
condition: candidate_count > max_candidates
default_bulk_deep_check: false
result_status: too_many_candidates
output:
  - top_candidates
  - rank_reason
  - ask_user_to_narrow_scope
recommended_narrowing_dimensions:
  - 时间范围
  - 最近登录 / 最近活跃
  - 成功 / 失败登录
  - 风险事件时间点
  - 指定业务场景
```

禁止：

- 默认批量调用 Device SDK hand 深查全部候选设备。
- 把候选过多解释为无风险。
- 把未覆盖候选解释为全量已查。
- 默认进入批量 DataAgent / Hive 查询。

## 5.1 规则 5a：graphData 运行态错误语义

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

禁止：

- 把 `auth_required`、`permission_denied` 当成无数据。
- 把 `no_related_entity`、`no_direct_relation` 当成无风险。
- 把 `parse_error` 当成空结果。
- 候选过多时默认批量调用 Device SDK 或 DataAgent。

## 6. 规则 6：Device SDK riskData 的位置

```yaml
device_sdk_riskData_role:
  entity_resolution_main_entry: false
  role: device_risk_evidence_after_entity_resolved
  when_to_call:
    - user_to_device 得到 selected_device_id 后
    - 用户直接输入 deviceId 并询问设备画像 / 设备环境风险时
  evidence_scope:
    - hook
    - frida
    - root / jailbreak
    - proxy
    - simulator
    - repack
```

说明：

- graphData 负责 User ↔ Device 实体转译。
- Device SDK hand / riskData 负责设备侧风险补证。
- 不允许把 riskData 作为 user_to_device 主实体解析入口。

## 7. 规则 7：档案中心用户分析 API 的位置

处理：

- 档案中心 → 用户分析 API 的近期关联设备只作为 user_to_device 的补充来源。
- 用于 candidate_device_ids 去重、recent_device_id 辅助排序。
- 不作为本轮主入口。
- 本轮不真实查询，不新增接口，只写规则边界。

## 8. 排序规则

### candidate_devices

1. 优先 `relationEdgeList` 直接相连节点。
2. 其次看 `relationDetail` 中风险更高的设备：
   - 强风险标签数高
   - 中风险标签数高
   - 弱风险标签数高
   - 关联用户数高
   - 封禁用户数 / 状态异常数高
3. 再看 `weight`，weight 高的优先。
4. 档案中心用户分析 API 的近期关联设备命中时，可提升 `recent_device_id` 排序。
5. 仍无法判断时，返回 top candidates，不默认全量深查。

### related_user_ids

1. 优先 `relationEdgeList` 直接相连节点。
2. 其次看 `relationDetail` 中风险更高的用户：
   - 封禁用户
   - 社交封禁
   - 状态异常
   - 最近注册
3. 再看 `weight`，weight 高的优先。
4. 候选用户过多时，返回 top candidates，不默认批量深查。

注意：当前样例中 weight 都是 `0.56`，weight 是辅助字段，不能过度依赖。

## 9. 与 DataAgent / Hive 的边界

- 批量用户设备关系、长期历史聚合、群体分布统计，应生成 DataAgent / Hive 查询建议。
- DataAgent / Hive 只定位为公司数仓取数分析能力。
- DataAgent / Hive 不替代 Weapon graphData 的在线实体转译，也不替代 Device SDK hand 的设备画像。

## 10. 输出话术边界

当 Entity Resolution 成功时：

```text
我先把输入实体和目标手脚入参对齐：你给的是 userId，但设备 SDK 需要 deviceId。
本轮实体转译主入口是 Weapon graphData；先用 userId 查候选 deviceId，再对选中的 deviceId 做设备侧补证。
```

当 Entity Resolution 失败时：

```text
当前缺少后续手脚必需的 deviceId / did / deviceceid，不能直接调用设备 SDK。
Weapon graphData 未解析出候选设备时，应返回 missing_device_id，而不是给设备风险结论。
```
