# DataAgent Local Env Setup Helper v1

## Summary

本轮新增 DataAgent 本地非敏感 env 配置助手，用于降低手动配置 `~/.dennis-agent/dataagent.env` 的复杂度。

该助手只写入 base URL、endpoint path、请求身份标识和超时参数，不保存 cookie、token、session、header、password 或 SSO state。

## Added / Updated

- 新增 `computer_use_poc/setup_dataagent_local_env.py`。
- 新增 `computer_use_poc/dataagent_local_env_setup_guide_v1.md`。
- 更新 `computer_use_poc/dataagent_network_readiness_check.py`：env 未加载但本地 env 文件存在时，只提示 `source ~/.dennis-agent/dataagent.env`。
- 更新 `computer_use_poc/runtime_required_file_manifest_v1.yaml`：纳入 setup helper 和 guide；排除 `dataagent.env`。
- 更新 `computer_use_poc/smoke_tests.md`：增加本地 env helper 检查。

## Boundary

- 未访问 DataAgent API。
- 未调用 Hive。
- 未提交 SQL。
- 未读取 cookie/token/session/header。
- 未读取 `.ks_sso`。
- 未保存任何敏感认证信息。
- 未改 auth / gateway / safeBins / TOOLS。
- 未打包。
- 未提交 git。

## Validation

- `python3 -m py_compile computer_use_poc/setup_dataagent_local_env.py computer_use_poc/dataagent_network_readiness_check.py`：通过。
- `python3 computer_use_poc/setup_dataagent_local_env.py --check`：通过，本地当前未创建 env，输出 `FAIL_CLOSED` 与 `<missing>`，未打印配置值或敏感内容。
- `python3 computer_use_poc/setup_dataagent_local_env.py --print-source-command`：通过，输出 `source ~/.dennis-agent/dataagent.env`。
- `env -u DATAAGENT_BASE_URL -u DATAAGENT_ENDPOINT_URL -u DATAAGENT_ENDPOINT_PATH -u DATAAGENT_HTTP_TIMEOUT_SECONDS python3 computer_use_poc/dataagent_network_readiness_check.py --json`：通过，输出 `network_status=env_missing`。
- `python3 computer_use_poc/runtime_snapshot_builder.py --mode full_runtime`：通过，`missing_required=[]`，`copied_files_count=104`。
- `outputs/full_runtime/RUNTIME_MANIFEST.md`：已包含 `computer_use_poc/setup_dataagent_local_env.py` 和 `computer_use_poc/dataagent_local_env_setup_guide_v1.md`。
- forbidden path check：`outputs/full_runtime` 未发现 `dataagent.env`、cookie/header/token/password/raw session artifact 路径。
- `git diff --check`：通过。
