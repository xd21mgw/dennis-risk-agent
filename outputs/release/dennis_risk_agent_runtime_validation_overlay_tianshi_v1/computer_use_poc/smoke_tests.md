# Overlay Smoke Tests

These checks are scoped to `dennis_risk_agent_runtime_validation_overlay_tianshi_v1`.

## File Presence

- `README.md` exists.
- `OVERLAY_MANIFEST.md` exists.
- `OVERLAY_CHECKLIST.md` exists.
- `computer_use_poc/capability_registry.md` exists.
- `computer_use_poc/scene_to_capability_routing.md` exists.
- `computer_use_poc/answer_experience_templates.md` exists.
- `computer_use_poc/real_name_feature_service_partial_contract_v1.md` exists.
- strategy governance documents exist.
- selected run logs exist under `computer_use_poc/selected_run_logs/`.

## Capability Registration

- `tianshi_strategy_governance_readonly` exists.
- `tianshi_strategy_hit_inventory` exists.
- `tianshi_live_attach_attribution_candidate` exists and is beta partial.
- `business_security_scene_asset_mapping` exists and is asset-index / query-plan only.
- `tianshi_anticrawl_family_candidate` exists and is candidate-only / query-plan only.
- `real_name_feature_service_partial_contract` exists and is partial-contract / redaction-schema / query-plan only.

## Routing

- Event blocking question routes to single-event policy attribution.
- Policy definition question routes to policy detail lookup.
- Policy node question routes to policy tree asset lookup.
- Policy release question routes to release record lookup.
- Strategy-hit overview question routes to strategy hit inventory and prefers fastQueryHbase.
- Live attach question routes to live attach beta candidate and surfaces `event_detail_partial`.
- Business-security scene question routes to asset map and does not execute.
- ANTICRAWL question routes to candidate-only query plan.
- Real-name field question routes to partial contract.
- User risk question routes to multi-evidence orchestration and does not default to specialized capabilities.

## Boundary Checks

- Strategy hit is not final risk judgement.
- Strategy attribution is not final cheating judgement.
- Live attach candidate is not full success.
- Asset map is not executable judgement.
- ANTICRAWL is not executable runtime.
- Real-name feature service is not identity runtime and not standalone ATO judgement.
- Sensitive identity fields are not output; only derived summaries are allowed.
- No DataAgent call.
- No real platform access.
- No new interface.
- No write action, launch, approval, or enforcement.
