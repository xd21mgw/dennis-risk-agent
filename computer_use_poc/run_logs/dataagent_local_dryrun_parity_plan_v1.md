# DataAgent Local Dry-Run Parity Plan v1

## Summary

本轮选择 Plan B：DataAgent local live parity dry-run。

目标是准备本地 full_runtime 用云上 Skill 对齐的 Conversational API payload 做 dry-run parity，验证 request builder、payload shape、step-based JSON / `MODEL_ANSWER` normalizer 和 `source_quality` 映射。

本轮只设计和准备，不真实调用 DataAgent API，不调用 Hive，不提交 SQL。

## Added / Updated

- 新增 `computer_use_poc/dataagent_local_dryrun_parity_plan_v1.md`。
- 新增 `computer_use_poc/dataagent_local_dryrun_invocation_template_v1.md`。
- 新增 `computer_use_poc/dataagent_local_dryrun_parity_check.py`。
- 更新 `computer_use_poc/dataagent_connector_contract_v1.md`：
  - 增加 `local_live_parity_dryrun_pending`。
  - 明确 `dry_run=true` 只代表 SQL generation，不代表查数完成。
  - 明确 `sql_generated` 不得进入 completed evidence。
  - 明确 `dry_run=false` 仍需逐次授权。
- 更新 `computer_use_poc/source_executability_inventory_v1.yaml`：
  - `local_dryrun_parity_plan_ready=true`
  - `local_dryrun_live_call_required=true`
- 更新 `computer_use_poc/runtime_required_file_manifest_v1.yaml`，纳入 dry-run parity 文件。
- 更新 `computer_use_poc/smoke_tests.md`，增加 dry-run parity plan、mock、print-payload、allow-live-dry-run 和 dry_run evidence 边界检查。

## Boundary

- `--mock` 只使用本地 mock，不访问 DataAgent。
- `--print-payload` 只打印脱敏 payload，不发请求。
- `--live-dry-run` 没有 `--allow-live-dry-run` 必须 fail closed。
- `--live-dry-run --allow-live-dry-run` 只允许 dry-run Conversational API payload，不提交 Hive SQL，不做认证排障。
- 不读取 `.ks_sso`。
- 不手拼 cookie/header。
- 不输出 cookie/token/session/header。

## This Run Did Not

- 未真实调用 DataAgent API。
- 未调用 Hive。
- 未提交 SQL。
- 未读取 `.ks_sso`。
- 未手拼 cookie/header。
- 未改 auth / gateway / safeBins / TOOLS。
- 未打包。
- 未提交 git。

## Validation

- `python3 -m py_compile computer_use_poc/dataagent_local_dryrun_parity_check.py`：通过。
- YAML parse：
  - `computer_use_poc/source_executability_inventory_v1.yaml`：通过。
  - `computer_use_poc/runtime_required_file_manifest_v1.yaml`：通过。
  - `computer_use_poc/dataagent_request_schema_v1.yaml`：通过。
  - `computer_use_poc/dataagent_response_schema_v1.yaml`：通过。
- `python3 computer_use_poc/dataagent_local_dryrun_parity_check.py --mock --json`：通过，`real_dataagent_api_called=false`，`hive_called=false`，`sql_submitted=false`。
- `python3 computer_use_poc/dataagent_local_dryrun_parity_check.py --print-payload --case single_user_ato --json`：通过，只打印 payload，未发请求。
- `python3 computer_use_poc/dataagent_local_dryrun_parity_check.py --live-dry-run --json`：按预期 fail closed，要求显式 `--allow-live-dry-run`。
- `python3 computer_use_poc/runtime_snapshot_builder.py --mode full_runtime`：通过，`missing_required=[]`。
- `outputs/full_runtime/RUNTIME_MANIFEST.md`：已包含 dry-run parity plan、invocation template 和 parity check 脚本。
- forbidden artifact path check：未发现 `run_logs`、`.ks_sso`、`TOOLS.md`、cookie/header/token/session/raw HAR 等禁入产物路径。
- `git diff --check`：通过。

## Status Semantics Patch

本轮修正 DataAgent local dry-run parity check 的状态字段语义，仅修改本地 normalizer / check 输出和 mock self-test，未访问真实 DataAgent API。

字段语义收敛为：

- `dataagent_api_attempted`：是否尝试调用 DataAgent API 路径。
- `http_request_sent`：是否实际发出 HTTP 请求。已发出请求但 read timeout 时必须为 `true`。
- `step_response_received`：是否收到 DataAgent step-based JSON。
- `model_answer_extracted`：是否提取到 `MODEL_ANSWER`。
- `real_dataagent_api_called`：仅保留为兼容字段，语义对齐 `http_request_sent`，不得再表达 step response 是否成功。
- `hive_called=false`、`sql_submitted=false`：dry-run 语义下保持不变。
- read timeout 映射为 `source_status=timeout`、`failure_reason=read_timeout`。

本轮新增本地 self-test：

- `python3 computer_use_poc/dataagent_local_dryrun_parity_check.py --self-test-status-semantics --json`

验证结果：

- `python3 -m py_compile computer_use_poc/dataagent_local_dryrun_parity_check.py computer_use_poc/dataagent_response_normalizer.py`：通过。
- `python3 computer_use_poc/dataagent_local_dryrun_parity_check.py --mock --json`：通过，mock 输出 `dataagent_api_attempted=false`、`http_request_sent=false`、`step_response_received=true`、`model_answer_extracted=true`、`hive_called=false`、`sql_submitted=false`。
- `python3 computer_use_poc/dataagent_local_dryrun_parity_check.py --self-test-status-semantics --json`：通过，read timeout self-test 输出 `source_status=timeout`、`failure_reason=read_timeout`、`http_request_sent=true`、`step_response_received=false`。
- `git diff --check`：通过。

本轮未真实调用 DataAgent API，未调用 Hive，未提交 SQL，未改 auth / gateway / safeBins / TOOLS，未打包，未提交 git。
