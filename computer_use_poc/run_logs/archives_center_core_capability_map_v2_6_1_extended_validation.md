# Archives Center Core Capability Map v2.6.1 Extended Validation

## 1. 本轮目标

基于内部 Agent 最新 v2.6.1 archives extended validation observation，继续更新档案中心 API-first capability 文档。

本轮是 extended validation patch，不是全量重跑，也不更新 release package。

## 2. 执行边界

- real_platform_access=false
- dataagent_called=false
- release_package_updated=false
- auth_state_exported=false
- write_action=false
- auto_enforcement=false
- auto_risk_finalization=false
- sensitive_plaintext_output=false

## 3. Extended Validation 结果

### 3.1 Private Message Search Direction

Endpoint: `POST /archives/user/message/search`

Validated directions:

- Sender direction: `fromUserId=<user_id>`, `toUserId=null`, observed `total=66`.
- Receiver direction: `fromUserId=null`, `toUserId=<user_id>`, observed `total=204`.

Capability update:

- `private_message_search_direction=validated`
- `fromUserId` and `toUserId` are both usable query directions.

Output boundary:

- Do not output raw private message content.
- Output only field names, counts, status distribution, time range, and risk summaries.

### 3.2 Photo Comment Search Direction

Endpoint: `POST /archives/photo/comment/search`

Validated directions:

- `userId=<user_id>`: comments sent by the user, observed `total=20`.
- `photoId=<photoId>, containsPhotoInfo=true`: comments received by the photo, observed `total=3180`.

Capability update:

- `comment_by_userId=validated`
- `comment_by_photoId=validated`
- `containsPhotoInfo=true` returns extra `photoInfo`.

Output boundary:

- Do not output raw comment content.
- Do not output full `photoInfo`.
- Output only field names, counts, status distribution, risk-label summary, and derived features.

### 3.3 Livestream Chain

Validated chain:

- `POST /v4/archives/gallery/live/list`
- `POST /archives/livestream/home/info`
- `POST /archives/livestream/home/meta`
- `POST /archives/livestream/home/log`
- `POST /archives/livestream/comment/statistics`
- `POST /archives/livestream/comment/detail`

Capability update:

- `livestream_chain=validated`
- live list can provide `liveStreamId`, then live detail/meta/log/comment statistics/comment detail can be read by API direct path.

Output boundary:

- Do not output media URLs.
- Do not output raw live comments.
- Do not output full response JSON.
- Output only field names, counts, time ranges, state distribution, and interaction summaries.

### 3.4 Four-info Log InfoType Mapping

Endpoint: `POST /v4/audit/user/fourinfo/log/search`

Correct payload:

```json
{
  "keyword": "<user_id>",
  "infoType": "<0|1|2|3|4>",
  "markResult": 0,
  "punishResult": 0,
  "count": 20,
  "page": 1
}
```

Corrections:

- The correct user field is `keyword`, not `userId`.
- Previous empty smoke result was caused by payload shape issue.

Validated mapping:

- `infoType=0`: all, observed 71.
- `infoType=1`: username, observed 12.
- `infoType=2`: avatar, observed 18.
- `infoType=3`: profile description, observed 22.
- `infoType=4`: background, observed 19.

Output boundary:

- Do not output raw username.
- Do not output avatar URL.
- Do not output profile description text.
- Do not output background URL.
- Output only change count, time range, status, and type summaries.

## 4. 修改文件

- `computer_use_poc/archives_center_core_capability_map_v2_6_1.md`
- `computer_use_poc/archives_center_api_inventory_v2_4_7_2.md`
- `computer_use_poc/archives_center_internal_agent_playbook.md`
- `computer_use_poc/observation_schema.md`
- `computer_use_poc/smoke_tests.md`
- `computer_use_poc/README.md`

## 5. Smoke Test Updates

新增 / 修正检查项：

- private message search `fromUserId` direction validated.
- private message search `toUserId` direction validated.
- photo comment search by `userId` validated.
- photo comment search by `photoId` validated.
- livestream full chain validated.
- fourinfo payload uses `keyword`, not `userId`.
- fourinfo `infoType=0` all validated.
- fourinfo `infoType=1` username validated.
- fourinfo `infoType=2` avatar validated.
- fourinfo `infoType=3` profile description validated.
- fourinfo `infoType=4` background validated.
- private message raw content is not output.
- comment raw content is not output.
- live comment raw content is not output.
- fourinfo raw profile values are not output.

## 6. 已知限制

- This is not full API regression.
- Extended validation only covers observed request / response shapes.
- Raw private messages, raw comments, live comments, profile values, media URLs, and full JSON remain non-output.
- No automatic enforcement, no automatic risk finalization, and no DataAgent boundary change.

## 7. 结论

建议标记为：

`v2.6.1 archives extended validation patch`
