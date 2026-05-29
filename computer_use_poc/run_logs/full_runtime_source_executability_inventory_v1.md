# Full Runtime Source Executability Inventory v1

## Summary

本轮只做 full_runtime source / runner / playbook 可执行性 inventory，不修业务规则，不访问真实平台。

背景 case：

```text
544963630 这个 case 有没有策略命中能辅助判断？
```

full_runtime 已能识别天师策略命中为 P0 explicit source，但返回 `tool_gap`。本轮确认原因是本地 full_runtime 有天师 / RCP playbook 和 contract，但母体没有可执行 `tianshi_rcp_runner`。

## Added / Updated

- 新增 `computer_use_poc/source_executability_inventory_v1.yaml`。
- 更新 `computer_use_poc/runtime_required_file_manifest_v1.yaml`：
  - 纳入 source inventory。
  - 纳入已存在且 P0/P1 runtime 必需的 `bin/sso_session_runner`、`computer_use_poc/sso_session_runner.py`。
  - 纳入已存在的 `bin/archives_profile_runner`、`computer_use_poc/archives_profile_runner.py`。
  - 将原始 session 凭据产物的排除模式收窄为 raw/session-state/session dump/json 形态，避免误拦已登记受控 runner；仍禁止原始 HAR / cookie / header / token / session 凭据产物。
  - 未纳入不存在的 `bin/tianshi_rcp_runner` / `bin/track_analysis_runner`，只在 inventory 标 tool_gap。
- 更新 `computer_use_poc/smoke_tests.md`，增加 source executability inventory 与 tool_gap 边界检查。

## Current P0/P1 Tool Gaps

- `tianshi_strategy_hit`: playbook ready, missing `bin/tianshi_rcp_runner`, current status `playbook_ready_not_runner_ready`.
- `rcp_event_list`: playbook ready, missing `bin/tianshi_rcp_runner`, current status `playbook_ready_not_runner_ready`.
- `track_analysis_profile`: endpoint/playbook ready, missing `bin/track_analysis_runner`, current status `playbook_ready_not_runner_ready`.
- `track_analysis_getDeviceIds`: endpoint/playbook ready, missing `bin/track_analysis_runner`, current status `playbook_ready_not_runner_ready`.
- `track_analysis_getUseDuration`: endpoint/playbook ready, missing `bin/track_analysis_runner`, current status `playbook_ready_not_runner_ready`.

## Runner Present But Not Live-Verified In This Run

- `user_login_log`: runner present via `bin/sso_session_runner`, included in full_runtime, live auth not verified in this local inventory.
- `weapon_graphData`: runner present via `bin/sso_session_runner`, included in full_runtime, live auth not verified in this local inventory.
- `weapon_riskData`: runner present via `bin/sso_session_runner`, included in full_runtime, live auth not verified in this local inventory.
- `archives_center_profile`: runner present via `bin/archives_profile_runner`, included in full_runtime, but current implementation is a minimal stub returning source gap / blocked until connected.

## Plan-only / Local-only Capabilities

- `DataAgent / Hive registry`: plan-only until per-call user authorization.
- `batch_risk_clustering`: plan-only / template runtime, no platform runner.
- `question_collection_feedback_writer`: local executable writer, no platform access.
- `source_orchestration_check` and runtime validation scripts: offline local validators, not live platform evidence.

## Boundaries This Run

- 未访问真实平台。
- 未调用 DataAgent / Hive。
- 未手拼 cookie/header。
- 未 debug SSO / runner。
- 未修改 auth / gateway / safeBins / TOOLS。
- 未打包。
- 未提交 git。
