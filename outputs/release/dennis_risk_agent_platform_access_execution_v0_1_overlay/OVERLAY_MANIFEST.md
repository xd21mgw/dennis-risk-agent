# Overlay Manifest

## Package

- name: `dennis_risk_agent_platform_access_execution_v0_1_overlay`
- type: runtime overlay
- purpose: synchronize Platform Access Execution v0.1 into internal Agent / dennis-risk-agent runtime for minimum smoke validation

## Included Files

- `README.md`
- `OVERLAY_MANIFEST.md`
- `INTERNAL_AGENT_VALIDATION_LIST.md`
- `AGENTS.md`
- `computer_use_poc/bin/sso_session_runner`
- `computer_use_poc/platform_access/platform_access_inventory_v0_1.yaml`
- `computer_use_poc/platform_access/observation_schema_v0_1.yaml`
- `computer_use_poc/platform_access/failure_taxonomy_v0_1.yaml`
- `computer_use_poc/platform_access/runner_invocation_contract_v0_1.md`
- `computer_use_poc/platform_access/browser_same_origin_adapter_contract_v0_1.md`
- `computer_use_poc/platform_access/weapon_api_contract_v0_1.yaml`
- `computer_use_poc/platform_access/tianshi_rcp_api_contract_v0_1.yaml`
- `computer_use_poc/platform_access/login_log_api_contract_v0_1.yaml`
- `computer_use_poc/platform_access/archives_center_contract_v0_1.yaml`
- `computer_use_poc/platform_access/track_analysis_api_contract_v0_1.yaml`
- `computer_use_poc/platform_access/source_orchestration_examples_v0_1.md`
- `computer_use_poc/multi_entry_runtime_guard_v1.md`
- `computer_use_poc/source_orchestration_plan_v1.yaml`
- `computer_use_poc/platform_call_playbook_index.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`
- `computer_use_poc/run_logs/platform_access_execution_v0_1_hardening.md`

## Main Capabilities

- standard runner wrapper;
- RCP `eventList` main entry;
- `fastQueryHbase` fallback;
- Weapon `graphData` / `riskData`;
- login log fixed window;
- Archives Center P0 / publish chain;
- track-analysis event-day activity;
- unified `platform_access_observation` schema;
- failure taxonomy.

## Explicitly Excluded

- raw HAR files;
- raw observations;
- authentication state;
- cookie / token / session / header / password material;
- DataAgent/Hive query results;
- unrelated run logs or full run log directory;
- full runtime release packages;
- `outputs/dist`;
- `outputs/intermediate`.
