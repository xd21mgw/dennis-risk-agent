# Overlay Manifest

## Package Identity

- overlay_name: `dennis_risk_agent_runtime_validation_overlay_tianshi_v1`
- purpose: cloud natural-language runtime validation overlay
- source_workspace: Dennis Risk Agent local workspace
- real_platform_access: no
- DataAgent_call: no
- release_package_update: overlay only, not full release
- core_skill_modified: no

## Included Files

Core runtime validation files:

- `computer_use_poc/capability_registry.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/smoke_tests.md`
- `computer_use_poc/real_name_feature_service_partial_contract_v1.md`

Strategy governance documents:

- `computer_use_poc/strategy_governance/tianshi_strategy_governance_readonly_capability_v1.md`
- `computer_use_poc/strategy_governance/tianshi_strategy_governance_validation_cases_v1.md`
- `computer_use_poc/strategy_governance/tianshi_policy_attribution_api_read_poc_v1.md`
- `computer_use_poc/strategy_governance/single_user_event_strategy_inventory_poc_v1.md`
- `computer_use_poc/strategy_governance/business_security_scene_asset_mapping_poc_v1.md`
- `computer_use_poc/strategy_governance/non_register_login_scene_deep_validation_poc_v1.md`

Selected run logs:

- `computer_use_poc/selected_run_logs/tianshi_strategy_hit_inventory_runtime_dryrun_v1.md`
- `computer_use_poc/selected_run_logs/non_register_login_runtime_candidate_dryrun_v1.md`
- `computer_use_poc/selected_run_logs/real_name_feature_service_partial_contract_dryrun_v1.md`
- `computer_use_poc/selected_run_logs/tianshi_fast_query_hbase_poc_v1.md`
- `computer_use_poc/selected_run_logs/tianshi_policy_attribution_api_read_run_002_full_success.md`
- `computer_use_poc/selected_run_logs/tianshi_strategy_governance_readonly_capability_summary_v1.md`

Overlay control files:

- `README.md`
- `OVERLAY_MANIFEST.md`
- `OVERLAY_CHECKLIST.md`

## Explicitly Excluded

- `outputs/dist/`
- historical full `computer_use_poc/run_logs/`
- complete original Skill or Prompt source
- auth state, cookie, token, session, header, API key material
- raw platform observations or full platform JSON
- raw identity fields including ID number, ID first 6 digits, name, phone number, full birthday, full IP
- risky mock fixtures

## Capability Status Summary

Executable / readonly-capable validation candidates:

- `tianshi_strategy_governance_readonly`
- `tianshi_strategy_hit_inventory`

Beta / partial candidate:

- `tianshi_live_attach_attribution_candidate`

Query-plan-only or asset-index-only:

- `business_security_scene_asset_mapping`
- `tianshi_anticrawl_family_candidate`
- `real_name_feature_service_partial_contract`

## Key Guardrails

- `fastQueryHbase` is the preferred strategy hit inventory overview entry.
- `eventList` is only a supplement for eventType/request-level detail.
- `SYNC_LIVE_ATTACH_REQUEST` must remain beta partial and must surface `event_detail_partial`.
- Business security scene asset map is not an executable judgement capability.
- ANTICRAWL family remains candidate-only until hit samples and attribution are validated.
- Real-name feature service remains partial contract / redaction schema only and never becomes standalone identity or ATO judgement.

## Asset Scan Summary

Local command:

```bash
python3 computer_use_poc/package_asset_scanner.py outputs/release/dennis_risk_agent_runtime_validation_overlay_tianshi_v1
```

Result:

- status: warning
- package_should_block: false
- critical: 0
- high: 0
- medium: 17
- low: 0

All remaining warnings are `poc_process_file` path warnings caused by the workspace directory name and selected POC/validation documents. No blocking credential, auth material, identity raw field, prompt asset, raw platform response, full run log directory, or historical dist package finding remains.
