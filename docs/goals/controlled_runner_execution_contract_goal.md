# Goal: Controlled Runner Execution Contract v1

## Objective

Build the minimum controlled-execution foundation for the first platform runners in Dennis full_runtime.

Scope only:
- user_login_log
- weapon_graphData
- weapon_riskData

Do not cover:
- tianshi/RCP
- track-analysis
- archives center upgrade
- DataAgent/Hive execution

This goal is local-only. Do not access real platforms. Do not call DataAgent/Hive. Do not modify auth/gateway/safeBins/TOOLS. Do not package. Do not commit.

## Background

The current full_runtime can be generated and source_executability_inventory_v1.yaml shows:
- user_login_log / weapon_graphData / weapon_riskData: runner_present_not_verified
- tianshi_strategy_hit / rcp_event_list: playbook_ready_not_runner_ready
- track_analysis: playbook_ready_not_runner_ready
- DataAgent/Hive: plan_only

We need a controlled runner contract before live readonly testing.

## Required changes

### 1. Add source runner execution contract

Create:
- computer_use_poc/source_runner_execution_contract_v1.md

Must define:
- runner may execute only inventory-registered sources
- no arbitrary_url
- no .ks_sso read
- no manual Cookie/Header
- no SmartSSOSession / sso_session_runner debugging
- no cookie/token/session/header output
- max one primary attempt plus registered fallback
- normalize all inputs before execution
- normalize all outputs into standard observation schema
- HTML / redirect / non-JSON / missing fields map to auth_failed / blocked / parse_error / source_schema_drift
- no_data is not no risk
- auth_failed / blocked / timeout / parse_error / tool_gap enter source_quality only

### 2. Add standard observation schema

Create:
- computer_use_poc/source_observation_schema_v1.yaml

Required fields:
- source_name
- source_action
- source_status
- input_normalized
  - entity_type
  - entity_id
  - time_window
  - product
  - inferred_fields
- records_count
- evidence_summary
- key_fields
- source_quality
- failure_reason
- fallback_used
- raw_reference_safe_id
- redaction_applied
- sensitive_output
- collected_at

source_status enum:
- completed
- no_data
- auth_failed
- blocked
- timeout
- parse_error
- source_schema_drift
- tool_gap
- skipped

### 3. Add controlled runner invocation plan

Create:
- computer_use_poc/controlled_runner_invocation_plan_v1.yaml

Cover:
- user_login_log
- weapon_graphData
- weapon_riskData

For each source define:
- supported_actions
- required_inputs
- optional_inputs
- default_inference
- command_entry
- dry_run_check
- live_readonly_check
- expected_output_schema
- schema_drift_policy
- failure_policy
- redaction_policy

Rules:
- user_login_log default input is user_id + bounded_time_window
- weapon_graphData supports user_id to device and device to user
- weapon_riskData requires device_id; do not fabricate device_id

### 4. Update source executability inventory

Update:
- computer_use_poc/source_executability_inventory_v1.yaml

For user_login_log / weapon_graphData / weapon_riskData add:
- controlled_execution_contract_ready: true
- observation_schema_ready: true
- live_readonly_verification_required: true

Keep current_status as runner_present_not_verified. Do not mark executable.

### 5. Add local contract check script

Create:
- computer_use_poc/controlled_runner_contract_check.py

It must only do local contract checks, no platform access.

Check:
- runner file exists
- source is registered in inventory
- invocation plan has source
- required_inputs / output_schema / failure_policy / redaction_policy exist
- forbidden behavior rules exist
- mock observation conforms to source_observation_schema_v1.yaml

Support:
python3 computer_use_poc/controlled_runner_contract_check.py --json

Output status:
- PASS_CONTROLLED_RUNNER_CONTRACT_CHECK
- FAIL_CONTROLLED_RUNNER_CONTRACT_CHECK

### 6. Update runtime manifest

Update:
- computer_use_poc/runtime_required_file_manifest_v1.yaml

Add to full_runtime_required:
- computer_use_poc/source_runner_execution_contract_v1.md
- computer_use_poc/source_observation_schema_v1.yaml
- computer_use_poc/controlled_runner_invocation_plan_v1.yaml
- computer_use_poc/controlled_runner_contract_check.py

Do not include run_logs, outputs, .ks_sso, TOOLS.md, raw HAR, cookie/header/token/session, risky fixtures, historical releases.

### 7. Update smoke tests

Update:
- computer_use_poc/smoke_tests.md

Add checks:
- user_login_log and weapon sources have controlled execution contract
- runner_present_not_verified must not be executable
- source_observation_schema_v1.yaml exists
- schema_drift_policy exists
- HTML/redirect/non-JSON maps to auth_failed/blocked/parse_error/source_schema_drift
- no_data must not mean low risk/no risk
- controlled_runner_contract_check.py supports --json

### 8. Add run log

Create:
- computer_use_poc/run_logs/controlled_runner_execution_contract_v1.md

Record:
- only user_login_log and Weapon were selected
- no real platform access
- no DataAgent/Hive
- no auth/gateway/safeBins/TOOLS changes
- no tianshi/RCP
- no track-analysis
- no packaging
- no commit
- status remains runner_present_not_verified, not live executable

## Validation

Run:

1. Python compile:
PYTHONPYCACHEPREFIX=/private/tmp/codex_pycache python3 -m py_compile computer_use_poc/controlled_runner_contract_check.py

2. YAML parse:
- computer_use_poc/source_observation_schema_v1.yaml
- computer_use_poc/controlled_runner_invocation_plan_v1.yaml
- computer_use_poc/source_executability_inventory_v1.yaml
- computer_use_poc/runtime_required_file_manifest_v1.yaml

3. Local contract check:
python3 computer_use_poc/controlled_runner_contract_check.py --json

4. Rebuild full runtime:
python3 computer_use_poc/runtime_snapshot_builder.py --mode full_runtime

5. Manifest check:
outputs/full_runtime/RUNTIME_MANIFEST.md must include the new contract/schema/plan/check files.

6. Forbidden check:
outputs/full_runtime must not contain run_logs, nested outputs, .ks_sso, TOOLS.md, cookie/header/token/session, raw HAR, risky fixtures, historical releases.

7. git diff check:
git diff --check

## Final response

Summarize:
- added files
- modified files
- validation results
- current status of user_login_log / weapon_graphData / weapon_riskData
- platform access: no
- DataAgent/Hive call: no
- auth/gateway/safeBins/TOOLS changes: no
- packaging: no
- git commit: no
