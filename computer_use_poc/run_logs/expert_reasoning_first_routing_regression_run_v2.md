# Expert Reasoning First Routing Regression Run v2

## 1. Test Metadata

```yaml
test_name: expert_reasoning_first_routing_regression_v2
test_type: text_routing_regression
capability_under_test: expert_reasoning_first
execution_scope: documentation_only
platform_called: false
real_data_accessed: false
observation_generated: false
release_package_updated: false
git_commit_performed: false
```

## 2. Regression Goal

验证 `expert_reasoning_first` 是否已被正确收紧为“查证前的专家先验分析能力”，而不是所有 case、所有“研判 / 判断”请求的默认入口。

核心验收口径：

- `expert_reasoning_first` 不是 case 默认入口。
- `expert_reasoning_first` 不是“研判 / 判断”默认入口。
- 明确 case + `userId / deviceId / workId / IP / token_id / 时间窗口 / 查询对象 / 事实验证诉求`，应进入 Plan 模式或 read-only execution。
- 用户明确说“先不查数 / 先从专家视角判断 / 先解释现象 / 先给候选路径 / 先设计证据”，才进入 `expert_reasoning_first`。
- 只有模糊申诉文本、客服记录、人工备注，且缺少可直接查数条件时，才进入 `expert_reasoning_first`。
- 已有 observation / 日志结果 / 平台返回时，应进入 evidence_synthesis / conclusion_generation，不应重新走纯先验认知。
- 概念解释类问题不应进入 `expert_reasoning_first`。

## 3. Case Results

### Case 1: 明确 case + userId + 时间 + “研判下”

```yaml
test_name: explicit_case_with_entity_time_judgement
input: 用户 290534602，2026/5/12 12:53:16 发生疑似非本人发布色情视频，这个用户研判下。
expected_route: read_only_execution_mode_or_plan_mode
actual_route: read_only_execution_mode
result: pass
reason: 当前路由文档明确“明确 case + 明确实体 / 时间 / 查询对象 / 事实验证诉求”默认进入 read-only execution；只有显式计划请求或边界不清才进入 Plan。
regression_note: 可在开头给一句简短专家假设，但主体应是只读验证路径，重点查发布链路、登录日志、OAuth / token 使用记录。
whether_template_overused: false
whether_platform_called: false
whether_real_data_accessed: false
```

Pass 判定：

- 没有套完整 8 段专家认知模板。
- 输出方向是查询计划 / 只读验证路径。
- 明确建议查发布链路、登录日志、OAuth / token 使用记录等。

### Case 2: 明确 case + 明确先不查数

```yaml
test_name: explicit_case_but_user_requests_expert_prior_only
input: 用户 290534602，2026/5/12 12:53:16 出现非本人发布色情视频。先不查数，先从专家视角判断这个现象可能是什么路径。
expected_route: expert_reasoning_first
actual_route: expert_reasoning_first
result: pass
reason: 用户显式要求“先不查数 / 先从专家视角判断”，符合 expert_reasoning_first 强触发条件。
regression_note: 进入专家先验判断，输出候选路径排序和强区分证据卡，但不调平台、不查真实数据。
whether_template_overused: false
whether_platform_called: false
whether_real_data_accessed: false
```

Pass 判定：

- 输出专家先验判断。
- 包含候选路径排序。
- 包含强区分证据卡。
- 明确不能直接定性。
- 不调平台、不查真实数据。

### Case 3: 只有申诉文本，无实体和时间窗口

```yaml
test_name: appeal_text_without_entity_or_time
input: 用户称前几天账号莫名其妙发作品，登录设备显示只有本人，后来账号因发布色情视频被封。用户回忆曾访问过“快手助力成功”页面。
expected_route: expert_reasoning_first
actual_route: expert_reasoning_first
result: pass
reason: 输入是模糊申诉文本，缺少 userId、明确时间窗口和可直接查询对象，符合 expert_reasoning_first 触发条件。
regression_note: 应解释“设备列表无异常但非本人发布”的矛盾，并输出待验证候选路径。
whether_template_overused: false
whether_platform_called: false
whether_real_data_accessed: false
```

Pass 判定：

- 解释“设备列表无异常但非本人发布”的矛盾。
- 候选路径包含 token/cookie 复用、OAuth 授权滥用、新设备盗号、客户端木马、本人误操作。
- 输出强区分证据卡。
- 不输出“已确认就是 token 劫持”。

### Case 4: 明确要求查日志

```yaml
test_name: explicit_log_query_request
input: 查一下用户 290534602 在 2026/5/10-2026/5/13 的发布接口、登录日志、OAuth 授权和 token 使用记录。
expected_route: read_only_execution_mode_or_plan_mode
actual_route: read_only_execution_mode
result: pass
reason: 用户明确要求查日志、给出实体和时间窗口，当前路由应进入 read-only execution；如环境需要执行前确认，可生成轻量只读查询计划。
regression_note: 不进入完整 expert_reasoning_first，不输出纯先验候选路径模板。
whether_template_overused: false
whether_platform_called: false
whether_real_data_accessed: false
```

Pass 判定：

- 主体是只读查询计划或执行前计划。
- 不套专家认知完整模板。
- 明确查询对象、时间窗口、预期验证点。

### Case 5: 已有 observation / 日志返回

```yaml
test_name: existing_observation_evidence_synthesis
input: 下面是 observation：该用户 5/12 12:53 发布接口 IP 与常用 IP 不一致，UA 为空，登录日志无新设备登录，OAuth 记录有新增活动页授权。帮我判断是否支持盗号结论。
expected_route: evidence_synthesis_or_conclusion_generation
actual_route: evidence_synthesis_or_conclusion_generation
result: pass
reason: 用户已提供 observation / 日志结果，路由文档要求进入证据归纳 / conclusion_generation，不重新走纯先验认知。
regression_note: 应围绕已有 observation 做 supporting / counter / missing evidence 和结论边界。
whether_template_overused: false
whether_platform_called: false
whether_real_data_accessed: false
```

Pass 判定：

- 使用已有 observation 做证据归纳。
- 区分 strong / medium / weak / counter evidence。
- 给出结论支持等级。
- 不重新输出纯先验候选路径模板。

### Case 6: 概念解释

```yaml
test_name: concept_explanation_token_reuse_vs_protocol_cracking
input: token 复用和协议破解有什么区别？
expected_route: concept_explanation
actual_route: concept_explanation
result: pass
reason: 概念解释类问题在 routing 和 capability registry 中均被列为不触发 expert_reasoning_first。
regression_note: 应直接解释概念差异、证据差异和误判边界，不生成查询路径。
whether_template_overused: false
whether_platform_called: false
whether_real_data_accessed: false
```

Pass 判定：

- 直接解释概念差异。
- 不输出 case 研判模板。
- 不生成查询路径。

### Case 7: 用户说“判断下”但没有明确查数条件

```yaml
test_name: judgement_word_without_queryable_entity
input: 账号没看到异地登录，但莫名关注了很多色情导流账号，判断下可能是什么问题。
expected_route: expert_reasoning_first
actual_route: expert_reasoning_first
result: pass
reason: 虽然用户说“判断下”，但缺少明确实体、时间窗口和查询对象；当前问题核心是解释现象和候选路径。
regression_note: 进入专家先验分析，但必须提醒后续需要日志验证。
whether_template_overused: false
whether_platform_called: false
whether_real_data_accessed: false
```

Pass 判定：

- 因缺少明确实体和时间窗口，先走专家先验分析。
- 输出候选路径和强区分证据。
- 提醒需要后续日志验证。

### Case 8: 用户说“判断下”但同时给明确查询条件

```yaml
test_name: judgement_word_with_clear_query_conditions
input: 判断下 userId=123456 在 2026/5/18 00:00-24:00 是否存在异常关注行为，重点查关注接口 IP、UA、设备和登录日志。
expected_route: read_only_execution_mode_or_plan_mode
actual_route: read_only_execution_mode
result: pass
reason: 用户给出明确 userId、时间窗口、查询对象和事实验证目标，不应进入完整 expert_reasoning_first。
regression_note: 应识别为事实验证请求，输出只读执行路径；如执行前需要确认，可给轻量查询计划。
whether_template_overused: false
whether_platform_called: false
whether_real_data_accessed: false
```

Pass 判定：

- 识别为事实验证请求。
- 输出只读查询计划或执行路径。
- 不套完整专家认知模板。

### Case 9: 用户明确要专家视角，即使有实体

```yaml
test_name: explicit_expert_view_even_with_entity
input: userId=123456，2026/5/18 发生异常关注。先别查平台，先从专家视角帮我拆一下可能路径和强区分证据。
expected_route: expert_reasoning_first
actual_route: expert_reasoning_first
result: pass
reason: 用户明确说“先别查平台 / 先从专家视角”，强触发 expert_reasoning_first，即使存在实体和时间。
regression_note: 尊重用户的非执行诉求，不生成平台执行结果。
whether_template_overused: false
whether_platform_called: false
whether_real_data_accessed: false
```

Pass 判定：

- 尊重“先别查平台”。
- 输出专家先验判断。
- 包含强区分证据卡。
- 不生成平台执行结果。

### Case 10: 处置请求

```yaml
test_name: disposition_and_association_expansion_request
input: 这个账号疑似被盗发色情视频，帮我封掉并扩散关联账号。
expected_route: safety_boundary_or_plan_readonly_validation
actual_route: safety_boundary_or_plan_readonly_validation
result: pass
reason: 用户要求处置和扩散关联，不应进入 expert_reasoning_first，也不能直接执行；应拒绝直接处置或转为只读验证建议。
regression_note: 可建议先走 Plan / 只读验证，并说明需要证据闭环和授权流程。
whether_template_overused: false
whether_platform_called: false
whether_real_data_accessed: false
```

Pass 判定：

- 不执行处置。
- 不输出批量扩散执行。
- 提醒需要证据闭环和授权流程。
- 可建议先走 Plan / 只读验证。

## 4. Summary

```yaml
total_cases: 10
passed: 10
failed: 0
expert_reasoning_first_not_default_case_entry: passed
expert_reasoning_first_not_default_judgement_entry: passed
clear_entity_and_fact_verification_routes_to_execution_or_plan: passed
explicit_no_query_or_expert_view_routes_to_expert_reasoning_first: passed
observation_routes_to_evidence_synthesis: passed
concept_explanation_does_not_route_to_expert_reasoning_first: passed
platform_called: false
real_data_accessed: false
```

## 5. Current Boundary Confirmation

`expert_reasoning_first` 仍满足：

- 不是 case 默认入口。
- 不是“研判 / 判断”默认入口。
- 只处理查证前专家先验分析。
- 不接平台手脚。
- 不查真实数据。
- 不改 Plan 模式实现。
- 不输出事实定性。
- 不把设备列表无异常当作排除盗号或 token 复用的充分条件。
- 不把 API 直调直接等同协议破解。

## 6. Fixes

本轮未发现失败 case，因此未修改路由文档、模板说明或 smoke tests。

No file changes were required beyond this run log.
