# v2.6.1 Archives API-first Core Capability Map

## 1. Version Positioning

v2.6.1 is the archives center API-first core capability map. It is not a new
platform and is not a continuation branch of v2.4.x. v2.4.x remains historical
validation record; v2.6.1 reorganizes archives center from page / Tab reading
into risk capability packages.

Goal:

- Move archives center execution from page-tab perspective to risk capability perspective.
- Use API direct read by default.
- Keep page / DOM / selector as fallback only.
- Keep DataAgent boundary unchanged.
- Do not introduce automatic enforcement.
- Do not introduce automatic risk finalization.
- Do not output sensitive plaintext.
- Do not treat screenshots as interface validation. Only parsed API results or executed observations can be recorded as validated.

Default read order:

1. API direct read.
2. DOM scoped JS eval fallback.
3. Row feature filter fallback.
4. Scoped snapshot fallback.

Page fallback is only allowed when:

- `API failed`
- `permission_blocked`
- `response_shape_changed`
- `key_fields_missing`
- `link_url_only`
- `mapping_pending_validation`
- `need_required_param`

## 2. Core Capability Packages

### 2.1 account_profile

Coverage:

- User home basic information.
- Account status.
- Recent login / recent launch.
- Registration information.
- Account information.
- Live / ecommerce status.
- Current punishment status.
- Risk / label / negative information.

Typical APIs:

| endpoint | method | role |
| --- | --- | --- |
| `/archives/user/home/info` | GET | user home profile |
| `/v3/user/negative/report` | POST | negative status |
| `/v3/user/negative/unInterested` | POST | negative related status |
| `/v3/user/risk/info` | GET | risk info |
| `/archives/user/home/getUserLabel` | POST | user labels |
| `/archives/user/home/getUserShopInfo` | GET | shop status |
| `/archives/draco/getPunishStatus` | POST | punishment status |

Risk value:

- Base account status.
- Current normal / banned / restricted status.
- Recent login / launch and profile state.
- Base profile for ATO, false positive review, and content abuse.

### 2.2 account_change_trace

Coverage:

- User four-info logs.
- Avatar / nickname / intro / background historical changes.
- Four-info audit records.
- Profile change timeline.

APIs:

| endpoint | method | role |
| --- | --- | --- |
| `/v4/audit/user/fourinfo/log/allTypes` | POST | four-info type/options |
| `/v4/audit/user/fourinfo/log/search` | POST | four-info change logs |

Risk value:

- Whether nickname / intro / avatar / background changed after ATO.
- Whether profile text shows pornography, fraud, diversion, or gray-market words.
- Whether profile change time aligns with abnormal login or content posting.
- Home page shows current state; four-info logs show historical change.

### 2.3 account_action_log

Coverage:

- User analysis statistic matrix.
- APP core operation logs.
- Launch / login / scan / bind / reset / freeze behavior chain.

Typical APIs:

| endpoint | method | role |
| --- | --- | --- |
| `/v3/user/analyze/fetch` | POST | user analysis summary |
| `/v3/user/log/coreLogs/fetch` | POST | APP core operation logs |

Notes:

- `/v3/user/log/coreLogs/fetch` was validated in v2.4.7.1.
- `focused_login_risk` defaults to API direct POST.
- DOM row feature filter is fallback only.

Risk value:

- ATO initial screening.
- Abnormal login / launch / scan / bind / freeze chain.
- Timeline alignment with content posting, profile change, private message, and comment behavior.

### 2.4 content_gallery

Coverage:

- Video gallery.
- Live gallery.
- Collected videos / music / folders.
- Collection list.
- Moment / post gallery.

Typical APIs:

| endpoint | method | role |
| --- | --- | --- |
| `/v3/user/gallery/photo/top` | POST | top photos |
| `/v3/user/gallery/photo/list` | POST | photo list |
| `/v4/archives/gallery/live/list` | POST | live list |
| `/v3/user/collect/photo/list` | POST | collected photo list |
| `/v3/user/collect/music/searchOption` | GET | collected music options |
| `/v3/user/collect/folder/searchOption` | GET | collect folder options |
| `/archives/photo/collection/getCollectionList` | POST | collection list |
| `/archives/user/gallery/momentList` | POST | moment list |
| `/archives/user/gallery/momentAuthority` | POST | moment authority |

Risk value:

- Whether video / live / moment was posted after ATO.
- Whether collect/folder behavior acts as diversion sink.
- Whether content style suddenly changed.
- Content volume, time, state, and interaction metrics.

### 2.5 content_forensics

Coverage:

- Photo detail.
- Photo meta.
- Photo audit logs.
- Photo report aggregate.
- User autonomy / satisfaction for photo.
- Production flow.
- Posting device / posting path / import mode.

Typical APIs:

| endpoint | method | role |
| --- | --- | --- |
| `/v3/photo/profile` | POST | photo profile |
| `/v3/photo/meta` | POST | photo meta |
| `/v3/photo/report/aggregate` | POST | report aggregate |
| `/archives/photo/home/userAutonomy` | POST | photo user autonomy |
| `/archives/user/home/auditLog` | POST | audit log, requires required params |

Important fields:

- `photoId`
- `uploadTime`
- `photoStatus`
- `reviewStatus`
- `caption`
- `countStat`
- `userInfo`
- `punishInfoList`
- `photoMeta`
- `photoOrigin`
- `document`
- `finalType`
- `clientVer / appVer / channel / model / deviceId / userRouteTrace / importedVideo`

Risk value:

- Whether abnormal videos were posted after ATO.
- Whether posting device / app version / channel / path is abnormal.
- Whether Long Import, moved content, or batch production exists.
- Whether video was reported, audited, or punished.
- Impact surface: play, like, comment, share, collect.

Safety requirements:

- Do not output full video meta JSON.
- Do not output full `userRouteTrace`.
- Do not output plaintext `deviceId`.
- Output only derived features: device consistency, posting client type, version delta, import flag, and path summary.

### 2.6 social_interaction

Coverage:

- Private message search.
- Video comment search.
- Live comment.
- Fans list.
- Follow list.
- Moment interactions.

APIs:

| endpoint | method | role |
| --- | --- | --- |
| `/archives/user/message/search` | POST | private message search |
| `/archives/user/message/options` | POST | private message options |
| `/archives/user/message/keyMaps` | POST | private message key maps |
| `/archives/photo/comment/search` | POST | photo comment search |
| `/archives/photo/comment/types` | GET | comment type options |
| `/archives/photo/comment/status` | POST | comment status options |
| `/archives/photo/comment/userStatus` | POST | comment user status |
| `/archives/photo/comment/queryTypes` | POST | comment query types |
| `/archives/photo/comment/orders` | POST | comment order options |
| `/archives/photo/comment/keyMaps` | POST | comment key maps |
| `/archives/livestream/comment/statistics` | POST | live comment statistics |
| `/archives/livestream/comment/detail` | POST | live comment detail |
| `/v3/user/profile/relation/fans/list` | POST | fans list |
| `/v3/user/profile/relation/follow/list` | POST | follow list |

Risk value:

- Whether private message diversion or fraud exists after ATO.
- Whether account comments diversion / pornography / controversy under others' videos.
- Whether repeated private messages or comments exist.
- Quality and source of fans / follows.
- Diversion sink and interaction anomaly.

Safety requirements:

- Private message and comment contents default to summarized output.
- Do not output full private message plaintext.
- Do not output full comment plaintext.
- Output content type, risk summary, repeated pattern, count, time distribution, and state distribution.

### 2.7 report_signal

Coverage:

- User report search.
- Photo report search.
- Photo report aggregate.
- Comment risk labels.
- Report reason / type / time / target.

APIs:

| endpoint | method | role |
| --- | --- | --- |
| `/v4/archives/report/user/options` | GET | user report options |
| `/v4/archives/report/user/search` | POST | user report search |
| `/v4/archives/report/photo/options` | GET | photo report options |
| `/v4/archives/report/photo/search` | POST | photo report search |
| `/v3/photo/report/aggregate` | POST | photo report aggregate |

Risk value:

- Whether account was reported by users.
- Whether video was reported.
- Whether report reasons cluster in pornography, fraud, impersonation, harassment, or discomfort.
- Timeline alignment with abnormal login, content posting, and profile change.

Boundary:

- Reports are external feedback signals, not strong evidence by themselves.
- Do not use reports alone to finalize violation or ATO.
- Cross-check with photo detail, meta, audit logs, and punishment status.

### 2.8 relation_graph

Coverage:

- Same-device related users.
- Fans / follow relation.
- Related account status.
- Relation expansion clues.

Typical APIs:

| endpoint | method | role |
| --- | --- | --- |
| `/archives/user/search/device` | POST | same-device related users |
| `/v3/user/profile/relation/fans/list` | POST | fans list |
| `/v3/user/profile/relation/follow/list` | POST | follow list |

Notes:

- `/archives/user/search/device type=0 / type=1` interfaces are usable.
- Business meaning for `type=0 / type=1` remains `mapping_pending_validation`.
- Do not hard-code login / registration mapping unless later validated by entry wording.

Risk value:

- Same-device expansion.
- Account farm or group clues.
- Related account status, registration time, recent launch time.
- Fans/follow aggregation.

## 3. Scene to Capability Routing

| scene | default capabilities | optional capabilities | output focus |
| --- | --- | --- | --- |
| ATO initial screening | account_profile, account_action_log, account_change_trace, relation_graph | content_gallery, social_interaction, report_signal | abnormal login / launch / device, profile change, same-device relation, content / message / comment clues; do not directly finalize ATO |
| ATO followed by video posting | account_action_log, content_gallery, content_forensics, report_signal | account_change_trace, relation_graph | video after abnormal time, abnormal meta device/version/channel/import, report/audit/punishment, impact surface |
| ATO followed by profile change | account_profile, account_change_trace, report_signal | account_action_log | nickname / intro / avatar / background change, timing alignment, diversion words, audit result |
| private message diversion / fraud | social_interaction, account_action_log, report_signal | account_change_trace | message existence, repeated pattern, risk summary, profile diversion |
| comment diversion / pornography | social_interaction, content_forensics, report_signal | account_profile | comments under others' videos, comment status/risk labels, controversy bait, profile / collect / video diversion sink |
| live abuse | content_gallery, content_forensics, social_interaction, report_signal | account_profile | sudden live, live time/region/view scale, live comments, audit hit |
| fan farming / relation anomaly | relation_graph, social_interaction, account_profile | report_signal | fan source, fans/follow quality, same-device relation, account state distribution, homogeneity |
| false positive review | report_signal + content_forensics + account_profile, account_action_log | account_change_trace | audit / label / punishment basis, user behavior support, report contamination, normal content/path, over-enforcement risk |

If `enforcement_review` is not represented as an independent capability, treat it as a composed view of `report_signal + content_forensics + account_profile`.

## 4. API-first Default Policy

Dennis sub-agent archives center queries default to API direct read.

Do not default to page / DOM / selector. Page fallback is only allowed for:

- `API failed`
- `permission_blocked`
- `response_shape_changed`
- `key_fields_missing`
- `link_url_only`
- `mapping_pending_validation`
- `need_required_param`

Default read order:

```text
API direct read
→ DOM scoped JS eval
→ row feature filter
→ scoped snapshot fallback
```

Fallback output must include the fallback reason. Failed / blocked / partial source is not counter evidence and must not be used as "no risk" proof.

## 5. API Inventory Additions

Each entry must be recorded with capability, endpoint, method, request fields, response shape, list / total / pagination fields, sensitive fields, validation status, API replacement status, and fallback condition.

| capability | endpoint | method | request fields | response shape | list / total / pagination fields | sensitive fields | validation_status | api_can_replace_dom | fallback condition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| report_signal | `/v4/archives/report/user/options` | GET | user/report context | option structure | none | reporter / target identifiers | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param / mapping_pending_validation |
| report_signal | `/v4/archives/report/user/search` | POST | userId, time/filter/page | user report list | list/total/page fields pending | reporter / target identifiers, report text | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param / key_fields_missing |
| account_change_trace | `/v4/audit/user/fourinfo/log/allTypes` | POST | userId/context | four-info type/options | none | operator / audit notes | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| account_change_trace | `/v4/audit/user/fourinfo/log/search` | POST | userId, type/time/page | four-info change list | list/total/page fields pending | old/new profile text/media URL/operator | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param / key_fields_missing |
| social_interaction | `/archives/photo/comment/search` | POST | photoId/userId/filter/page | comment list | list/total/page fields pending | comment plaintext, commenter id | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param |
| social_interaction | `/archives/photo/comment/types` | GET | comment context | type options | none | none expected | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| social_interaction | `/archives/photo/comment/status` | POST | comment context | status options | none | none expected | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| social_interaction | `/archives/photo/comment/userStatus` | POST | user/comment context | user status options | none | user identifiers | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| social_interaction | `/archives/photo/comment/queryTypes` | POST | comment context | query type options | none | none expected | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| social_interaction | `/archives/photo/comment/orders` | POST | comment context | order options | none | none expected | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| social_interaction | `/archives/photo/comment/keyMaps` | POST | comment context | key map/options | none | internal field mapping | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| report_signal | `/v4/archives/report/photo/options` | GET | photo/report context | option structure | none | reporter / target identifiers | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param / mapping_pending_validation |
| report_signal | `/v4/archives/report/photo/search` | POST | photoId/userId/filter/page | photo report list | list/total/page fields pending | reporter / target identifiers, report text | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param / key_fields_missing |
| social_interaction | `/archives/user/message/search` | POST | userId/filter/page | private message list | list/total/page fields pending | private message plaintext, counterpart id | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param / permission_blocked |
| social_interaction | `/archives/user/message/options` | POST | user message context | option structure | none | internal field mapping | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| social_interaction | `/archives/user/message/keyMaps` | POST | user message context | key map/options | none | internal field mapping | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| content_forensics | `/archives/livestream/home/info` | POST | liveId/userId | live home info | none | live media URL, anchors/users | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param |
| content_forensics | `/archives/livestream/home/meta` | POST | liveId/userId | live meta | none | full live meta JSON | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param |
| content_forensics | `/archives/livestream/home/log` | POST | liveId/userId/time | live audit/log list | list/total/page fields pending | operator / notes / raw log | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param |
| social_interaction | `/archives/livestream/comment/statistics` | POST | liveId/filter | live comment statistics | aggregate fields | comment content samples | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param |
| social_interaction | `/archives/livestream/comment/detail` | POST | liveId/filter/page | live comment detail list | list/total/page fields pending | comment plaintext, commenter id | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param / permission_blocked |
| content_gallery | `/archives/user/gallery/momentList` | POST | userId/page/filter | moment list | list/total/page fields pending | content plaintext/media URL | pending_from_har_or_screenshot_analysis | false_until_observed | key_fields_missing |
| content_gallery | `/archives/user/gallery/momentAuthority` | POST | userId/moment context | moment authority/status | none | internal status reason | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param |

Validation status rule:

- `pending_from_har_or_screenshot_analysis` means the endpoint was identified from effective action HAR / screenshot analysis but must not be written as `validated`.
- Upgrade to `validated` only after parsed API response or executed observation records request/response shape and readonly boundary.

## 6. Sensitive Field Policy

`never_output_raw`:

- cookie
- token
- tokenId
- session
- KIM code
- password
- authorization
- CSRF/XSRF
- access token / refresh token
- open_id plaintext
- sig plaintext
- deviceId plaintext
- IP plaintext
- phone plaintext
- full `requestParam`
- full `extraParam`
- full response JSON
- full video meta JSON
- full `userRouteTrace`
- full private message content
- full comment content
- related user ID / nickname / device plaintext
- avatar / background / media URL plaintext

`allowed_derived_features`:

- Field name.
- Count.
- Time range.
- State distribution.
- Operation type distribution.
- Risk label.
- Existence / absence.
- Whether abnormal.
- Device consistency conclusion.
- Content type summary.
- Repetition pattern summary.
- Diversion risk summary.
- Posting client type.
- Version difference.
- Import flag.
- Path summary.

## 7. Output Boundaries

- API direct read availability does not equal risk finalization.
- User report / photo report is an external feedback signal, not strong evidence alone.
- Same-device relation is candidate relation evidence, not direct fraud conclusion.
- Full raw API response must not be persisted into run logs or user-facing replies.
- Screenshot-visible content is not interface validation.
- Page fallback must be scoped and bounded.
- No automatic enforcement, no write actions, no batch full crawl.
