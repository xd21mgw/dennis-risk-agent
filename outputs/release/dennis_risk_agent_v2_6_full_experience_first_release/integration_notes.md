# Dennis Risk Agent v2.6 Full Experience-First Integration Notes

## 1. Integration Position

Use this directory as the full cloud internal Agent integration package.

Do not integrate `outputs/release/dennis_risk_agent_v2_6_experience_first_release/` alone. That directory is an experience addendum and lacks the full v2.4 runtime-plus base.

## 2. Recommended Load Order

1. Core runtime base:
   - `dennis_risk_agent_v2_4_runtime_plus_manifest_v1.md`
   - `integration_quick_start.md`
   - `dennis_risk_agent_v2_4_startup_loading_order_checklist_v1.md`
   - `query_intent_schema_v2.md`

2. ATO and domain runtime:
   - `account_security_expert_skill.md`
   - `ato_runtime_slim_manifest_v1.md`
   - `ato_short_question_entrypoint_adaptation_v1.md`
   - related `*_runtime_summary_v1.md` files

3. DataAgent boundary:
   - `dataagent_provider_boundary_overlay_v1.md`
   - `dataagent_conclusion_thresholds_v1.md`
   - `data_join_paths_v1.md`
   - `dataagent_timeout_policy_review_v1.md`

4. Experience-first layer:
   - `computer_use_poc/user_experience_golden_cases.md`
   - `computer_use_poc/answer_experience_templates.md`
   - `computer_use_poc/scene_to_capability_routing.md`

5. Observation and readonly hand contracts:
   - `computer_use_poc/observation_contract_v2_4_6.md`
   - `computer_use_poc/observation_schema.md`
   - `computer_use_poc/readonly_safety_rules.md`
   - specific hand playbooks only when routed

6. Smoke and regression:
   - `computer_use_poc/smoke_tests.md`
   - `computer_use_poc/run_logs/user_experience_golden_cases_dry_run_001.md`
   - `computer_use_poc/run_logs/entity_resolution_user_device_text_regression_run_v2_6_0.md`

## 3. Runtime Behavior Rules

Users still ask business questions, not platform questions. The Agent should:

- Identify the scene first.
- Select the minimum necessary capabilities.
- Avoid over-querying and unnecessary platform calls.
- Summarize conclusion / explanation first, then evidence and uncertainty.
- Keep supporting evidence, counter evidence, missing evidence, and next checks separate.

## 4. Failure / Missing Input Handling

Use explicit blockers instead of fabricating conclusions:

- `missing_device_id`: Device SDK requires a deviceId; if user gives userId, run user-to-device entity resolution first.
- `missing_required_input`: ask for the missing minimal input or route to entity resolution when possible.
- `permission_blocked`: treat as missing evidence / blocker, not no risk.
- `api_failed`: treat as source failure, not no data.
- `auth_required`: stop and request auth recovery; do not continue platform clicking.

## 5. Safety Rules

- Do not print cookie, token, session, storageState, KIM code, auth headers, or credential raw values.
- Do not copy full JSON payloads from internal tools.
- Do not recommend punishment or enforcement from one source alone.
- Do not classify ATO / cheating / group control from a single strategy hit, a single login failure, or a single device association.
- Keep DataAgent / Hive limited to batch, historical, and offline aggregate analysis.

## 6. First Cloud Verification

After integration, verify in this order:

1. ATO user judgment golden case.
2. Login failure / verification reason explanation golden case.
3. Device-risk input completeness branch: userId input must go through user-to-device entity resolution before Device SDK.
