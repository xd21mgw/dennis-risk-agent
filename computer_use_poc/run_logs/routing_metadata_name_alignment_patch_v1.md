# routing_metadata name alignment patch v1

## Goal

Fix unstable `routing_metadata` field naming observed during activation validation. Case 1 used exact names, while Case 2 and Case 3 emitted `route=dennis-risk-agent` and unregistered capability names such as `strategy_attribution` and `user_risk_profile`.

## Problem

The metadata block existed and correctly marked:

- `platform_called=false`
- `dataagent_called=false`
- `sensitive_output=false`
- `redaction_applied=true`

But route and capability names were not consistently aligned to registry/routing names, making main-agent parsing and acceptance checks unreliable.

## Files Updated

- `AGENTS.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/smoke_tests.md`
- `computer_use_poc/README.md`

## Added Hard Rules

1. `route` must use a formal route name from `scene_to_capability_routing.md`.
2. `capability` must use a formal capability name from `capability_registry.md`.
3. `sub_capability` must use a formal sub-capability name; use `null` when none exists.
4. `boundary_flags` must use standard flag names, not semantic variants.
5. `route` must never be an agent name such as `dennis-risk-agent`.
6. `capability` must never be an unregistered invented name such as `strategy_attribution` or `user_risk_profile`.
7. If unsure, use `multi_evidence_orchestration` instead of inventing a new name.

## Standard Mapping Table

| User intent | route | capability | sub_capability | required boundary_flags |
|---|---|---|---|---|
| eventId 为什么被阻止 | `single_event_policy_attribution` | `tianshi_strategy_governance_readonly` | `single_event_policy_attribution` | `attribution_not_cheating_judgement` |
| 这条策略是什么 | `policy_detail_lookup` | `tianshi_strategy_governance_readonly` | `policy_detail_lookup` | `expression_not_business_causality` |
| 策略挂在哪个节点 | `policy_tree_asset_lookup` | `tianshi_strategy_governance_readonly` | `policy_tree_asset_lookup` | `policy_tree_asset_not_event_hit_path` |
| 策略什么时候上线 | `policy_release_record_lookup` | `tianshi_strategy_governance_readonly` | `policy_release_record_lookup` | `release_record_not_risk_judgement` |
| 用户最近命中过哪些策略 | `tianshi_strategy_hit_inventory` | `tianshi_strategy_hit_inventory` | `strategy_hit_overview_lookup` | `strategy_hit_not_final_risk_judgement` |
| 一天内哪些策略反复命中 | `tianshi_strategy_hit_inventory` | `tianshi_strategy_hit_inventory` | `strategy_hit_overview_lookup` | `cooccurrence_not_attack_path_conclusion` |
| 直播长连接为什么被拦 | `tianshi_live_attach_attribution_candidate` | `tianshi_live_attach_attribution_candidate` | `attach_policy_attribution` | `live_attach_beta_partial`, `event_detail_timeout_not_no_data` |
| 业务安全有哪些场景 | `business_security_scene_asset_mapping` | `business_security_scene_asset_mapping` | `null` | `asset_map_not_executable` |
| ANTICRAWL 怎么查 | `tianshi_anticrawl_family_candidate` | `tianshi_anticrawl_family_candidate` | `null` | `anticrawl_candidate_only`, `not_executable_runtime` |
| 实名能否输出身份证前6位 | `real_name_feature_service_partial_contract` | `real_name_feature_service_partial_contract` | `null` | `real_name_no_raw_identity`, `not_identity_runtime` |
| 实名省份和 IP 一致是否排除盗号 | `multi_evidence_orchestration` | `account_security_expert_mode` | `null` | `province_match_not_ato_exclusion`, `real_name_not_standalone_evidence` |
| 用户有没有风险 | `multi_evidence_orchestration` | `account_security_expert_mode` | `null` | `generic_risk_no_default_specialized_capability` |

## New Smoke Coverage

- `routing_metadata.route` must not equal `dennis-risk-agent`.
- `routing_metadata.capability` must not be `strategy_attribution` or `user_risk_profile`.
- “这个用户最近命中过哪些策略” must map to `tianshi_strategy_hit_inventory`.
- “帮我看下这个用户有没有风险” must map to `multi_evidence_orchestration`.
- `boundary_flags` must use exact standard flag names.

## Boundaries

- real_platform_access: no
- DataAgent_call: no
- new_interface_added: no
- release_package_updated: no
- new_capability_registered: no
- git_commit: no
