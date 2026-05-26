# v2.6.1 Archives API-first Core Capability Map

## 1. Version Positioning

v2.6.1 is the archives center API-first core capability map. It is not a new
platform and is not a continuation branch of v2.4.x. v2.4.x remains historical
validation record; v2.6.1 reorganizes archives center from page / Tab reading
into risk capability packages.

Current status:

- `v2_6_1_capability_smoke_test` passed for the API-first capability loop.
- All 8 capability packages completed API-first smoke coverage.
- 6 capability packages basically succeeded.
- 2 capability packages remain partial.
- This is a capability smoke test, not a full API regression.
- Page / DOM / selector were not triggered by default.
- Fallback only triggered under allowed conditions.
- No sensitive plaintext output, auth export, write action, risk finalization, or enforcement suggestion.

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

Smoke-test status:

- `/archives/user/home/info`: success.
- `/archives/user/home/getUserLabel`: success.
- `/archives/draco/getPunishStatus`: user-level unsupported; photo-level and live-level are validated.
- Photo-level payload: `{ "targetId": "<photoId>", "targetType": "PHOTO" }`.
- Live-level payload: `{ "targetId": "<liveStreamId>", "targetType": "LIVE_STREAM" }`.
- `targetType` must be uppercase. Lowercase `"photo"` returns 412; live-level uses `"LIVE_STREAM"`, not `"LIVE"`.

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

Smoke-test status:

- `/v4/audit/user/fourinfo/log/search`: success.
- Current sample returned `empty_result`; do not interpret empty result as no profile change.

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
- Smoke-test status: `/v3/user/log/coreLogs/fetch` success.
- Current sample returned `empty_result`; do not interpret empty result as no operation log.

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

Smoke-test status:

- `/v3/user/gallery/photo/list`: success, observed `total=746`.
- `/v4/archives/gallery/live/list`: success with `empty_result`.
- `/archives/user/gallery/momentList`: success with `empty_result`.
- Empty gallery/live/moment result is source output, not a no-risk conclusion.

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

Smoke-test status:

- `/v3/photo/profile`: success.
- `/v3/photo/meta`: success.
- `/v3/photo/report/aggregate`: success.
- `/archives/photo/home/userAutonomy`: success.
- `photo/meta` did not expose `publishDevice` / `publishVersion` / `isImport` in the smoke sample; use `profile.uploadSource` / `photoMethod` and related profile fields as proxy features when meta fields are missing.

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

Smoke-test status:

- `/archives/user/message/search`: success, but observed `total=4029930781` appears to be an internal counter or unreliable total; do not use it as true message volume. Record `list_len` and response field structure instead.
- `/archives/photo/comment/search`: success.
- `/v3/user/profile/relation/fans/list`: success.
- `/v3/user/profile/relation/follow/list`: success.

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

Smoke-test status:

- `/v4/archives/report/user/search`: success with `empty_result`.
- `/v4/archives/report/photo/search`: follow-up validation passed; `code/result=1`, `totalCount=292`, and `dataList.length=20` observed for the corrected payload.
- Correct payload uses `reportedIds=<user_id>`, `begin` / `end` millisecond timestamps, `sort`, `page`, `count`, and string values for `matchType` / `sort`.
- Previous 500 was caused by wrong payload field names and semantics, not by endpoint unavailability.
- `report_signal` status: `user_report_search=validated`, `photo_report_search=validated`.

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

- `/archives/user/search/device type=0 / type=1` interfaces are usable and mapping validated by page entry wording plus request payload relation.
- Correct payload shape is `{keyword, inputType: 0, type}`.
- `type=0` means same-device registered users.
- `type=1` means same-device login users.
- Do not use the old `{userId, source, type}` payload shape.

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
| report_signal | `/v4/archives/report/user/search` | POST | userId, time/filter/page | user report list | empty_result observed in smoke sample | reporter / target identifiers, report text | smoke_validated_empty_result | true_for_observed_shape | key_fields_missing / empty_result_not_counter_evidence |
| account_change_trace | `/v4/audit/user/fourinfo/log/allTypes` | POST | userId/context | four-info type/options | none | operator / audit notes | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| account_change_trace | `/v4/audit/user/fourinfo/log/search` | POST | userId, type/time/page | four-info change list | empty_result observed in smoke sample | old/new profile text/media URL/operator | smoke_validated_empty_result | true_for_observed_shape | need_required_param / empty_result_not_counter_evidence |
| social_interaction | `/archives/photo/comment/search` | POST | photoId/userId/filter/page | comment list | list_len and field structure observed | comment plaintext, commenter id | smoke_validated | true_for_observed_shape | need_required_param |
| social_interaction | `/archives/photo/comment/types` | GET | comment context | type options | none | none expected | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| social_interaction | `/archives/photo/comment/status` | POST | comment context | status options | none | none expected | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| social_interaction | `/archives/photo/comment/userStatus` | POST | user/comment context | user status options | none | user identifiers | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| social_interaction | `/archives/photo/comment/queryTypes` | POST | comment context | query type options | none | none expected | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| social_interaction | `/archives/photo/comment/orders` | POST | comment context | order options | none | none expected | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| social_interaction | `/archives/photo/comment/keyMaps` | POST | comment context | key map/options | none | internal field mapping | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| report_signal | `/v4/archives/report/photo/options` | GET | photo/report context | option structure | none | reporter / target identifiers | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param / mapping_pending_validation |
| report_signal | `/v4/archives/report/photo/search` | POST | `reportedIds=<user_id>`, `matchType` string, `sort` string, `begin/end` ms, `page/count` | photo report list | `totalCount`, `dataList`, page/count | reporter / target identifiers, report text | validated | true | API failed / permission_blocked / response_shape_changed / key_fields_missing |
| social_interaction | `/archives/user/message/search` | POST | userId/filter/page | private message list | list_len observed; total unreliable | private message plaintext, counterpart id | smoke_validated_partial_total_unreliable | true_for_list_shape_only | total_semantics_untrusted / permission_blocked |
| social_interaction | `/archives/user/message/options` | POST | user message context | option structure | none | internal field mapping | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| social_interaction | `/archives/user/message/keyMaps` | POST | user message context | key map/options | none | internal field mapping | pending_from_har_or_screenshot_analysis | false_until_observed | mapping_pending_validation |
| content_forensics | `/archives/livestream/home/info` | POST | liveId/userId | live home info | none | live media URL, anchors/users | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param |
| content_forensics | `/archives/livestream/home/meta` | POST | liveId/userId | live meta | none | full live meta JSON | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param |
| content_forensics | `/archives/livestream/home/log` | POST | liveId/userId/time | live audit/log list | list/total/page fields pending | operator / notes / raw log | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param |
| social_interaction | `/archives/livestream/comment/statistics` | POST | liveId/filter | live comment statistics | aggregate fields | comment content samples | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param |
| social_interaction | `/archives/livestream/comment/detail` | POST | liveId/filter/page | live comment detail list | list/total/page fields pending | comment plaintext, commenter id | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param / permission_blocked |
| content_gallery | `/archives/user/gallery/momentList` | POST | userId/page/filter | moment list | empty_result observed in smoke sample | content plaintext/media URL | smoke_validated_empty_result | true_for_observed_shape | key_fields_missing / empty_result_not_counter_evidence |
| content_gallery | `/archives/user/gallery/momentAuthority` | POST | userId/moment context | moment authority/status | none | internal status reason | pending_from_har_or_screenshot_analysis | false_until_observed | need_required_param |

Validation status rule:

- `pending_from_har_or_screenshot_analysis` means the endpoint was identified from effective action HAR / screenshot analysis but must not be written as `validated`.
- Upgrade to `validated` only after parsed API response or executed observation records request/response shape and readonly boundary.
- `smoke_validated` means the endpoint completed a v2.6.1 API-first capability smoke-test loop for the observed request shape only. It is not full API regression.
- `smoke_validated_empty_result` means request/response shape was observed but the sample returned empty; empty result must not be interpreted as no behavior or no risk.
- `/v4/archives/report/photo/search` is upgraded to `validated` in the follow-up patch only for the corrected payload shape above.
- `server_error_500_request_shape_uncertain_pending` remains pending for other endpoints or unvalidated payload shapes and must not be treated as validated.

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
