# DataAgent Network Readiness Check v1

## Summary

本轮新增 DataAgent local network readiness check，用于只检查本地到 DataAgent base URL / endpoint 的网络可达性和超时边界。

该检查不是业务查询 runner，不发送 DataAgent 业务 payload，不提交 SQL，不调用 Hive。

## Added / Updated

- 新增 `computer_use_poc/dataagent_network_readiness_check.py`。
- 更新 `computer_use_poc/dataagent_connector_contract_v1.md`，沉淀 network readiness boundary。
- 更新 `computer_use_poc/smoke_tests.md`，增加 network readiness smoke test。

## Behavior

支持命令：

```text
python3 computer_use_poc/dataagent_network_readiness_check.py --json
```

环境变量：

- `DATAAGENT_BASE_URL`：未配置 `DATAAGENT_ENDPOINT_URL` 时必需。
- `DATAAGENT_ENDPOINT_URL`：可选完整 endpoint override。
- `DATAAGENT_ENDPOINT_PATH`：可选 path override，默认 `/v1/chat/completions/full`。
- `DATAAGENT_HTTP_TIMEOUT_SECONDS`：可选超时配置。

输出 `network_status`：

- `env_missing`
- `dns_failed`
- `tcp_failed`
- `tls_failed`
- `http_reachable`
- `auth_required`
- `permission_denied`
- `read_timeout`
- `unknown`

## Boundary

- 不访问业务 DataAgent query。
- 不发送业务 payload。
- 不调用 Hive。
- 不提交 SQL。
- 不读取 `.ks_sso`。
- 不手拼认证 header。
- 不打印 cookie/token/session/header。
- `401` / `403` 只作为 auth / permission boundary，不当 connector 失败。
- 未改 auth / gateway / safeBins / TOOLS。
- 未打包。
- 未提交 git。

## Validation

- `python3 -m py_compile computer_use_poc/dataagent_network_readiness_check.py`：通过。
- `env -u DATAAGENT_BASE_URL -u DATAAGENT_ENDPOINT_URL -u DATAAGENT_ENDPOINT_PATH -u DATAAGENT_HTTP_TIMEOUT_SECONDS python3 computer_use_poc/dataagent_network_readiness_check.py --json`：通过，输出 `network_status=env_missing`，未触发 DNS / TCP / TLS / HTTP。
- `python3 computer_use_poc/dataagent_network_readiness_check.py --json`：通过，本地当前无 DataAgent env，输出 `network_status=env_missing`。
- `git diff --check`：通过。
