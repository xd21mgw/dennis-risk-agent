# Entity Resolution Layer v2.6.0 MVP: User ↔ Device

## 1. 定位

Entity Resolution Layer 位于主 Agent intent routing 和具体 hand 之间。

v2.6.0 MVP 只负责 `userId` 与 `deviceId / did / deviceceid` 的双向实体转译：

- `userId → candidate_device_ids`
- `deviceId / did / deviceceid → related_user_ids`

该层不直接查最终风险，不直接做风险定性，不替代 Device SDK hand、用户登录统一日志、档案中心或 DataAgent / Hive。它只为后续 hand 补齐必要入参。

本轮主入口统一为 Weapon `graphData`：

- `user_to_device`: `groupKey=USER_ID`, `dimKey=DEVICE_ID`
- `device_to_user`: `groupKey=DEVICE_ID`, `dimKey=USER_ID`

Device SDK `riskData` 本轮不作为实体解析主入口，只保留为后续设备侧风险补证 hand。档案中心用户分析 API 的近期关联设备只作为 `user_to_device` 的补充来源，用于 deviceId 去重和 `recent_device_id` 辅助排序。

## 2. 支持的双向转译

### A. userId → deviceId

适用场景：

- 用户输入 `userId`，但问题是设备环境风险。
- 用户问某用户是否有 hook / frida / root / jailbreak / 改机 / 模拟器 / 双开 / proxy / repack 风险。
- 用户问某用户是否存在群控 / 自动化设备证据。
- 用户问某用户近期登录设备是否异常。
- 用户问某用户有没有设备风险。

主入口：

```text
GET https://weapon-platform.corp.kuaishou.com/apiv2/graphData?productName=KWAI_PROD&groupValue={userId}&searchLevel=2&dimKey=DEVICE_ID&groupKey=USER_ID
```

语义：

- `groupValue` 传 `userId`
- `groupKey=USER_ID`
- `dimKey=DEVICE_ID`
- 用于查询用户关联设备

解析规则：

- `response.code=0` 且 `msg=success` 才视为接口成功。
- `data.pointInfoMap` 中，`key=输入 userId` 且 `type=USER_ID` 的节点是中心用户节点。
- `data.pointInfoMap` 中，`type=DEVICE_ID` 的节点是 candidate device candidates。
- `data.relationEdgeList` 中，`source=输入 userId`、`target=DEVICE_ID` 的边表示用户到设备的直接关联。
- 中心用户节点 `relationDetail` 可解析为 `graph_summary`，例如关联设备数、强风险标签数、中风险标签数、弱风险标签数。
- `relationDetail` 是中文摘要字符串，解析失败时保留原文到 `evidence_summary / graph_summary`。

补充来源：

- 档案中心 → 用户分析 API 的近期关联设备。
- 仅用于 deviceId 去重、`recent_device_id` 辅助排序。
- 不作为本轮主入口。

候选来源保留说明：

- user_login_log hand：可作为未来最近登录设备补证来源。
- frontend_activity hand：可作为未来前端活跃设备标识补证来源。
- DataAgent / Hive：只适合批量或历史聚合场景，本轮不做。
- Device SDK `riskData`：本轮不作为实体解析主入口，只作为后续设备侧补证 hand。

输出：

```yaml
user_to_device_resolution:
  candidate_device_ids:
    - device_id:
      device_id_type:
      source_hand: weapon_graphData
      relation_type: USER_ID_TO_DEVICE_ID
      confidence:
      time_range:
      weight:
      tags:
      color:
      relation_detail:
      rank:
      rank_reason:
      evidence_summary:
  primary_device_id:
  recent_device_id:
  high_risk_hint_device_id:
  graph_summary:
  source_hand: weapon_graphData
  confidence:
  time_range:
  rank_reason:
```

### B. deviceId → userId

适用场景：

- 用户输入 `deviceId / did / deviceceid`，但问题是设备关联用户。
- 用户问这个设备是谁在用。
- 用户问这个设备关联多少账号。
- 用户问这个设备是否关联封禁用户 / 异常用户。
- 用户问某设备是否是账号团伙节点。

主入口：

```text
GET https://weapon-platform.corp.kuaishou.com/apiv2/graphData?productName=KWAI_PROD&groupValue={deviceId}&searchLevel=2&dimKey=USER_ID&groupKey=DEVICE_ID
```

语义：

- `groupValue` 传 `deviceId`
- `groupKey=DEVICE_ID`
- `dimKey=USER_ID`
- 用于查询设备关联用户

解析规则：

- `response.code=0` 且 `msg=success` 才视为接口成功。
- `data.pointInfoMap` 中，`key=输入 deviceId` 且 `type=DEVICE_ID` 的节点是中心设备节点。
- `data.pointInfoMap` 中，`type=USER_ID` 的节点是 related user candidates。
- `data.relationEdgeList` 中，`source=输入 deviceId`、`target=USER_ID` 的边表示设备到用户的直接关联。
- 中心设备节点 `relationDetail` 可解析为 `graph_summary`，例如关联用户数、封禁用户数、社交封禁数、状态异常数、最近注册数。

输出：

```yaml
device_to_user_resolution:
  related_user_ids:
    - user_id:
      source_hand: weapon_graphData
      relation_type: DEVICE_ID_TO_USER_ID
      confidence:
      time_range:
      weight:
      tags:
      color:
      relation_detail:
      rank:
      rank_reason:
      evidence_summary:
  primary_user_id:
  recent_user_id:
  banned_user_count:
  abnormal_user_count:
  graph_summary:
  source_hand: weapon_graphData
  confidence:
  time_range:
```

## 3. 排序规则

### candidate_devices 排序

1. 优先 `relationEdgeList` 直接相连节点。
2. 其次看 `relationDetail` 中风险更高的设备：
   - 强风险标签数高
   - 中风险标签数高
   - 弱风险标签数高
   - 关联用户数高
   - 封禁用户数 / 状态异常数高
3. 再看 `weight`，weight 高的优先。
4. 如果档案中心用户分析 API 的近期关联设备命中，可提升 `recent_device_id` 排序。
5. 如果仍无法判断，返回 top candidates，不默认全量深查。

### related_user_ids 排序

1. 优先 `relationEdgeList` 直接相连节点。
2. 其次看 `relationDetail` 中风险更高的用户：
   - 封禁用户
   - 社交封禁
   - 状态异常
   - 最近注册
3. 再看 `weight`，weight 高的优先。
4. 如果候选用户过多，返回 top candidates，不默认批量深查。

注意：当前样例中 weight 都是 `0.56`，因此 weight 只是辅助字段，不能过度依赖。

## 4. 边界

- 如果输入是 `userId`，但 Weapon graphData 没有找到 `candidate_device_ids`，返回 `missing_device_id`。
- 如果输入是 `deviceId`，但 Weapon graphData 没有找到 `related_user_ids`，返回 `missing_user_id` 或 `no_related_user`。
- 多设备候选时，不默认批量深查；优先按直接关联、风险提示、weight、近期关联排序。
- 多用户候选时，不默认批量深查；优先按直接关联、封禁 / 异常状态、weight 排序。
- 如果候选过多，返回 `too_many_candidates`，需要缩小范围。
- 实体解析结果只是候选实体关系，不是风险结论。
- graphData 的 `relationDetail`、`weight`、`tags`、`color` 只能作为排序和摘要依据，不能直接当作最终风险定性。
- answer_boundary 必须说明：只能说“关联设备 / 关联用户存在某些补证线索”，不能直接说“该用户 / 设备一定作弊”。

## 4.1 graphData 运行态错误语义

| 运行态情况 | status | next_action | 禁止解释 |
|---|---|---|---|
| `code != 0` 或 `msg != success` | `graphdata_error` | 返回错误摘要 | 不解释为无关联 / 无风险 |
| 认证失效、跳登录、无有效 cookie | `auth_required` | 提示需要重新认证态 | 不解释为接口无数据 |
| 权限不足、接口返回无权限 | `permission_denied` | 提示当前账号无 graphData / 关联图谱权限 | 不解释为无关联 |
| `data` 为空 | `no_related_entity` | 返回当前条件下未见关联实体 | 不解释为无风险 |
| `pointInfoMap` 为空 | `no_related_entity` | 返回当前条件下未见关联实体 | 不解释为无风险 |
| `relationEdgeList` 为空但 `pointInfoMap` 有节点 | `no_direct_relation` | 保留节点摘要，说明未见直接关联边 | 不解释为无关联风险闭环 |
| `user_to_device` 无 `DEVICE_ID` 候选 | `missing_device_id` | 不调用 Device SDK，返回缺少设备实体 | 不把 userId 填给 Device SDK |
| `device_to_user` 无 `USER_ID` 候选 | `no_related_user` / `missing_user_id` | 返回未见关联用户或缺少用户实体 | 不解释为设备干净 |
| 候选超过 `max_candidates` | `too_many_candidates` | 返回 top candidates，要求缩小范围 | 不默认批量深查 |
| 返回结构变化、字段缺失 | `parse_error` | 保留 raw_summary，要求人工复核 | 不降级成 no_data |

这些错误语义只描述实体解析执行状态，不产生风险结论。

## 5. 下一步 hand 接入规则

### userId → deviceId → Device SDK

当用户输入 `userId` 但问题需要设备风险证据时：

1. 先识别用户问题意图。
2. 判断 Device SDK hand 所需入参为 `deviceId / did / deviceceid`。
3. 进入 `user_to_device` entity resolution。
4. 主入口调用 Weapon graphData。
5. 选出 `selected_entity.device_id`。
6. 再调用 `device_sdk_api_direct_readonly_hand` 做设备侧风险补证。
7. 回答中保留边界：设备侧 observation 只能作为补证，不单独最终定性。

### deviceId → userId → 账号相关 hand

当用户输入 `deviceId` 但问题是“谁在用 / 关联账号 / 是否关联封禁账号”时：

1. 进入 `device_to_user` entity resolution。
2. 主入口调用 Weapon graphData。
3. 输出 `related_user_ids / graph_summary`。
4. 如需账号画像，再进入档案中心；如需登录链路，再进入用户登录统一日志。
5. 不把关联关系直接解释为风险定性。

## 6. 不纳入 v2.6.0 MVP 的实体

本轮不做：

- case_id / ticket_id
- IP / 网段
- app / package / bundle id
- phone / open_id / third-party id
- photoId / liveStreamId
- 时间窗口解析
- 风险标签映射
- 批量实体展开

这些实体后续如需接入，应单独设计，不混入 v2.6.0 MVP。
