# DataAgent Cloud Skill Parity Contract v1

## Summary

本轮将 DataAgent connector 从“从零设计”调整为“对齐云上已验证 Skill contract”。

云上 Dennis/DataAgent Skill 已验证 DataAgent 入口参数和 step-based response 形态。当前本地 full_runtime connector 的目标是 parity with cloud Skill，不是重新定义 DataAgent API。

## Added / Updated

- 更新 `computer_use_poc/dataagent_connector_contract_v1.md`，新增 `cloud_skill_verified_contract` 章节。
- 新增 `computer_use_poc/dataagent_cloud_skill_parity_contract_v1.md`。
- 新增 `computer_use_poc/test_fixtures/dataagent_cloud_skill_response_mock.json`，使用脱敏 step-based mock。
- 更新 `computer_use_poc/dataagent_response_normalizer.py`：
  - 支持云上 Skill mock response。
  - 只把 `MODEL_ANSWER` 作为 evidence explanation。
  - 将 `TOOL_CALL.query_id` / `TOOL_CALL.generated_sql` / trace handle 作为 provenance。
- 更新 `computer_use_poc/dataagent_connector_check.py`：
  - 增加 cloud skill parity check。
  - 输出 `cloud_skill_contract_known=true`、`local_live_verified=false`、`parity_mock_pass=true`。
- 更新 `computer_use_poc/source_executability_inventory_v1.yaml`：
  - `dataagent_hive_registry.current_status=cloud_skill_verified_contract`。
  - `local_connector_contract_ready=true`。
  - `local_live_verification_required=true`。
  - `evidence_boundary=pending_or_sql_generated_not_evidence`。
- 更新 `computer_use_poc/runtime_required_file_manifest_v1.yaml`，纳入 parity contract 和 mock fixture。
- 更新 `computer_use_poc/smoke_tests.md`，增加 cloud Skill parity、cloud verified not local live verified、MODEL_ANSWER evidence 和不重新发明 API schema 的检查。

## Contract Boundary

- 云上 Skill 已验证 DataAgent 入口参数。
- 本轮只做本地 parity contract。
- 本地仍未 live 验证，所以不得标 `local_live_verified`。
- Conversational API 仍是当前 MVP 通道。
- structured-query 仍只是设计方案，不是当前可用接口。
- DataAgent 执行仍需逐次授权。
- `MODEL_ANSWER` 才能进入 evidence explanation。
- `TOOL_CALL` / SQL / trace handle 只能作为 provenance，不能直接当业务结论。

## Boundaries This Run

- 未真实调用 DataAgent。
- 未调用 Hive。
- 未提交 SQL。
- 未改 auth / gateway / safeBins / TOOLS。
- 未打包。
- 未提交 git。

## Validation

- `PYTHONPYCACHEPREFIX=/private/tmp/codex_pycache python3 -m py_compile computer_use_poc/dataagent_response_normalizer.py computer_use_poc/dataagent_connector_check.py`: passed.
- `python3 computer_use_poc/dataagent_response_normalizer.py --input computer_use_poc/test_fixtures/dataagent_cloud_skill_response_mock.json`: passed.
  - `MODEL_ANSWER` extracted.
  - `TOOL_CALL` provenance retained as provenance only.
  - normalized status `completed`, row_count `1`.
- `python3 computer_use_poc/dataagent_connector_check.py --json`: `PASS_DATAAGENT_CONNECTOR_CONTRACT_CHECK`.
  - `cloud_skill_contract_known=true`
  - `local_live_verified=false`
  - `parity_mock_pass=true`
  - `real_dataagent_api_called=false`
  - `hive_called=false`
  - `sql_submitted=false`
- YAML parse passed for:
  - `computer_use_poc/dataagent_request_schema_v1.yaml`
  - `computer_use_poc/dataagent_response_schema_v1.yaml`
  - `computer_use_poc/source_executability_inventory_v1.yaml`
  - `computer_use_poc/runtime_required_file_manifest_v1.yaml`
- Inventory assertions passed:
  - `current_status=cloud_skill_verified_contract`
  - `local_connector_contract_ready=true`
  - `local_live_verification_required=true`
  - `expected_runtime_mode=authorized_execution_only`
  - `default_mode=dry_run_sql_generation`
  - `user_confirmation_required=true`
  - `evidence_boundary=pending_or_sql_generated_not_evidence`
- Mock fixture check passed: no `cookie` / `token` / `session` / `header` / `phone` terms.
- `python3 computer_use_poc/runtime_snapshot_builder.py --mode full_runtime`: passed, `status=created`, `copied_files_count=99`, `missing_required=[]`.
- `outputs/full_runtime/RUNTIME_MANIFEST.md` contains:
  - `computer_use_poc/dataagent_cloud_skill_parity_contract_v1.md`
  - `computer_use_poc/test_fixtures/dataagent_cloud_skill_response_mock.json`
- `python3 outputs/full_runtime/computer_use_poc/dataagent_connector_check.py --json`: `PASS_DATAAGENT_CONNECTOR_CONTRACT_CHECK`.
- forbidden path check passed for `outputs/full_runtime`.
