# DataAgent Response Envelope Probe v1

## Summary

本轮因 DataAgent local live dry-run 出现 HTTP 200 但 `missing_model_answer`，先推进 cloud Skill parity 复用优先，再补安全的 response envelope shape probe fallback，并增强 normalizer 的 envelope 兼容层。

repo 中已找到云上 DataAgent Skill 成功解析契约与脱敏 fixture：`computer_use_poc/dataagent_cloud_skill_parity_contract_v1.md` 和 `computer_use_poc/test_fixtures/dataagent_cloud_skill_response_mock.json`。目标是优先复用该 step-based JSON / `MODEL_ANSWER` 解析逻辑；如果后续仍无法解释本地 HTTP 200 response，再在授权后执行 shape probe，只看 sanitized shape，不输出 raw response。

## Added / Updated

- 更新 `computer_use_poc/dataagent_local_dryrun_parity_check.py`：
  - 新增 `--probe-response-shape`。
  - probe 只在 `--live-dry-run --allow-live-dry-run` 下可用。
  - probe 不输出 raw response body，只输出 sanitized shape summary。
  - SQL / query_id / trace_id 只输出 present=true/false，不输出原值。
- 更新 `computer_use_poc/dataagent_cloud_skill_parity_contract_v1.md`：
  - 记录 cloud Skill parity fixture 作为本地解析优先来源。
  - 明确 live shape probe 只是 contract 不足时的授权 fallback。
- 更新 `computer_use_poc/dataagent_response_normalizer.py`：
  - 支持 `steps[]` / `subType=MODEL_ANSWER`。
  - 支持 OpenAI-like `choices[].message.content` / `choices[].delta.content`。
  - 支持 `data.steps[]`、`data.messages[]`、`result.steps[]`、`result.answer`、`answer`、`content` fallback。
  - missing model answer 映射为 `source_schema_drift`，而不是 completed。
- 更新 `computer_use_poc/dataagent_response_schema_v1.yaml`：
  - 增加 `response_shape_probe`。
  - 增加 `model_answer_source`。
  - 增加 `parse_error` / `source_schema_drift` 状态边界。
- 更新 `computer_use_poc/dataagent_connector_check.py`：
  - 增加 cloud skill steps、choices message content、data.steps、answer field、missing model answer mock。
- 更新 `computer_use_poc/smoke_tests.md`：
  - 增加 response envelope probe 安全边界检查。

## Boundary

- 未重新访问真实 DataAgent API。
- 未输出原始 DataAgent response。
- 未调用 Hive。
- 未提交 SQL。
- 未读取或输出 cookie/token/session/header。
- 未改 auth / gateway / safeBins / TOOLS。
- 未打包。
- 未提交 git。

## Validation

- `python3 -m py_compile computer_use_poc/dataagent_local_dryrun_parity_check.py computer_use_poc/dataagent_response_normalizer.py computer_use_poc/dataagent_connector_check.py`：通过。
- `python3 computer_use_poc/dataagent_connector_check.py --json`：通过，新增 envelope compatibility mocks 全部通过：
  - `cloud_skill_steps` -> `status=sql_generated`、`model_answer_source=model_answer_step`。
  - `choices_message_content` -> `status=sql_generated`、`model_answer_source=content_fallback`。
  - `choices_delta_content` -> `status=sql_generated`、`model_answer_source=content_fallback`。
  - `data_steps` -> `status=sql_generated`、`model_answer_source=model_answer_step`。
  - `answer_field` -> `status=sql_generated`、`model_answer_source=answer_field`。
  - `missing_model_answer` -> `status=source_schema_drift`、`model_answer_source=missing`。
- `python3 computer_use_poc/dataagent_local_dryrun_parity_check.py --mock --json`：通过。
  - `model_answer_extracted=true`。
  - `normalized_status=sql_generated`。
  - `completed_evidence=false`。
  - `hive_called=false`、`sql_submitted=false`。
- `python3 computer_use_poc/dataagent_local_dryrun_parity_check.py --self-test-status-semantics --json`：通过。
- `python3 computer_use_poc/dataagent_local_dryrun_parity_check.py --probe-response-shape --json`：按预期 blocked，要求 `--live-dry-run --allow-live-dry-run`。
- YAML parse `computer_use_poc/dataagent_response_schema_v1.yaml`：通过。
- `git diff --check`：通过。
