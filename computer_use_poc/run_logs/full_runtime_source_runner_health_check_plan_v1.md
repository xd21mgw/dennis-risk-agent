# Full Runtime Source Runner Health Check Plan v1

## Summary

本轮基于 `computer_use_poc/source_executability_inventory_v1.yaml` 做已有 runner 的本地 health check 规划和最小验证脚本收口。

范围只覆盖已存在并已进入 full_runtime 的 runner：

- `user_login_log`
- `weapon_graphData`
- `weapon_riskData`
- `archives_center_profile`

## Added / Updated

- 新增 `computer_use_poc/source_runner_health_check_plan_v1.md`。
- 新增 `computer_use_poc/source_runner_health_check.py`。
- 更新 `computer_use_poc/smoke_tests.md`，增加：
  - health check plan / script 存在；
  - `runner_present_not_verified` 不得标记为 executable；
  - local health check 不得访问平台，不得泄露 cookie/token/session/header/authorization/password。

## Local Health Check Boundary

- `sso_session_runner` 没有 safe dry-run 参数；因此本轮只设计和执行缺必填参数路径，验证 invocation contract / required args / JSON output schema，不进入 SmartSSOSession 或 cookie fallback。
- `archives_profile_runner` 当前是本地 stub；可以执行 valid stub invocation，输出 `blocked` / `source_gap`，`real_platform_request_executed=false`。
- `runner_present_not_verified` 仍不得升级为 executable 或 completed。

## Source Status

- `user_login_log`: runner present, included in full_runtime, local contract check only.
- `weapon_graphData`: runner present, included in full_runtime, local contract check only.
- `weapon_riskData`: runner present, included in full_runtime, local contract check only.
- `archives_center_profile`: runner present, included in full_runtime, stub check only; not live connected.

## Boundaries This Run

- 未访问真实平台。
- 未调用 DataAgent / Hive。
- 未手拼 cookie/header。
- 未 debug SSO / runner。
- 未修改 auth / gateway / safeBins / TOOLS。
- 未开发新 runner。
- 未打包。
- 未提交 git。

## Validation

- `PYTHONPYCACHEPREFIX=/private/tmp/codex_pycache python3 -m py_compile computer_use_poc/source_runner_health_check.py`: passed.
- `python3 computer_use_poc/source_runner_health_check.py --json`: `PASS_LOCAL_RUNNER_CONTRACT_CHECK`.

Health check observations:

- `user_login_log`: missing required `user_id` path returned `blocked`, `real_platform_request_executed=false`.
- `weapon_graphData`: missing required `user_id` path returned `blocked`, `real_platform_request_executed=false`.
- `weapon_riskData`: missing required `device_id` path returned `blocked`, `real_platform_request_executed=false`.
- `archives_center_profile`: safe local stub returned `blocked`, `real_platform_request_executed=false`, `failure_reason=archives_runner_not_connected`.

All checked outputs had `sensitive_output=false` and no credential-like plaintext was detected by the local validator.
