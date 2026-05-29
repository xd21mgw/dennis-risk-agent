# DataAgent Connector Contract v1

## Summary

本轮基于 DataAgent API 对接说明，为 Dennis full_runtime 新增 DataAgent connector contract。

当前可用入口是 Conversational API：

```text
POST https://video-data.corp.kuaishou.com/v1/chat/completions/full
```

本轮只做本地 contract、request schema、response schema、prompt templates、mock response normalizer 和 connector check，不真实调用 DataAgent API，不调用 Hive，不提交 SQL。

## Added / Updated

- 新增 `computer_use_poc/dataagent_connector_contract_v1.md`。
- 新增 `computer_use_poc/dataagent_request_schema_v1.yaml`。
- 新增 `computer_use_poc/dataagent_response_schema_v1.yaml`。
- 新增 `computer_use_poc/dataagent_prompt_templates_v1.md`。
- 新增 `computer_use_poc/dataagent_response_normalizer.py`。
- 新增 `computer_use_poc/dataagent_connector_check.py`。
- 更新 `computer_use_poc/source_executability_inventory_v1.yaml`：
  - `dataagent_hive_registry` 从 `plan_only` 推进到 `connector_contract_ready`。
  - `expected_runtime_mode=authorized_execution_only`。
  - `default_mode=dry_run_sql_generation`。
  - `user_confirmation_required=true`。
  - `live_api_verification_required=true`。
- 更新 `computer_use_poc/runtime_required_file_manifest_v1.yaml`，将 DataAgent connector 文件纳入 full_runtime。
- 更新 `computer_use_poc/smoke_tests.md`，增加 DataAgent connector、Conversational API、MODEL_ANSWER evidence、逐次授权、敏感字段拦截和 dry-run SQL 边界检查。

## Contract Boundary

- Conversational API 是当前 MVP 通道。
- SDK / CLI / RPC / MCP 当前不可用。
- structured-query API 只是中期设计方案，不得当成已可用接口。
- Dennis 默认先生成 query plan / dry-run SQL。
- 真实执行必须用户逐次授权。
- 不允许写操作。
- DataAgent response 是 step-based JSON；只有 `MODEL_ANSWER` 可进入 evidence。
- `MODEL_THINKING` / raw `TOOL_CALL` 不得原样当证据。
- `no_data` / `pending` / `failed` / `timeout` / `permission_denied` 都进入 `source_quality`，不得当无风险。
- phone / cookie / token / session / header / email / id_card 等敏感字段必须拦截或脱敏。

## Boundaries This Run

- 未访问真实 DataAgent API。
- 未调用 Hive。
- 未提交 SQL。
- 未改 auth / gateway / safeBins / TOOLS。
- 未打包。
- 未提交 git。

## Validation

- `PYTHONPYCACHEPREFIX=/private/tmp/codex_pycache python3 -m py_compile computer_use_poc/dataagent_response_normalizer.py computer_use_poc/dataagent_connector_check.py`: passed.
- YAML parse passed for:
  - `computer_use_poc/dataagent_request_schema_v1.yaml`
  - `computer_use_poc/dataagent_response_schema_v1.yaml`
  - `computer_use_poc/source_executability_inventory_v1.yaml`
  - `computer_use_poc/runtime_required_file_manifest_v1.yaml`
- `python3 computer_use_poc/dataagent_connector_check.py --json`: `PASS_DATAAGENT_CONNECTOR_CONTRACT_CHECK`.
  - mock `completed`: normalized to `completed`.
  - mock `no_data`: normalized to `no_data`.
  - mock `permission_denied`: normalized to `permission_denied`.
  - mock `sql_generated`: normalized to `sql_generated`.
  - mock sensitive fields: blocked/redacted, `sensitive_output=false`.
  - `real_dataagent_api_called=false`, `hive_called=false`, `sql_submitted=false`.
- `python3 computer_use_poc/runtime_snapshot_builder.py --mode full_runtime`: passed, `status=created`, `copied_files_count=97`, `missing_required=[]`.
- `outputs/full_runtime/RUNTIME_MANIFEST.md` contains:
  - `computer_use_poc/dataagent_connector_check.py`
  - `computer_use_poc/dataagent_connector_contract_v1.md`
  - `computer_use_poc/dataagent_prompt_templates_v1.md`
  - `computer_use_poc/dataagent_request_schema_v1.yaml`
  - `computer_use_poc/dataagent_response_normalizer.py`
  - `computer_use_poc/dataagent_response_schema_v1.yaml`
- forbidden path check passed for `outputs/full_runtime`.
- `python3 outputs/full_runtime/computer_use_poc/dataagent_connector_check.py --json`: `PASS_DATAAGENT_CONNECTOR_CONTRACT_CHECK`.
- inventory assertions passed:
  - `current_status=connector_contract_ready`
  - `expected_runtime_mode=authorized_execution_only`
  - `user_confirmation_required=true`
  - `live_api_verification_required=true`
  - `default_mode=dry_run_sql_generation`
- `git diff --check`: passed.
