# Archives Center Core Capability Map v2.6.1 Follow-up Validation

## 1. 本轮目标

基于内部 Agent v2.6.1 archives follow-up validation 结果，统一修正档案中心 API-first capability 文档中的 three-item status drift：

- `/v4/archives/report/photo/search` 从 pending / 500 更新为 validated。
- `/archives/draco/getPunishStatus` 从笼统 photo/live targetId 边界更新为 photo / live level validated、user-level unsupported。
- `/archives/user/search/device` same_device type 映射从 pending 更新为 validated。

本轮是 follow-up validation patch，不是全量接口回归。

## 2. 执行边界

- real_platform_access=false
- dataagent_called=false
- release_package_updated=false
- auth-state category_read=false
- write_action=false
- auto_enforcement=false
- auto_risk_finalization=false
- sensitive_plaintext_output=false

## 3. 更新摘要

### photo_report_search

Endpoint: `POST /v4/archives/report/photo/search`

Correct payload:

```json
{
  "matchType": "0",
  "reportedIds": "<user_id>",
  "sort": "0",
  "begin": "<ms_timestamp>",
  "end": "<ms_timestamp>",
  "page": 1,
  "count": 20
}
```

Follow-up observation:

- `code/result=1`
- `totalCount=292`
- `dataList.length=20`
- `validation_status=validated`
- `api_can_replace_dom=true`

Correction:

- `reportedIds` is `user_id`, not `photoId`.
- Use `begin` / `end`, not `beginTime` / `endTime`.
- Use `sort`, not `sortType`.
- `matchType` and `sort` are strings.
- Previous 500 was caused by payload field and semantic mismatch, not endpoint unavailability.

### getPunishStatus

Endpoint: `POST /archives/draco/getPunishStatus`

Validated payloads:

```json
{"targetId": "<photoId>", "targetType": "PHOTO"}
```

```json
{"targetId": "<liveStreamId>", "targetType": "LIVE_STREAM"}
```

Correction:

- User-level is unsupported.
- `targetType` must be uppercase.
- Lowercase `"photo"` returns 412.
- Live-level target type is `"LIVE_STREAM"`, not `"LIVE"`.

### same_device

Endpoint: `POST /archives/user/search/device`

Validated payload:

```json
{"keyword": "<user_id>", "inputType": 0, "type": 0}
```

```json
{"keyword": "<user_id>", "inputType": 0, "type": 1}
```

Correction:

- `type=0` means same-device registered users.
- `type=1` means same-device login users.
- Mapping status is `mapping_validated`.
- Do not use the old `{userId, source, type}` payload.
- Related user ID / nickname / device values must remain redacted or aggregated.

## 4. 修改文件

- `computer_use_poc/archives_center_core_capability_map_v2_6_1.md`
- `computer_use_poc/archives_center_api_inventory_v2_4_7_2.md`
- `computer_use_poc/archives_center_internal_agent_playbook.md`
- `computer_use_poc/observation_schema.md`
- `computer_use_poc/smoke_tests.md`
- `computer_use_poc/README.md`

## 5. Smoke Test Updates

新增 / 修正检查项：

- photo report search validated with `reportedIds=user_id`
- photo report search uses `begin/end`, not `beginTime/endTime`
- photo report search uses `sort`, not `sortType`
- getPunishStatus photo level validated
- getPunishStatus live level validated
- getPunishStatus user level unsupported
- same_device type mapping validated
- same_device `type=0` is same-device registered users
- same_device `type=1` is same-device login users

## 6. 已知限制

- 这不是全量接口回归。
- 这不代表所有 report / punish / same-device 分页、过滤和边界参数都已覆盖。
- report signals 仍然不能单独作为强证据。
- same-device relation 只能作为关联线索，不能自动风险定性。
- 本轮不改变 DataAgent 边界，不引入自动处置。

## 7. 结论

建议标记为：

`v2.6.1 archives follow-up validation patch`

状态：文档口径可更新为 follow-up validated，但仍需保留非全量回归边界。
