# Overlay Capability Registry

This file is the runtime validation overlay subset for Tianshi and real-name partial-contract acceptance. It is intentionally smaller than the workspace registry and does not register new interfaces.

| capability | purpose | status | default scope | boundary |
|---|---|---|---|---|
| `tianshi_strategy_governance_readonly` | Explain policy detail, policy tree asset, single-event policy attribution, and release record | documented_ready_for_runtime | readonly governance explanation | Not final cheating judgement; no write, launch, approval, or enforcement |
| `tianshi_strategy_hit_inventory` | Inventory strategy hits for one source/user over a bounded window | documented_ready_for_runtime | single-source strategy-hit overview | fastQueryHbase is preferred overview entry; eventList is supplement only; hit overview is not final risk judgement |
| `tianshi_live_attach_attribution_candidate` | Explain live attach / `SYNC_LIVE_ATTACH_REQUEST` blocking path | runtime_candidate_beta_partial | live attach candidate attribution | Must mark `event_detail_partial`; beta partial, not full success |
| `business_security_scene_asset_mapping` | Explain business-security scene asset map and validation priorities | asset_index_only_query_plan_only | asset index / query plan only | Not executable judgement; no platform execution |
| `tianshi_anticrawl_family_candidate` | Explain ANTICRAWL family candidate path and query plan | candidate_only_query_plan_only | query plan only | Not executable runtime; missing hit sample means no attribution claim |
| `real_name_feature_service_partial_contract` | Record EB_USER_REAL_NAME_VERILY__1 bridge parameters, field availability, and redacted output schema | partial_contract_redaction_schema_only_query_plan_only | contract / schema / query plan only | Not identity runtime; not本人/盗号 judgement; no raw identity output |

## Sub-capability Notes

`tianshi_strategy_governance_readonly`:

- `policy_detail_lookup`: policy definition, expression, versions, related tree.
- `policy_tree_asset_lookup`: tree structure, node path, bound policies, full-tree policy code list.
- `single_event_policy_attribution`: event detail, feature snapshot, condition-level attribution, node-level attribution.
- `policy_release_record_lookup`: workflow status, gray/online/termination records, version tracing.

`tianshi_strategy_hit_inventory`:

- `strategy_hit_overview_lookup`: prefer fastQueryHbase, using source_id and time window.
- `event_type_detail_supplement`: use eventList only for request/eventType detail.
- `representative_event_attribution`: use event attribution on selected representative events, not every event by default.

`tianshi_live_attach_attribution_candidate`:

- `attach_hit_overview_lookup`: overview of attach-related events.
- `attach_event_detail_supplement`: eventList and detail supplement; detail timeout must be partial.
- `attach_policy_attribution`: representative condition-level attribution for validated attach policies.

`real_name_feature_service_partial_contract`:

- access path: `/v2/rest/testCase/run`
- foreign key: `EB_USER_REAL_NAME_VERILY__1`
- `sourceId` maps to userId.
- `activityName` maps to call condition.
- required `activityName`: `MERCHANT_NEWSHOP_OPEN_AWARD`
- service-side `sid` is filled by feature configuration.
- allowed output: presence flag and derived province / city availability / age bucket / gender summary.
- forbidden output: raw ID number, ID prefix, name, full birth date, phone number, full IP, detailed address.
