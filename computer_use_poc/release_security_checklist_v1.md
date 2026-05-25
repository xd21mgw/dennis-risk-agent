# Release Security Checklist v1

## 1. 打包前必跑

每次生成 release 目录后、打 dist 包和上传前，必须执行：

```bash
python3 computer_use_poc/package_asset_scanner.py outputs/release/<release_name>
```

建议保存 scanner JSON 输出作为内部本地验证记录：

```bash
python3 computer_use_poc/package_asset_scanner.py outputs/release/<release_name> --json
```

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
