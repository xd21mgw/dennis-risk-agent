# Platform Access Execution v0.1 Hardening Run Log

## Purpose

This patch converts recent platform-access learnings into execution contracts for Dennis Risk Agent. The goal is not to package authentication state or write another auth diagnosis document. The goal is to make platform calling chains, runner invocation, same-origin adapters, parameter contracts, failure taxonomy, observation schema, and regression expectations explicit.

## Added

- `computer_use_poc/platform_access/platform_access_inventory_v0_1.yaml`
- `computer_use_poc/platform_access/observation_schema_v0_1.yaml`
- `computer_use_poc/platform_access/failure_taxonomy_v0_1.yaml`
- `computer_use_poc/platform_access/runner_invocation_contract_v0_1.md`
- `computer_use_poc/platform_access/browser_same_origin_adapter_contract_v0_1.md`
- `computer_use_poc/platform_access/weapon_api_contract_v0_1.yaml`
- `computer_use_poc/platform_access/tianshi_rcp_api_contract_v0_1.yaml`
- `computer_use_poc/platform_access/login_log_api_contract_v0_1.yaml`
- `computer_use_poc/platform_access/archives_center_contract_v0_1.yaml`
- `computer_use_poc/platform_access/track_analysis_api_contract_v0_1.yaml`
- `computer_use_poc/platform_access/source_orchestration_examples_v0_1.md`
- `computer_use_poc/bin/sso_session_runner`

## Key Rules

- First classify invocation chain, then auth.
- First classify parameter contract, then permission.
- First classify local API/path availability, then platform availability.
- RCP `eventList` on `rcp.corp.kuaishou.com` is the primary strategy-hit event source.
- `fastQueryHbase` is fallback and must not block the RCP primary chain.
- Weapon `graphData` and `riskData` use `/apiv2/*`; `riskData` is a direct deviceId source.
- Same-origin API failures are not automatically auth failures.
- All platform hands output `platform_access_observation`, `source_quality`, redaction state, and next action.

## HAR / Historical Contract Extraction

This patch used local HAR / historical run-log structure only for endpoint paths, parameter keys, response keys, and schema shape. It did not copy credential material or raw sensitive observations.

RCP / eventList:

- HAR confirmed `POST /v2/rest/event/eventList` on `rcp.corp.kuaishou.com`.
- HAR confirmed request keys: `tableHeaderList`, `pageIndex`, `pageSize`, `eventV2`, `startTime`, `endTime`, `currentTime`.
- HAR confirmed `eventV2` keys: `eventType`, `hitPolicies`, `version`, `status`, `snapshotVersion`, `sourceIds`, `realTimeOp`, `isPolicyTreeExperiment`, `conditionList`, `grayFeature`, `grayQueryStatus`, `region`.
- HAR confirmed table / response fields such as `sourceId`, `eventId`, `_occurTime`, `_realTimeOp`, `_errorCode`, `_sideEffectOps`, `time`, `photoId`, `deviceId`, `hitFusePolicyCode`, `userRegisterIp`, `ipCity_zh`, `openId`.
- Custom policy-code fields remain field-level partial when not observed; the overall eventList chain is not unknown.

Track-analysis:

- HAR confirmed `/dp/platform/app/analytics/v2/sequence/getLastestDateTime`, `getDeviceIds`, `getUseDuration`, and `profile`.
- `getUseDuration.rows` is `{date, duration}` object array.
- `profile` uses `startTime/endTime` millisecond fields and `secondLevelProfile` label-value pairs.
- Unobserved userId/deviceId request variants are marked `needs_har_confirmation`, not whole-source unknown.

Archives / audit:

- Historical archives inventories and run logs confirm user home/profile, labels, shop/status, punishment status, device search, report/photo/message/comment/live/moment-related paths at varying validation levels.
- Archives user analysis remains ATO P0. Publish chain and publish device are P0-conditional for abnormal publish cases.
- Audit reason, audit time, and punishment time are time-window anchors only and do not independently classify ATO.

## Not Done

- Did not access real platforms.
- Did not call DataAgent/Hive.
- Did not modify auth, gateway, safeBins, tools, or TOOLS.md.
- Did not output or save cookie/token/session/header/password.
- Did not copy raw HAR material.
- Did not build a full runtime release.
- Did not submit git.
