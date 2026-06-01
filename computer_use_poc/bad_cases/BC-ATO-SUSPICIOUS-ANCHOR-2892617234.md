# BC-ATO-SUSPICIOUS-ANCHOR-2892617234

## Background

User asked: `2892617234 这个账号是不是被盗了？`

The previous runtime entered a flat source-status path: Track, RCP, Weapon, login logs, and Archives were summarized as partial evidence / source gaps. It did not first discover suspicious anchors. Only after the user added the key clue, `WEB 登录发了导流视频`, did the answer move to the correct ATO path.

## Root Problem

ATO single-case reasoning must not start from a platform inventory. It must start from:

```text
user_id
-> suspicious_anchor_discovery
-> login/control-chain or content/action anchor
-> candidate_control_endpoint_extraction
-> device_identity_consistency
-> historical_baseline_comparison
-> business evidence card
```

The failure pattern was:

- No automatic discovery of suspicious device / suspicious action anchor.
- Track was over-weighted as owner or normal-device support.
- `response_too_large` from login logs risked being interpreted as login evidence.
- Device risk was reduced to `device_id` instead of device identity consistency.
- User-facing answer exposed runtime process concepts instead of a business evidence card.

## Correct ATO Mainline

For a naked ATO question, Dennis must actively seek:

- recent login / WEB login
- scan / OAuth / one-click / token / session
- resetPwd / account protection / kick out
- abnormal publish, live, comment, DM
- profile change and four-items change
- strategy-hit anchor

Each anchor should extract candidate control endpoint fields:

- action and time
- device_id, model, OS, OS version, app version
- UA, IP, province, city, ASN
- login source and login type
- browser fingerprint
- session_id, request_id, event_id
- content_id, photo_id, live_id, comment_id
- source_name, source_status, source_quality

If no anchor is found, the user-facing answer must say `未完成可疑锚点发现`, not a generic `证据不足`.

## Device Identity Consistency

`device_id` is not sufficient identity proof. A common device_id can still be suspicious if other identity variables drift.

Required comparison:

- device_id historical commonness
- first-seen time
- 30/90/180-day active days
- device model
- OS / OS version
- app version
- UA
- browser fingerprint
- IP / province / city / ASN
- login source
- login type

Risk tags:

- `device_identity_inconsistency`
- `possible_device_id_spoofing`
- `common_device_id_but_abnormal_fingerprint`
- `common_device_id_not_sufficient_to_exclude_ato`

Required wording when applicable:

```text
device_id 看似常用，但设备身份变量不一致，存在伪装常用设备或 session/token 接管嫌疑。
```

## Track Boundary

Track activity can only support frontend activity context. It cannot prove owner operation and cannot exclude ATO.

If backend WEB/session/API content action exists but Track has no matching frontend activity, mark:

- `front_backend_activity_mismatch`

## Login Log Contract Boundary

`response_too_large` means wrapper/source contract gap. It is not evidence of high login volume and cannot enter completed login evidence.

If UI shows no data while wrapper returns `response_too_large`, mark:

- `wrapper_response_mismatch`
- `source_contract_gap`
- `actual_ui_no_data_unverified_by_wrapper`
- `login_log_evidence_unusable`

If an anchor time exists, shrink the login query to anchor time +/- 2-6 hours. If no anchor time exists, do anchor discovery first instead of widening the query window.

## Content Action Deep Dive

If WEB publish, diversion video, abnormal content, or user-claimed abnormal publish is discovered or suspected, enter `content_action_deep_dive`.

Fields:

- photo_id / content_id
- publish time
- publish source
- publish device
- publish IP / UA
- audit / strategy / diversion reason
- four-items change
- time delta to login anchor
- candidate session / request id
- historical publish baseline

## User-Facing Output

Use business language and this order:

1. Conclusion
2. Suspicious action anchors
3. Candidate control endpoint / device identity consistency
4. Login-chain evidence
5. Content / four-items / post-action evidence
6. Historical baseline
7. Evidence gaps
8. Next evidence / handling suggestion

Do not show:

- `routing_metadata`
- `source_quality` YAML
- `boundary_flags`
- `execution_mode`
- validator fields
- platform debug YAML

## Regression Added

Runtime validation cases:

- `ATO-SINGLE-NAKED-QUESTION-ANCHOR-FIRST-001`
- `ATO-NAKED-QUESTION-ACTION-DISCOVERY-001`
- `ATO-WEB-PUBLISH-DEEP-DIVE-001`
- `ATO-PUBLISH-VIDEO-ANCHOR-001`
- `ATO-COMMON-DEVICE-ID-SPOOFING-001`
- `ATO-DEVICE-ID-NOT-SOLE-IDENTITY-001`
- `ATO-COMMON-DEVICE-NOT-EXCLUSION-001`
- `TRACK-NOT-PROOF-OF-OWNER-001`
- `TRACK-BACKEND-MISMATCH-001`
- `LOGIN-RESPONSE-TOO-LARGE-NOT-EVIDENCE-001`
- `LOGIN-UI-NODATA-WRAPPER-LARGE-MISMATCH-001`
- `ATO-LOGIN-HIVE-REGISTRY-FIRST-001`
- `USER-FACING-NO-ROUTING-METADATA-001`
- `SOURCE-PLAN-NOT-FLAT-SOURCE-SUMMARY-001`

