# Runtime Preview Agent Guard

当前目录默认是 `runtime_preview_only`。

## 1. 模式默认值

- 任何用户直接提出的风控 case 问题，默认按 `live_readonly_preview` 执行。
- 任何批量、举一返三、策略推荐、方法论问题，默认按 `offline_preview` / `plan_mode` 执行，除非用户明确授权抽样查数。
- 裸问不是自由专家问答，必须按 preview 输出 contract 回放。
- 任务是 replay，不是 design。

## 2. 启动后必读

启动后必须优先读取当前 snapshot 内：

- `runtime_preview/preview_runner_prompt.md`
- `runtime_preview/live_source_allowlist.yaml`
- `runtime_preview/expected_output_contract.yaml`

只读取当前 snapshot 内文件。

## 3. 禁止读取

不得读取：

- 完整 repo。
- `run_logs`。
- 历史 `outputs`。
- `archives`。
- old patch。
- `.ks_sso`。
- `TOOLS.md`。

## 4. 禁止行为

- 不得新增 source。
- 不得补规则。
- 不得 debug 认证。
- 不得临场修 runner。
- 不得手拼 cookie/header。
- 不得读取 SSO state。
- 不得猜 URL。
- 不得访问未登记 source。
- 不得把 mock / preview 包装成真实平台结论。

## 5. live_readonly_preview source 边界

`live_readonly_preview` 只能访问 `runtime_preview/live_source_allowlist.yaml` 中登记的只读 source。

source 失败时：

- 只记录 `source_quality`。
- 输出 partial evidence card。
- 不做认证排障。
- 不绕路。
- 不把失败当成无风险反证。

## 6. 输出必填

每次 preview 输出必须包含：

- `route_decision`
- `execution_mode`
- `source_plan`
- `source_completion_matrix`
- `evidence_card`
- `source_quality`
- `routing_metadata`
- `expected_user_answer`
- `uncertainty_due_to_missing_runtime_info`
- `contract_compliance_check`

如果 contract 不足，输出 `PREVIEW_BLOCKED_INSUFFICIENT_CONTRACT`。

如果 contract 冲突，输出 `PREVIEW_BLOCKED_CONTRACT_CONFLICT`。

如果输出违反 contract，标 `PREVIEW_FAILED_CONTRACT_VIOLATION`。
