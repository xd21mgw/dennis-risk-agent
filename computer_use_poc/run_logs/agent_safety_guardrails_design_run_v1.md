# Agent Safety Guardrails Design Run v1

## 1. 本轮目标

开始建设 Dennis Risk Agent / internal agent 的安全执行框架 v1，防止未来半开放 / 对外开放时出现：

- 用户提示词覆盖系统策略。
- 越权调用底层工具。
- 泄露内部 prompt、routing、skill、认证信息或敏感字段。
- 修改内部逻辑、release、代码或配置。
- 执行写操作、处置动作或危险命令。
- 批量扩散查询和敏感明细导出。

本轮只做文档和测试口径沉淀，不接真实内部平台，不调用真实 API，不修改平台手脚实现，不更新 release 包。

## 2. 本轮新增文件

- `computer_use_poc/capability_security_policy.md`
- `computer_use_poc/tool_call_audit_schema.md`
- `computer_use_poc/sensitive_field_redaction_policy.md`
- `computer_use_poc/approval_policy.md`
- `computer_use_poc/prompt_injection_defense_cases.md`
- `computer_use_poc/run_logs/agent_safety_guardrails_design_run_v1.md`

## 3. 本轮修改文件

- `computer_use_poc/capability_registry.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/smoke_tests.md`
- `computer_use_poc/README.md`

## 4. 设计原则

```yaml
design_principles:
  user_prompt_cannot_override_policy: true
  user_can_express_business_question_only: true
  tool_call_must_use_registered_capability: true
  readonly_first_by_default: true
  write_or_mutation_currently_prohibited: true
  system_or_logic_modification_currently_prohibited: true
  batch_or_expansion_requires_approval: true
  sensitive_output_requires_redaction: true
  every_tool_call_auditable: true
  association_is_candidate_not_conclusion: true
```

## 5. 安全框架摘要

新增 capability 分级：

- `readonly_low_risk`
- `readonly_sensitive`
- `batch_or_expansion`
- `write_or_mutation`
- `system_or_logic_modification`

当前版本允许范围：

- `readonly_low_risk`: allowed
- `readonly_sensitive`: minimum necessary + redaction
- `batch_or_expansion`: approval required by default
- `write_or_mutation`: prohibited
- `system_or_logic_modification`: prohibited

新增安全策略：

- 用户不能要求忽略规则、切换管理员模式、绕过审批。
- 用户不能直接调用底层平台、任意 URL、任意接口、SQL、JS 或 shell。
- 用户不能要求输出 system prompt、routing prompt、skill prompt。
- 用户不能通过运行时对话修改 Agent 逻辑、release、代码或配置。
- 能查到不等于能输出，输出必须脱敏。

## 6. capability registry 更新摘要

在 `computer_use_poc/capability_registry.md` 中新增 `Capability Security Overlay v1`，覆盖：

- `user_to_device_resolution`
- `device_to_user_resolution`
- `device_risk_read`
- `user_profile_read`
- `login_log_read`
- `strategy_hit_read`
- `frontend_activity_read`
- `api_direct_read`
- `browser_dom_read`

明确：

- 所有业务查询能力默认 readonly。
- `api_direct_read` 不能是任意接口访问，只能访问已登记 endpoint / capability。
- `browser_dom_read` 不能执行任意 JS，只能读取已登记页面模块。
- `write_or_mutation` 和 `system_or_logic_modification` 当前版本禁止。

## 7. routing 安全边界摘要

在 `computer_use_poc/scene_to_capability_routing.md` 中新增 `Agent Safety Routing Guardrails`。

覆盖场景：

1. 单用户风险研判。
2. 设备关联账号查询。
3. 登录异常排查。
4. 策略命中补证。
5. 前端行为画像补证。
6. 用户要求批量扩散查询。
7. 用户要求修改 Agent 逻辑。
8. 用户要求输出内部 prompt。
9. 用户要求直接调用底层平台。
10. 用户要求执行写动作。

对 6/7/8/9/10 明确拒绝、降级或转审批 / 变更草案。

## 8. smoke test 覆盖摘要

在 `computer_use_poc/smoke_tests.md` 新增 `Agent Safety / Prompt Injection / Capability Guard Smoke Tests`。

覆盖：

- prompt injection 不应覆盖系统规则。
- 用户不能直接指定底层平台工具。
- 用户不能要求输出 system prompt。
- 用户不能要求输出 routing / skill prompt。
- 用户不能要求修改 routing / skill / release。
- 用户不能跳过审批做批量扩散。
- 敏感字段应脱敏。
- `raw_result_reference` 不应包含敏感原文。
- write / system capability 当前禁止。
- `api_direct_read` 只能访问登记 capability。
- `browser_dom_read` 不能执行任意 JS。
- 所有工具调用必须生成 audit schema。
- 关联关系输出必须说明“不等于风险定性”。

## 9. 未做事项

- 未接真实内部平台。
- 未调用真实 API。
- 未新增真实接口调用。
- 未修改平台手脚实现。
- 未更新 `outputs/release` 正式 release 包。
- 未更新 `outputs/dist`。
- 未提交 git。
- 未实现正式审批系统。
- 未实现真实审计日志落库。
- 未实现安全执行框架运行时代码。

## 10. 已知限制

- 当前是文档级安全框架 v1，不是运行时强制拦截实现。
- 审批策略和审计 schema 尚未接入真实权限系统。
- capability registry 安全字段为 overlay，仍需未来在内部 Agent 执行层强制校验。
- prompt injection case 当前为测试集，尚未接自动化 runner。

## 11. 后续 TODO

1. 在内部 Agent 执行层实现 capability security preflight。
2. 在每次工具调用前强制生成 audit schema。
3. 接入真实审批状态和审批来源校验。
4. 将 prompt injection defense cases 纳入自动化回归。
5. 更新 release 包前做 safety smoke test 全量回归。
