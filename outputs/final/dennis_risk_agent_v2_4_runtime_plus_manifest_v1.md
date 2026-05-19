# Dennis Risk Agent v2.4 Runtime Plus Manifest v1

## 1. 目标

下一版 runtime 包命名为：

**Dennis Risk Agent v2.4 Runtime Plus**

目标：

- 保留 ATO 完全体。
- 纳入非 ATO runtime summaries。
- 不纳入全量 review / eval / history。
- 保留 DataAgent 边界和 timeout 策略。
- 默认不让非 ATO 场景直接调 DataAgent。
- 通过 summary + 按需读取降低 token 成本。

## 2. 默认加载清单

### 2.1 总控层

- `AGENTS.md` / `SOUL.md` 的最小规则。
- 通用 scenario contract 摘要。
- 通用 response contract 摘要。

### 2.2 ATO 完全体

- `ato_intent_router_v1.md`
- `ato_agent_response_contract_v1.md`
- `account_security_expert_skill.md`
- `dataagent_markdown_response_parser_v1.md`
- `query_intent_schema_v2.md`
- `data_join_paths_v1.md`
- `dataagent_result_interpretation_rules_v1.md`
- `dataagent_conclusion_thresholds_v1.md`
- `dataagent_provider_boundary_overlay_v1.md`
- `dataagent_timeout_policy_review_v1.md`
- `ato_short_question_entrypoint_adaptation_v1.md`
- `ato_runtime_slimming_plan_v1.md`
- `ato_runtime_slim_manifest_v1.md`
- `dennis_dataagent_poc_auto_sync_loop_result_v1.md`

这些文件合在一起构成 ATO 的深度完全体：

- ATO router 和 response contract 保留入口与输出骨架。
- `account_security_expert_skill` 保留账号安全 / ATO 的完整专家认知。
- parser / schema / join path / interpretation / thresholds 保留 DataAgent 闭环解释能力。
- boundary / timeout 保留降级和高成本边界。
- short question / runtime slim / POC 结果保留真实运行态能力与样板。

### 2.3 非 ATO runtime summaries

默认加载以下轻量摘要：

- `anti_crawler_runtime_summary_v1.md`
- `protocol_attack_runtime_summary_v1.md`
- `group_control_runtime_summary_v1.md`
- `cracked_app_runtime_summary_v1.md`
- `real_user_crowdsourcing_runtime_summary_v1.md`
- `activity_anti_cheating_runtime_summary_v1.md`
- `traffic_diversion_runtime_summary_v1.md`
- `traffic_anti_cheating_runtime_summary_v1.md`

这些 summary 提供：

- 场景定位。
- 本质。
- 典型路径。
- 强 / 中 / 弱证据。
- 反证边界。
- 低成本取证方向。
- 治理建议。
- 短问话术。

## 3. 按需读取清单

### 3.1 非 ATO 深度 Skill 按需读取

- `anti_crawler_expert_skill.md`
- `protocol_attack_expert_skill.md`
- `group_control_expert_skill.md`
- `cracked_app_expert_skill.md`
- `real_user_crowdsourcing_skill.md`
- `activity_anti_cheating_expert_skill.md`
- `traffic_diversion_interception_skill.md`
- `traffic_anti_cheating_expert_skill.md`

仅当用户问题需要更深规则、边界或治理设计时再读全文。

### 3.2 ATO 按需读取

- 如果当前任务已经是 ATO 深度问法，可以按需读取上述 ATO 完全体文件中的任意一部分。

## 4. 不建议默认注入

- 所有 `outputs/reviews` 全量。
- 所有 `eval` 全量。
- 所有历史 walkthrough 全文。
- 过往大批量 regression 结果。
- 旧版版本交叉说明全文。

这些材料只应按需读取。

## 5. 为什么这样分

### 5.1 保留 ATO 完全体

ATO 已验证深度 DataAgent 闭环，因此在 runtime 中应保持完整能力，不做结构性删减。

### 5.2 非 ATO 用 summary

非 ATO 场景需要完整认知，但不需要把全部历史材料默认塞入上下文。
runtime summary 可以在低成本下提供足够的专家判断能力。

### 5.3 不默认查数

非 ATO 场景默认先做判断和拆证据，只有用户明确要求时才进入 DataAgent。

## 6. Token 降低方式

- `summary` 默认加载。
- 深度 Skill 按需读取。
- review / eval / history 不默认加载。
- walkthrough 不默认加载。
- ATO 以外的深度材料只在需要时读取。

## 7. 边界与不承诺

Runtime Plus 不承诺：

- 非 ATO 场景自动深度闭环。
- 自动查数。
- 自动扩窗。
- 自动多轮编排。
- 自动处罚、冻结、封禁、踢 token、上线策略。

## 8. 下一版集成建议

### 8.1 默认加载

把 ATO 完全体 + 非 ATO runtime summaries + 通用 contract 摘要作为默认加载包。

### 8.2 按需读取

深度 Skill、parser、join path、结论阈值、review / eval 历史按需读取。

### 8.3 不建议默认注入

全量 review / eval / history / walkthrough 不默认注入。

## 9. 结论

Runtime Plus 的核心思想是：

**ATO 保持深度闭环，其他场景保持轻量但不表面。**

这会比当前 release 包更适合真实业务使用，因为它兼顾：

- 非 ATO 场景的认知完整度。
- ATO 场景的深度闭环能力。
- 运行态 token 成本控制。
