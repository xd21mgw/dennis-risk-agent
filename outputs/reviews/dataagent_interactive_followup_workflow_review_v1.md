# Data Agent Interactive Follow-up Workflow Review v1

## 0. 本轮目标

本轮补充通用 `dataagent_interactive_followup` workflow，用于处理 Data Agent 分批返回、SQL-only 等待执行、partial 后选择下一步、扩窗建议、缺输入补充和多方向取证选择。

边界：
- 不调用 Data Agent。
- 不修改核心 Skill。
- 不编造真实数据。
- 不写真实表名、字段名、SQL 或 API。
- Data Agent 仍是 evidence provider。
- Dennis 主 Agent / Router 负责 next action、优先级、成本解释和 `dennis_final_judgement`。

## 1. 新增 / 修改文件

### 修改文件

- `skills/dennis_risk_agent_skills_v2_1_focused_deep/09_scenario_workflows/scenario_workflow_contract_v1.md`
  - 新增 `dataagent_interactive_followup` workflow。
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/10_agent_entrypoints/scenario_response_contract_v1.md`
  - 新增 `dataagent_interactive_followup_response` 输出协议。
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/07_tools/dataagent/real_pilot/dataagent_provider_boundary_overlay_v1.md`
  - 补充 Data Agent `next_data_options` 边界和显式确认规则。
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/07_tools/dataagent/adapter_design/dataagent_markdown_response_parser_v1.md`
  - 补充交互式 follow-up parser 字段和状态识别规则。

### 新增文件

- `outputs/reviews/dataagent_interactive_followup_workflow_review_v1.md`

## 2. dataagent_interactive_followup 如何工作

标准链路：

```text
Data Agent 分批 / SQL-only / partial / 缺输入 / 多方向返回
→ parser 抽取 next_data_options / required_missing_inputs / batch_status
→ Dennis Agent 解释当前证据上限和缺口
→ Dennis Agent 给出下一步选项、优先级和查询成本
→ 用户确认高成本或敏感查询
→ Dennis Agent 生成可复制给 Data Agent 的下一步问题
```

关键原则：
- Data Agent 可以提出候选下一步，但不决定最终下一步。
- Dennis Agent 负责把候选项翻译成用户可选择动作。
- SQL-only / running / partial 不能进入强结论。
- 高成本 Hive、长周期扩窗、跨域 join、大样本回捞必须显式确认。
- 若缺最小输入，不能生成可执行 Data Agent question，只能要求用户补充。

## 3. 回归 Case

### Case 1：Data Agent 只返回 SQL，询问是否执行

| 字段 | 内容 |
|---|---|
| Data Agent 返回摘要 | 已完成表检索和 SQL 生成，未执行查询；询问是否授权执行。 |
| parser 应识别字段 | `status=sql_only`；`batch_status=sql_only/waiting_user_choice`；`needs_user_confirmation=true`；`next_data_options=[执行 SQL, 人工下载执行]`；`estimated_query_cost=medium`。 |
| Dennis Agent 应展示给用户的选项 | 选项 A：授权 Data Agent 执行已生成 SQL；选项 B：人工下载 SQL 审核后执行；选项 C：先缩小时间窗再生成更低成本 SQL。 |
| 推荐优先级 | P0：执行或人工执行 SQL；P1：缩小时间窗优化 SQL；P2：暂存为 evidence plan。 |
| 是否需要用户确认 | 需要。SQL 执行会产生 Hive 成本。 |
| 可复制给 Data Agent 的下一步问题 | “请在只读边界内执行上一轮已生成的查询计划，并返回聚合摘要、返回行数、权限裁剪、缺失证据和口径风险。不要输出最终风控定性。” |
| 是否可以先输出阶段性 Dennis 判断 | 可以，但只能是“当前为 SQL-only / pending_execution，证据不足，不能支持风险结论”。 |
| 是否符合 Data Agent evidence provider 边界 | 符合。SQL 是取证计划，不是证据。 |

### Case 2：第一批登录链路结果，建议继续查下游行为

| 字段 | 内容 |
|---|---|
| Data Agent 返回摘要 | 第一批返回登录 / 授权链路聚合，显示疑似 Web 扫码登录线索；建议继续查发布、私信、关注或接口访问。 |
| parser 应识别字段 | `batch_status=first_batch`；`status=partial` 或 `success_with_missing_evidence`；`next_data_options=[发布行为, 私信/关注/评论, 接口访问]`；`needs_user_confirmation=true`。 |
| Dennis Agent 应展示给用户的选项 | 选项 A：低成本查发布行为；选项 B：中成本查互动行为；选项 C：中高成本查接口访问 / 资产访问；选项 D：先输出阶段性判断。 |
| 推荐优先级 | P0：补账号接管链路缺口；P1：按业务最关心的下游作恶分支查；P2：多分支并行仅在用户确认后执行。 |
| 是否需要用户确认 | 需要，尤其多分支或跨域 join。 |
| 可复制给 Data Agent 的下一步问题 | “请基于同一批样本和同一时间窗，只读查询登录/授权后是否存在发布、私信/关注/评论或接口访问等下游行为，按分支输出聚合摘要、覆盖范围、缺失证据和口径风险。” |
| 是否可以先输出阶段性 Dennis 判断 | 可以。最多输出“存在账号接管数据线索，但下游作恶链路未闭合”。 |
| 是否符合 Data Agent evidence provider 边界 | 符合。Data Agent 只提供第一批发现和候选下一步。 |

### Case 3：partial，前端行为无权限，建议补权限或改查后端链路

| 字段 | 内容 |
|---|---|
| Data Agent 返回摘要 | 后端 / 账号安全域可查，前端行为域无权限；建议申请权限或改查后端 service / 离线行为聚合。 |
| parser 应识别字段 | `status=partial`；`permission_notes=[前端行为域无权限]`；`missing_evidence=[前端行为证据]`；`next_data_options=[权限申请后重查, 改查后端链路]`。 |
| Dennis Agent 应展示给用户的选项 | 选项 A：申请前端行为权限后重查；选项 B：先查后端 service / 离线聚合替代路径；选项 C：阶段性输出“证据不足”。 |
| 推荐优先级 | P0：如果结论依赖前端行为，先申请权限；P1：若业务急需，可先查后端替代链路但标记 limitation。 |
| 是否需要用户确认 | 需要。权限申请和替代查询都需要确认。 |
| 可复制给 Data Agent 的下一步问题 | “当前前端行为域无权限。请在现有权限内改查后端链路和账号安全事件的离线聚合，说明该替代路径能覆盖什么、不能覆盖什么、口径风险是什么。” |
| 是否可以先输出阶段性 Dennis 判断 | 可以，但必须降级：关键前端证据缺失，不能强结论。 |
| 是否符合 Data Agent evidence provider 边界 | 符合。无权限不被解释为无风险。 |

### Case 4：建议扩大时间窗到 7-10 天

| 字段 | 内容 |
|---|---|
| Data Agent 返回摘要 | 单日窗口结果不足，建议扩展到 7-10 天以观察延迟下游作恶或登录态后续行为。 |
| parser 应识别字段 | `suggested_query_expansion.time_window=7-10天`；`estimated_query_cost=high`；`needs_user_confirmation=true`；`batch_status=waiting_user_choice`。 |
| Dennis Agent 应展示给用户的选项 | 选项 A：先扩到前后 1 天；选项 B：扩到 7-10 天；选项 C：先按低成本分支查重点行为；选项 D：不扩窗，只输出当前结论上限。 |
| 推荐优先级 | P0：先做低成本分支或前后 1 天；P1：若仍解释不了，再 7-10 天扩窗；P2：大样本扩窗需单独确认。 |
| 是否需要用户确认 | 必须确认。长周期 Hive 查询成本高。 |
| 可复制给 Data Agent 的下一步问题 | “请先不要直接扩到长周期。请优先在前后 1 天内补查关键下游行为；如果仍不足，再列出扩到 7-10 天的预计覆盖和成本。” |
| 是否可以先输出阶段性 Dennis 判断 | 可以。输出“当前窗口证据不足，不能因短窗口无结果反向排除”。 |
| 是否符合 Data Agent evidence provider 边界 | 符合。扩窗是可选取证动作，不是默认执行。 |

### Case 5：需要用户补充 device_id / session_id

| 字段 | 内容 |
|---|---|
| Data Agent 返回摘要 | 缺少可定位实体，只有笼统描述；要求补充 user_id / device_id / session_id / trace_id / 时间窗。 |
| parser 应识别字段 | `required_missing_inputs=[entity_identifier, time_window]`；`batch_status=waiting_user_choice`；`needs_user_confirmation=false`，但需要用户补输入。 |
| Dennis Agent 应展示给用户的选项 | 选项 A：补 user_id + 时间窗；选项 B：补 device_id / session_id / trace_id；选项 C：如果只有批量样本，先给样本范围和时间窗。 |
| 推荐优先级 | P0：补实体标识和时间窗；P1：补业务动作和异常描述；P2：补人工备注作为线索。 |
| 是否需要用户确认 | 不需要确认查询，但需要用户补最小输入。 |
| 可复制给 Data Agent 的下一步问题 | 暂不生成可执行问题。待用户补充实体标识和时间窗后再生成。 |
| 是否可以先输出阶段性 Dennis 判断 | 只能输出“无法取证 / missing input”，不能输出风险判断。 |
| 是否符合 Data Agent evidence provider 边界 | 符合。缺输入不等于查询失败，也不等于无风险。 |

### Case 6：多个下一步方向：登录、发布、私信、爬虫、活动

| 字段 | 内容 |
|---|---|
| Data Agent 返回摘要 | 已完成基础登录聚合，给出多个方向：继续查登录详情、发布行为、私信互动、接口访问、活动参与。 |
| parser 应识别字段 | `next_data_options=[登录详情, 发布, 私信互动, 接口访问, 活动参与]`；`estimated_query_cost` 分项；`batch_status=intermediate/waiting_user_choice`。 |
| Dennis Agent 应展示给用户的选项 | 登录详情：低成本，验证账号接管；发布：低/中成本，验证内容下游；私信互动：中成本，验证导流/骚扰；接口访问：中/高成本，验证反爬/资产访问；活动参与：中成本，验证活动套利。 |
| 推荐优先级 | P0：登录详情，先闭合 ATO 发生方式；P1：按业务损伤优先查一个下游分支；P2：多分支并行需确认成本。 |
| 是否需要用户确认 | 需要，尤其跨域多分支。 |
| 可复制给 Data Agent 的下一步问题 | “请优先补充登录详情，验证是否存在 Web 扫码 / 授权登录 / 新设备 / 非历史环境 / token 或 session 异常。下游分支暂不全部展开，只返回后续可选方向和成本说明。” |
| 是否可以先输出阶段性 Dennis 判断 | 可以。输出“基础登录聚合已完成，但 ATO 发生方式和下游作恶尚未完全闭合”。 |
| 是否符合 Data Agent evidence provider 边界 | 符合。Dennis Agent 做优先级排序，Data Agent 不决定最终路径。 |

## 4. 用户如何选择下一步 Data Agent 动作

Dennis Agent 应把 Data Agent 的下一步建议转成三类用户选择：

1. 低成本补证：
   - 单日 / 小样本 / 单域聚合。
   - 适合默认推荐，但仍需告知用户。
2. 中成本补证：
   - 多域 join、少量分支查询。
   - 需要用户确认优先查哪个分支。
3. 高成本补证：
   - 长周期扩窗、跨域 join、大样本回捞、高敏权限。
   - 必须显式确认。

如果用户只想要阶段性判断，Dennis Agent 可以输出当前结论上限，但必须标注 missing evidence 和 provider limitations。

## 5. 哪些动作必须显式确认

必须确认：
- 执行 SQL 或授权 Data Agent 执行 SQL。
- 长周期扩窗，例如 7-10 天。
- 跨域 join，例如登录、发布、私信、接口、活动、关系网络联合查询。
- 大样本回捞。
- 高成本 Hive 查询。
- 涉及权限申请或高敏字段的查询。

不需要确认但需要补输入：
- 缺 user_id / device_id / session_id / trace_id / risk_event_id / request_id。
- 缺明确 time_window。
- 缺业务场景或目标动作。

## 6. ATO Overlay 说明

本轮没有修改 ATO workflow 文件。

原因：
- `dataagent_interactive_followup` 是通用 workflow，ATO 场景可以直接继承。
- ATO 场景遇到 Data Agent 分批返回、SQL-only、partial、缺输入或多个后续方向时，应进入 `dataagent_interactive_followup`，而不是直接下结论。
- 若后续 ATO 真实使用中该模式高频出现，再在 ATO overlay 中补一条显式路由示例即可。

## 7. 是否修改核心 Skill

未修改核心 Skill。

