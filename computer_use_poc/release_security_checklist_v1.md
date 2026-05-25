# Release Security Checklist v1

## 1. 打包前必跑

每次生成 release 目录后、打 dist 包和上传前，必须执行：

```bash
python3 computer_use_poc/release_preflight_check.py outputs/release/<release_name>
```

preflight 会自动调用 package scanner：

```bash
python3 computer_use_poc/package_asset_scanner.py outputs/release/<release_name>
```

建议保存 scanner JSON 输出作为内部本地验证记录：

```bash
python3 computer_use_poc/package_asset_scanner.py outputs/release/<release_name> --json
```

不得跳过 `release_preflight_check.py` 直接打包。scanner 是底层检查器，preflight 是打包前门禁入口。

## 1A. Preflight 通过标准

必须同时满足：

- `preflight_pass=true`。
- `package_should_block=false`。
- `critical=0`。
- `high=0`，除非 high 规则在 preflight / rules / checklist 中显式记录豁免原因。
- 无 cookie / token / session / header / API key。
- 无完整 `domain_skills` / full prompt / sensitive run logs。
- 无 auth state / sso-state / browser cookie。
- release 目录包含 README、manifest 和 required runtime files。
- preflight 输出仅为 safe_summary，不打印敏感文件内容、完整 Skill 原文、完整 run_logs 或测试原始样本。

## 1B. Preflight 失败标准

出现任一情况即失败：

- `package_should_block=true`。
- scanner 运行异常、超时、无 JSON 输出或 JSON 解析失败。
- 命中 critical。
- 命中未豁免 high。
- release 目录缺失 manifest / README / required runtime files。
- 输出包含 cookie / token / session / header / API key、完整 Skill 原文、完整 run_logs 或其他敏感内容原文。

## 2. Critical / High 命中处理

如果 scanner 输出 critical / high，或 `package_should_block=true`：

- 不得上传。
- 不得打 dist 包。
- 不得通过改名、压缩、base64、分片或复制到其他目录绕过。
- 必须删除、替换或摘要化命中文件。
- 必须重新运行 scanner，直到 blocking findings 清零后才允许继续。

## 3. 推荐打包流程

1. 从母体仓库生成干净 release 目录：`outputs/release/<release_name>`。
2. 只复制 runtime 必要摘要、schema、guard、manifest、模板。
3. 运行 package scanner。
4. 检查 final manifest，确认每个文件都有 runtime 必要性。
5. scanner 通过后，再打包到 `outputs/dist/`。
6. `outputs/dist/` 默认不提交 git，不嵌套进 release 包。

## 4. 验收标准

release 包必须满足：

- 不包含完整 domain skill 原文。
- 不包含 `02_domain_skills/`。
- 不包含历史 run logs 全量。
- 不包含 runtime question collection 原始日志。
- 不包含 semi-open pilot 原始日志。
- 不包含原始 case / 原始 feedback / 原始 platform observation。
- 不包含完整 prompt / system prompt / agent prompt / tool prompt。
- 不包含 auth / session / token / cookie / header / API key / password / secret / credential。
- 不包含可复原内部平台调用链路的 raw curl、raw headers 或完整源码。
- 只包含 runtime 必要摘要、schema、guard、manifest、模板和最小 regression 摘要。

## 5. 失败时输出口径

```text
release security check 未通过，package_should_block=true。本轮不得上传或打 dist 包。需要先删除 / 摘要化 scanner 命中文件，重新运行 package_asset_scanner.py 通过后再继续。
```

## 6. 本地边界

该 checklist 只约束本地 release 瘦身与打包前门禁：

- 不访问真实内部平台。
- 不调用 DataAgent。
- 不修改 auth / gateway。
- 不重新打包 release，除非另有明确任务。
