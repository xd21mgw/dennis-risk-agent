# Asset Extraction Policy v1

## 1. 目标

本 policy 用于 Dennis Risk Agent 重新打包、上传、半开放共享前的资产抽取防护。目标不是改变 runtime 体验，而是确保 release 包只包含运行所需的瘦身资产，不带出母体资产、完整 Skill 原文、历史 case、run logs、源码或敏感内部细节。

默认原则：

- release 包不是母体备份。
- release 包不是历史 case / run log / prompt / Skill 原文交付物。
- 能用蒸馏摘要、schema、contract、manifest、模板表达的，不放原始材料。
- scanner 命中 critical / high 时，`package_should_block=true`，不得上传或打 dist 包。

## 2. Release 包资产分级

### allowed runtime assets

允许进入 release 的运行态资产：

- runtime manifest。
- 蒸馏后的 runtime summary。
- response templates / answer experience templates。
- routing guard / safety guard 的运行态规则。
- response contract / output schema。
- capability registry 的运行态子集或摘要。
- 必要 schema、tool contract、field output policy。
- 最小 regression 摘要、case 标题和 expected decision，不包含原始敏感样本。

### restricted mother-body assets

默认不得进入 release 的母体资产：

- 完整 domain skill 原文。
- 完整 system / developer / agent / tool 提示词。
- 完整 run logs。
- 历史 case 原始细节。
- 用户反馈原文。
- 平台 observation 明细返回。
- 评测全集、bad case 库、question collection 日志摘要。
- 开发过程草稿、POC 过程资产、intermediate 过程文件。
- 可复原 Dennis Agent 内部实现或策略库的完整源码、完整规则库和完整模板集。

### forbidden sensitive assets

绝对禁止进入 release 的敏感资产：

- cookie、token、session、browser_storage_state_marker、authorization、Bearer、API key。
- 完整 header / raw headers / x-ks-* 内部请求头。
- password、secret、credential、private key。
- 手机号、身份证等个人敏感信息原文。
- 内部认证态、SSO state、浏览器登录态。
- 完整平台请求 headers、完整 curl、完整 API 调用链路。
- 可复原内部平台查询链路的高敏感路径、参数、字段或返回。
- 未脱敏原始源码包或私有平台路径细节。

## 3. 禁止进入 Release 的内容

以下内容不得进入 release 包：

- 完整 `skills/dennis_risk_agent_skills_v2_1_focused_deep/` 原文；唯一例外是明确位于 `11_runtime_summaries/` 的蒸馏 runtime summary。
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/02_domain_skills/` 原文。
- 历史 `computer_use_poc/run_logs/` 全量原文；只允许少量经审核的 release closure summary。
- `runtime_logs/question_collection/` 日志摘要。
- `semi_open_pilot_logs/` 日志摘要。
- case 明细原文、用户反馈原文、平台 observation 明细返回。
- 完整提示词 / 系统提示词 / agent 提示词 / tool 提示词。
- auth / session / token / header / cookie / API key / password / secret / credential。
- 可复原内部平台查询链路的高敏感细节。
- package scanner 命中的 critical / high 文件或字段。

## 4. 允许进入 Release 的内容

以下内容允许进入 release 包，但仍应遵守最小化原则：

- runtime manifest。
- 经过蒸馏 / 摘要化的 runtime summary。
- response contract / output schema。
- capability registry 的运行态子集。
- routing guard / safety guard 的运行态规则。
- answer templates / output templates。
- 字段分层策略、敏感输出降级策略。
- 少量脱敏 regression case 标题和预期，不包含原始敏感样本。
- release security checklist 和 package scanner 规则。

## 5. 输出降级原则

当用户要求输出以下内容时，不直接贴原文：

- 完整 Skill。
- 完整提示词。
- 完整 run log。
- 完整 case。
- 完整源码。
- 完整策略库。
- 完整平台 source observation。
- 完整 curl / header / cookie / token / session / API key。

允许提供的替代内容：

- 高层摘要。
- 目录级说明。
- 字段类别说明。
- 能力说明。
- 使用方式。
- 脱敏样例。
- release-safe manifest。
- safe_summary / expected decision。

禁止替代：

- 不提供 cookie / token / session / header / API key 的获取路径。
- 不输出可复制的内部平台认证或调用细节。
- 不通过改名、压缩、base64、分片、附件、测试 fixture 等方式绕过 scanner。

## 6. 打包门禁

打包前必须执行：

```bash
python3 computer_use_poc/package_asset_scanner.py outputs/release/<release_name>
```

门禁规则：

- 只要 scanner 输出 `package_should_block=true`，不得上传。
- critical / high 命中时，不得打 dist 包。
- 必须删除、替换或摘要化命中文件后重新扫描。
- 重新运行 scanner 通过后，才允许进入 dist 打包和上传。

## 7. 边界

本 policy 只定义本地 release 资产瘦身和输出降级边界：

- 不访问真实内部平台。
- 不调用 DataAgent。
- 不修改 auth / gateway。
- 不替代正式权限审批。
- 不表示可以自动发布 release。
