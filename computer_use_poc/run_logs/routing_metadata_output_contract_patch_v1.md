# routing_metadata output contract patch v1

## Goal

Add a unified `routing_metadata` output block to dennis-risk-agent formal answers so main agent, observation logs, and runtime validation can parse the child agent final route and boundary decisions from the final answer text.

## Problem Addressed

Tianshi overlay activation can spawn dennis-risk-agent correctly and avoids direct exec bypass, but session history visibility is limited. Main agent cannot reliably inspect child session internals, so route / capability / boundary validation can be marked partial. The metadata block solves this by making the final route observable in-band.

## Files Updated

- `AGENTS.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/smoke_tests.md`
- `computer_use_poc/README.md`

## Metadata Schema

```yaml
routing_metadata:
  route: "<final_route>"
  capability: "<selected_capability>"
  sub_capability: "<selected_sub_capability_or_null>"
  intent_type: "<user_intent_type>"
  execution_mode: "execution | query_plan | expert_analysis | refusal | partial"
  query_plan_only: true
  platform_called: false
  platform_call_summary: []
  dataagent_called: false
  sensitive_output: false
  redaction_applied: true
  boundary_flags:
    - "<boundary_flag>"
  missing_required_fields: []
  partial_reason: null
  final_status: "answered | needs_input | partial | refused | failed"
```

## Covered Dry-run Cases

| case | expected route | required metadata boundary |
|---|---|---|
| 单事件策略归因缺字段 | `single_event_policy_attribution` | `final_status=needs_input`, missing event fields |
| 策略详情 | `policy_detail_lookup` | policy expression is not full causality |
| 策略命中盘点 | `tianshi_strategy_hit_inventory` | `strategy_hit_not_final_risk_judgement` |
| live attach | `tianshi_live_attach_attribution_candidate` | `live_attach_beta_partial`, `event_detail_timeout_not_no_data` |
| 业务安全资产地图 | `business_security_scene_asset_mapping` | `query_plan_only=true`, `asset_map_not_executable` |
| ANTICRAWL | `tianshi_anticrawl_family_candidate` | `query_plan_only=true`, `anticrawl_candidate_only`, `not_executable_runtime` |
| 实名字段边界 | `real_name_feature_service_partial_contract` | `real_name_no_raw_identity`, `not_identity_runtime` |
| 泛风险问题 | `multi_evidence_orchestration` | `generic_risk_no_default_specialized_capability` |

## Boundaries

- This patch does not change risk judgement logic.
- This patch does not add platform interfaces.
- `platform_called` and `dataagent_called` must reflect actual calls in the current answer.
- Sensitive raw output should remain `false`; safety refusals should still emit metadata.
- Query-plan-only capabilities must not be promoted to executable runtime through metadata.

## Execution Boundary

- real_platform_access: no
- DataAgent_call: no
- new_interface_added: no
- release_package_updated: no
- core_skill_large_edit: no

## Status

ready_for_runtime_validation_overlay_sync
