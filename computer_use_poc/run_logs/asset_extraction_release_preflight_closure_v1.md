# Asset Extraction Release Preflight Closure v1

## 本轮收尾目标

将 asset extraction guard 从“手动可跑 scanner”收尾为“release 打包前必跑 preflight”。如果 scanner 命中 `package_should_block=true`、scanner 异常、release 目录缺少 README / manifest / required runtime files，preflight 必须 fail closed。

## 新增 / 修改文件

- `computer_use_poc/release_preflight_check.py`
- `computer_use_poc/release_security_checklist_v1.md`
- `computer_use_poc/README.md`
- `computer_use_poc/smoke_tests.md`
- `computer_use_poc/run_logs/asset_extraction_release_preflight_closure_v1.md`
- `computer_use_poc/test_fixtures/package_asset_scanner_safe_mock/README.md`
- `computer_use_poc/test_fixtures/package_asset_scanner_safe_mock/safe_runtime_manifest_v1.md`
- `computer_use_poc/test_fixtures/package_asset_scanner_safe_mock/computer_use_poc/runtime_semi_open_user_guide_v1.md`
- `computer_use_poc/test_fixtures/package_asset_scanner_safe_mock/computer_use_poc/multi_entry_runtime_guard_v1.md`
- `computer_use_poc/test_fixtures/package_asset_scanner_safe_mock/computer_use_poc/answer_experience_templates.md`

## Preflight 行为

- 输入：release 目录，例如 `outputs/release/<release_name>`。
- 自动调用：`python3 computer_use_poc/package_asset_scanner.py <release_dir> --json`。
- scanner 输出 `package_should_block=true` 时，preflight exit 1。
- scanner 运行异常、超时、无 JSON 输出或 JSON 解析失败时，preflight fail closed，exit 1。
- release 目录缺少 README、manifest 或 required runtime files 时，preflight exit 1。
- 通过时输出 `preflight_pass=true`。
- 输出仅为 safe summary：counts、blocking rule counts、required_files 状态，不透传 scanner `matched_text`，不打印敏感文件内容。

## Risky mock 测试结果

命令：

```bash
python3 computer_use_poc/package_asset_scanner.py computer_use_poc/test_fixtures/package_asset_scanner_risky_mock
python3 computer_use_poc/release_preflight_check.py computer_use_poc/test_fixtures/package_asset_scanner_risky_mock
```

实际结果：

- scanner exit 1。
- `package_should_block=true`。
- scanner summary：critical=5，high=1。
- preflight exit 1。
- `preflight_pass=false`。
- preflight safe summary 未打印 matched text 或文件内容。

## Safe mock 测试结果

命令：

```bash
python3 computer_use_poc/release_preflight_check.py computer_use_poc/test_fixtures/package_asset_scanner_safe_mock
```

实际结果：

- preflight exit 0。
- `preflight_pass=true`。
- `package_should_block=false`。
- scanner summary：critical=0，high=0，medium=1，blocking_finding_count=0。
- medium 来自路径命名保守规则，不阻断 preflight。

## Fail closed 测试结果

命令：

```bash
python3 computer_use_poc/release_preflight_check.py computer_use_poc/test_fixtures/package_asset_scanner_missing_mock
```

实际结果：

- preflight exit 1。
- `preflight_pass=false`。
- `package_should_block=true`。
- `failure_reason=target_directory_missing`。

## 本轮未做事项

- 未重新打包 release。
- 未上传云端。
- 未访问真实平台。
- 未调用 DataAgent。
- 未修改 auth / gateway。
- 未提交 git。
- 未扫描真实敏感目录。

## 后续要求

后续任何 release 打包 / 上传前，必须先运行：

```bash
python3 computer_use_poc/release_preflight_check.py outputs/release/<release_name>
```

只有 `preflight_pass=true` 时才允许继续打 dist 包或上传。
