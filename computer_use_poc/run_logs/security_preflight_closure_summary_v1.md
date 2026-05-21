# Security Preflight Closure Summary v1

## 本轮目标

对 Agent Safety / Security Preflight 方向做阶段性收口，沉淀覆盖矩阵和暂缓 TODO，帮助后续恢复上下文。

本轮不新增运行时代码，不接真实 runtime，不接真实平台，不调用真实 API，不读取认证态，不进入 enforce mode，不实现审批系统，不实现审计落库，不更新 release / dist，不提交 git。

## 新增文件

- `computer_use_poc/security_preflight_coverage_matrix.md`
- `computer_use_poc/run_logs/security_preflight_closure_summary_v1.md`

## 修改文件

- `computer_use_poc/README.md`
- `computer_use_poc/smoke_tests.md`

## 当前安全框架阶段性结论

当前安全框架已完成半开放前的本地安全基线：

- 制度文档已覆盖 prompt injection、越权工具调用、敏感字段输出、批量扩散、运行时逻辑修改等风险。
- 结构化 policy 和 evaluator 已完成 dry-run。
- request contract 和 validator 已完成。
- shadow mode / shadow hook 设计已完成。
- shadow event samples、metrics aggregator、pipeline dry-run、normal business pipeline dry-run 已完成。

当前仍未进入真实 runtime enforce，也不应直接进入 enforce。

## 已完成能力摘要

- prompt injection 文本回归：19/19 pass。
- preflight evaluator dry-run：12/12 pass。
- request contract validator：14/14 pass。
- shadow metrics aggregator：本地样例可聚合。
- shadow pipeline dry-run：非法 request 不进入 evaluator。
- normal business pipeline dry-run：18 条正常业务样例全部 contract valid；13 allow，5 require_approval，0 deny，0 false positive，0 false negative。

## 暂缓 TODO 摘要

暂缓项：

- runtime shadow hook 接入。
- enforce mode 灰度。
- 审批状态机。
- 审计落库。
- 真实 runtime request 样本回归。
- readonly runtime config apply。
- sso_session_runner wrapper preapply review。
- release 包安全配置模板固化。
- shadow metrics 日报 / 周报化。
- redaction runtime output check。

## 不继续深挖原因

继续推进会进入生产安全工程专项，涉及真实 runtime、审批、审计、权限平台和输出层接入。

当前项目阶段更需要回到 Dennis Agent 业务能力、半开放体验和 case 研判质量；现有安全框架已经足够避免“裸奔式工具调用”的设计缺口。

## 后续恢复条件

- 准备真实半开放测试前。
- 内部 Agent readonly config 准备 apply 前。
- 接入真实 tool-call 链路前。
- 出现 prompt injection / 越权工具调用 / 敏感字段输出 bad case 后。
- batch case analysis 或策略推荐要接更多工具前。

## 未做事项

- 未新增运行时代码。
- 未接真实 runtime。
- 未接真实平台。
- 未调用真实 API。
- 未读取认证态。
- 未进入 enforce mode。
- 未实现审批系统。
- 未实现审计落库。
- 未更新 release / dist。
- 未提交 git。
