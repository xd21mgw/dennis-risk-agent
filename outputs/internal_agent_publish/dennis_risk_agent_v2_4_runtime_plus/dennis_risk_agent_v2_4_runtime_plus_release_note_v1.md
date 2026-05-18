# Dennis Risk Agent v2.4 Runtime Plus Release Note v1

## 1. 当前版本定位

Dennis Risk Agent 是**通用业务风控专家 Agent**，不是 ATO 专用 Agent。

当前版本的定位已经明确分层：

- **ATO** 是第一个深度完全体样板。
- **非 ATO** 通过 Runtime Plus 支持轻量但不表面的短问回答。
- **DataAgent** 只作为 Hive / 公司数仓取数分析能力，不是全能数据底座。

这一版的核心价值不是“把所有场景都做深”，而是：

- ATO 深度闭环先跑通。
- 非 ATO 场景先保持专家认知完整度。
- 默认加载成本可控。
- 查数边界清晰。

## 2. 当前能力边界

### 2.1 ATO 完全体能力

ATO 仍保留完整能力，包括：

- 短问入口。
- 单 case 判断。
- DataAgent 自动同步调用。
- DataAgent 返回解释。
- `provider_conclusion_hint` 与 `dennis_final_judgement` 分离。
- `SQL-only / partial / no_permission / timeout` 降级。
- runtime slim。

### 2.2 非 ATO 8 个 runtime summary 覆盖能力

Runtime Plus 已为以下场景提供轻量但不表面的专家认知：

- 反爬。
- 协议攻击。
- 群控。
- 破解包。
- 真人众包。
- 活动反作弊。
- 导流截流。
- 流量反作弊。

每个场景都覆盖：

- 场景定位。
- 核心判断问题。
- 典型攻击路径。
- 强 / 中 / 弱证据。
- 反证与误判边界。
- 低成本取证方向。
- 治理方法。
- 短问回复话术。
- DataAgent 默认边界。
- 默认输出结构 / 升级条件 / 当前边界。

### 2.3 默认加载规则

默认加载：

- 总控 system prompt / working guide / routing rules。
- Runtime Plus manifest。
- 通用 scenario contract 摘要。
- DataAgent boundary 摘要。
- timeout 策略摘要。
- 当前场景的 runtime summary。

按需读取：

- ATO 深度完全体。
- 非 ATO 深度 Skill。
- parser / schema / join path / interpretation / thresholds。

不默认加载：

- 全量 review。
- 全量 eval。
- walkthrough 全文。
- 历史 case 大集合。

### 2.4 DataAgent 触发边界

- 非 ATO 场景默认不调用 DataAgent。
- 只有用户明确要求查数、拉样本、看日志、看画像、验证数据、生成查询问题时，才进入 DataAgent。
- 高成本查询必须用户确认。
- SQL-only / partial / timeout 不能强结论。

### 2.5 Token 控制策略

- `summary` 默认加载。
- 深度 Skill 按需读取。
- review / eval / history 不默认加载。
- walkthrough 不默认加载。
- ATO 以外的深度材料只在需要时读取。

## 3. 文件清单

### 3.1 Runtime Plus manifest

- `outputs/final/dennis_risk_agent_v2_4_runtime_plus_manifest_v1.md`

### 3.2 启动加载顺序

- `outputs/final/dennis_risk_agent_v2_4_startup_loading_order_checklist_v1.md`

### 3.3 8 个 runtime summary

- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/anti_crawler_runtime_summary_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/protocol_attack_runtime_summary_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/group_control_runtime_summary_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/cracked_app_runtime_summary_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/real_user_crowdsourcing_runtime_summary_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/activity_anti_cheating_runtime_summary_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/traffic_diversion_runtime_summary_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/traffic_anti_cheating_runtime_summary_v1.md`

### 3.4 ATO 完全体保护文件

- `skills/dennis_risk_agent_skills_v2_1_focused_deep/02_domain_skills/account_security_expert_skill.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/07_tools/dataagent/adapter_design/dataagent_markdown_response_parser_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/07_tools/dataagent/configs/query_intent_schema_v2.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/07_tools/dataagent/configs/data_join_paths_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/07_tools/dataagent/adapter_design/dataagent_result_interpretation_rules_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/07_tools/dataagent/adapter_design/dataagent_conclusion_thresholds_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/07_tools/dataagent/real_pilot/dataagent_provider_boundary_overlay_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/07_tools/dataagent/real_pilot/dataagent_timeout_policy_review_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/10_agent_entrypoints/ato_short_question_entrypoint_adaptation_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/07_tools/dataagent/real_pilot/ato_runtime_slimming_plan_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/07_tools/dataagent/real_pilot/ato_runtime_slim_manifest_v1.md`
- `outputs/reviews/dennis_dataagent_poc_auto_sync_loop_result_v1.md`

### 3.5 最终路由回归

- `outputs/final/dennis_risk_agent_v2_4_runtime_plus_final_route_regression_v1.md`

## 4. 集成建议

### 4.1 内部智能体默认启动加载哪些文件

建议默认加载：

1. 总控 system prompt / working guide / routing rules。
2. Runtime Plus manifest。
3. 通用 scenario contract 摘要。
4. DataAgent boundary 摘要。
5. timeout 摘要。
6. 当前场景 runtime summary。

### 4.2 短问怎么走

短问默认先走轻量支持：

- 先识别场景。
- 先拆证据。
- 先给取证方向。
- 先给治理建议。
- 不默认查数。

### 4.3 深问怎么升级

当用户要求完整方案、策略树、汇报、复盘、治理评审，或短问回答不足时，再升级完整 Skill。

### 4.4 查数怎么触发

只有在用户明确要求以下动作时才进入 DataAgent：

- 查数。
- 拉样本。
- 看日志。
- 看画像。
- 验证数据。
- 生成查询问题。

### 4.5 哪些场景不要直接调用 DataAgent

不要默认调用 DataAgent 的场景包括：

- 只问“怎么看 / 是不是 / 怎么防”。
- 只问方法论。
- 只问场景边界。
- 只要治理方向。
- 非 ATO 的轻量研判。

## 5. 后续建设建议

- 暂不扩新架构。
- 下一阶段优先把反爬大 Skill 包升级为第二个完全体。
- 活动反作弊 / 流量反作弊排在下一阶段。
- 导流治理暂作为 P2 场景。

## 6. 对内说明版本价值（300 字以内）

v2.4 Runtime Plus 把 Dennis Risk Agent 从“单场景深度打通”升级成“通用风控专家 + ATO 深度样板 + 其他场景轻量但不表面”的可运行版本。ATO 已完成子 Agent × DataAgent 自动同步闭环，保留完整证据解释和降级能力；非 ATO 场景则以 runtime summary 形式提供反爬、协议、群控、破解包、真人众包、活动反作弊、导流截流、流量反作弊的专家认知，默认不查数，只在明确要求时进入 DataAgent。整体实现了能力完整度、默认成本和路由边界之间的平衡，适合作为下一阶段继续扩展第二个深度场景的基础版本。

