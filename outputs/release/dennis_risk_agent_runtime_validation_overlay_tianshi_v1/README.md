# Dennis Risk Agent Runtime Validation Overlay - Tianshi v1

This overlay is a runtime validation patch package for cloud-side natural-language acceptance. It only carries already-closed local registry, routing, answer template, smoke test, strategy governance documents, selected run logs, and the real-name partial contract.

It is not a full release package and does not add new platform interfaces.

## Included Capability Scope

| capability | status | runtime expectation |
|---|---|---|
| `tianshi_strategy_governance_readonly` | documented ready for runtime | readonly explanation across policy detail, policy tree asset, single-event attribution, and release record |
| `tianshi_strategy_hit_inventory` | documented ready for runtime | strategy hit inventory with fastQueryHbase as preferred overview entry and eventList as supplement |
| `tianshi_live_attach_attribution_candidate` | runtime candidate beta partial | live attach / `SYNC_LIVE_ATTACH_REQUEST` attribution candidate; must mark `event_detail_partial` when detail times out |
| `business_security_scene_asset_mapping` | asset index only / query plan only | scene asset map, not executable judgement |
| `tianshi_anticrawl_family_candidate` | candidate only / query plan only | ANTICRAWL query-plan path, not executable attribution runtime |
| `real_name_feature_service_partial_contract` | partial contract / redaction schema only / query plan only | EB_USER_REAL_NAME_VERILY__1 contract and redacted output schema; not identity runtime |

## Validation Boundaries

- Do not access real internal platforms from this overlay.
- Do not call DataAgent.
- Do not add interfaces.
- Do not register asset map as executable runtime.
- Do not register ANTICRAWL as executable runtime.
- Do not register real-name feature service as identity runtime.
- Do not output raw identity fields, credentials, auth material, raw platform JSON, or full private messages/comments.
- Do not treat strategy hit, policy attribution, live attach beta evidence, or real-name derived fields as final risk judgement.

## Selected Run Logs

Selected source run logs are copied under `computer_use_poc/selected_run_logs/` rather than the full historical `computer_use_poc/run_logs/` tree. This keeps the overlay focused and avoids packaging unrelated process history.

## How to Validate

1. Read `OVERLAY_MANIFEST.md` for included files and capability status.
2. Run the natural-language cases in `OVERLAY_CHECKLIST.md`.
3. Confirm routing follows `computer_use_poc/scene_to_capability_routing.md`.
4. Confirm answer boundaries follow `computer_use_poc/answer_experience_templates.md`.
5. Confirm no case triggers real platform access, DataAgent, write actions, or sensitive raw output.
