# Platform Capability Status and Cost Priority v1

## Goal

Replace the binary "API direct / non API direct" mental model with a four-level platform capability taxonomy and a low-cost-first source routing rule.

## Capability Status Taxonomy

- `api_direct_confirmed`: HTTP + SSO / controlled cookie-state can directly call structured API. Highest priority. Examples include unified login log runner, Weapon `graphData` / `riskData`, track-analysis `profile` / `getUseDuration` / `getDeviceIds` / `getLastestDateTime`, and Tianshi `fastQueryHbase`.
- `same_origin_api_confirmed`: API exists but requires browser / SPA auth activation before same-origin fetch. Higher priority than DOM. Example: parts of Archives Center.
- `partial_api_direct`: API exists but depends on precise event/source/device/time-window fields, or only some event types are stable. Examples include RCP event detail and parts of Tianshi event drilldown.
- `pending_api_direct_confirmation`: API likely exists but is not validated enough for automatic runtime use. Examples include publish audit and some long-window token / OAuth / passToken chains.

## Low-cost-first Routing

When multiple sources can answer the same question:

1. Prefer `api_direct_confirmed`.
2. Then `same_origin_api_confirmed`.
3. Then `partial_api_direct` with precise required fields.
4. Then browser UI / DOM / selector observation.
5. Use DataAgent / Hive only for long-window, cross-table, offline history, or realtime source-window gaps, and always with per-call confirmation.

## Evidence Boundaries

- Low-cost source `no_data`, `blocked`, `timeout`, or `auth_failed` is not a low-risk / no-risk conclusion.
- Incomplete time window or coverage must be marked `source_window_boundary`, `missing_evidence`, or `offline_hive_required`.
- If a later higher-quality source returns new evidence, recompute the conclusion.
- When sources conflict, prefer longer time window, fuller behavior chain, and raw behavior evidence over policy names / model scores.
- API `no_data` conflicting with Hive abnormal evidence must be explained as online-window or coverage gap.

## Modified Files

- `computer_use_poc/platform_call_playbook_index.md`
- `computer_use_poc/multi_entry_runtime_guard_v1.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/track_analysis_api_direct_contract_current.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`

## Regression Added

- `PLATFORM-CAPABILITY-STATUS-TAXONOMY-001`
- `LOW-COST-SOURCE-FIRST-001`
- `API-DIRECT-BEFORE-BROWSER-001`
- `REALTIME-API-BEFORE-DATAAGENT-001`
- `PRECISE-EVENTID-BEFORE-BROAD-SCAN-001`
- `LOW-COST-NODATA-NOT-FINAL-001`
- `SOURCE-CONFLICT-RECOMPUTE-001`

## Not Done

- Did not access real platforms.
- Did not call DataAgent.
- Did not modify gateway / safeBins / tools.
- Did not repackage release.
- Did not add or modify runners.
