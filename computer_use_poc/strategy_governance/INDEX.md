# strategy_governance Index

Status: strategy governance and Tianshi/RCP readonly capability navigation.
This directory is included by the runtime manifest glob and is high-risk for
path moves.

## Capability / Runtime-support Files

| file | purpose | move risk |
|---|---|---|
| `tianshi_strategy_governance_readonly_capability_v1.md` | Strategy governance readonly capability. | high |
| `tianshi_strategy_governance_validation_cases_v1.md` | Strategy governance validation cases. | high |
| `tianshi_policy_attribution_api_read_poc_v1.md` | Policy attribution API-read POC and contract context. | high |
| `single_user_event_strategy_inventory_poc_v1.md` | Single-user event strategy inventory POC. | high |
| `business_security_scene_asset_mapping_poc_v1.md` | Business-security scene asset mapping POC. | high |
| `non_register_login_scene_deep_validation_poc_v1.md` | Non-register/login scene deep validation POC. | high |

## Boundary

- Strategy hits and policy attribution are readonly evidence or governance
  context; they do not by themselves produce final cheating or ATO conclusions.
- Do not move these files without manifest, smoke, routing, and answer-template
  reference checks.
- This index follows `docs/architecture/runtime_directory_consolidation_plan_v1.md`.
