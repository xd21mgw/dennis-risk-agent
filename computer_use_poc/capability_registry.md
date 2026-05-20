# Capability Registry

本文记录 Dennis Risk Agent 在 `computer_use_poc` 阶段沉淀的能力类型。能力不等于平台手脚；部分能力只属于大脑认知层。

## plan_mode

```yaml
capability_name: plan_mode
chinese_name: Plan 模式 / 研判计划能力
layer: main_agent_orchestration
status: new_capability_from_zero
purpose: 在用户显式要求计划、边界不清、批量/关联扩展或高风险动作不适合直接执行时，生成用户可理解、可选择、可确认的只读研判计划
mode_boundary:
  - plan_mode_is_pre_execution_explanation
  - execution_mode_is_real_query_and_judgement
  - real_judgement_queries_should_default_to_execution_when_scope_is_clear
  - plan_is_not_default_for_every_query
input:
  - user_query
  - detected_entities
  - inferred_scene
  - available_capabilities
  - risk_context
output:
  - problem_understanding
  - judgement_goal
  - query_path_with_evidence_cards
  - evidence_strength_explanation
  - readonly_boundary
  - expected_output
  - user_choices
should_trigger_when:
  - user_explicitly_asks_for_plan
  - user_asks_how_to_investigate
  - unclear_entity_or_scope
  - large_batch_or_association_expansion_needed
  - high_risk_action_or_sensitive_boundary
  - method_or_path_design_question
should_not_trigger_when:
  - pure_concept_explanation
  - single_field_lookup
  - user_explicitly_requests_direct_query
  - clear_scope_real_judgement_query
  - normal_readonly_execution_can_answer
default_execution_examples:
  - 帮我看下这个用户是不是风险用户
  - 这个账号是不是盗号
  - 这批账号是不是一伙的
  - 这个用户是不是误伤
  - 这个 request_id 为什么被拦
  - 这个 device_id 有没有问题
boundaries:
  - readonly_only
  - no_disposition
  - no_default_batch_expansion
  - association_is_candidate_not_conclusion
  - no_fabricated_evidence
  - too_many_candidates_stop_expansion
  - missing_entity_requires_clarification_or_generic_plan
  - auth_or_permission_error_must_be_explicit
  - safety_framework_not_yet_integrated
downstream_capabilities:
  - archives_center
  - user_login_logs
  - device_sdk_or_device_profile
  - tianshi_strategy_hit
  - frontend_activity_profile
  - weapon_graph_or_entity_relation_when_needed
  - data_agent_only_when_scene_allows
```

### 定位

`plan_mode` 是执行前解释层，不是真实查询结果。它不调用接口、不生成 observation、不输出最终风险结论。

真实研判问题默认进入执行模式；Plan 只在用户显式要求“先说怎么查 / 先给计划 / 先不要执行”，或边界不清、批量 / 关联扩展、高风险动作不适合直接执行时触发。

Data Agent 不能被泛化成所有数据源底座。只有当场景允许，且确实需要 Hive / 公司数仓取数分析时，才可能进入 Data Agent。

### 输出模板

Plan 标准结构见 `computer_use_poc/plan_mode_capability_v1.md`，固定包含：

1. 我理解的问题。
2. 本次研判目标。
3. 查询路径与强区分证据卡。
4. 证据强弱说明。
5. 查询边界。
6. 预期输出。
7. 你可以选择。

## expert_reasoning_first

```yaml
capability_name: expert_reasoning_first
mode_name: expert_reasoning_first
display_name: 专家认知模式 / 专家认知先判模式
type: brain_capability
platform_call: false
real_data_read: false
write_action: false
downstream_can_connect_to:
  - plan_mode
  - read_only_execution_mode
input:
  - case_text
  - appeal_text
  - customer_service_record
  - manual_note
  - risk_phenomenon_description
output:
  - expert_prior_judgment
  - known_facts
  - core_contradiction_explanation
  - candidate_attack_paths
  - distinguishing_evidence_cards
  - suggested_query_path
  - confidence_and_boundaries
```

### 定位

`expert_reasoning_first` 是 Dennis Risk Agent 的专家认知先判模式，不是新平台手脚，也不是 v2.5 内部平台执行能力。

它复用 v2.1 大脑提示词、账号安全认知、风险路径判断、证据拆解和回复话术，用于“查证前的专家先验分析”。它不是所有 case 的默认入口，也不是所有“研判 / 判断”请求的默认入口。

适用前提：

- 先不查数。
- 先解释现象。
- 先判断可能路径。
- 先设计强区分证据。
- 暂时缺少可直接查数的实体或时间窗口，或用户明确要求“先不查平台”。

在这些前提下，先完成：

1. 看懂问题。
2. 提炼核心矛盾。
3. 给出候选风险路径。
4. 解释表面矛盾为什么可能成立。
5. 设计强区分证据。
6. 输出后续可选查询路径。
7. 标注置信度和边界。

该模式只输出“专家先验判断”和“证据规划”，不是事实结论。

### 触发条件

满足以下任一条件时，进入 `expert_reasoning_first`：

- 用户明确说：
  - 先不查数。
  - 先从专家视角判断。
  - 先解释现象。
  - 先给候选路径。
  - 先设计强区分证据。
  - 先给专家先验判断。
- 用户只提供申诉文本、客服记录、人工备注、模糊现象，且没有明确 `userId / deviceId / workId / IP / token_id / 时间窗口 / 平台名 / 日志对象`。
- 输入中有明显矛盾现象，但当前缺少可直接查询条件：
  - 登录设备只有本人，但账号发生非本人发布。
  - 用户称没操作，但存在交易、发布、登录、关注、点赞等行为。
  - 策略命中较强，但用户申诉材料看似正常。
  - 设备无异常，但行为链路异常。
  - 登录无异常，但内容、交易、互动异常。
- 当前问题核心是解释“为什么会这样”、梳理候选路径、设计强区分证据，而不是事实验证。

### 不触发条件

不要进入 `expert_reasoning_first`：

- 用户明确要求“查一下平台”“调用某个手脚”“看日志结果”。
- 用户提供了 `userId / deviceId / workId / IP / token_id / 时间窗口 / 平台名 / 日志类型 / 查询对象`，并要求“研判下 / 看下 / 查下”。这种场景默认进入 read-only execution；只有用户显式要求计划，或边界不清、批量扩展、高风险动作时才进入 Plan。
- 用户已经给出结构化平台 observation，需要做证据归纳或结论生成。
- 用户要写工程文档、改代码、生成 release 包。
- 用户只是问概念解释，例如“token 是什么”“OAuth 是什么”。
- 用户要求执行处置、封禁、解封、批量扩散查询。

### 路由优先级

- 明确 case + 明确实体 / 时间 / 查询对象 / 事实验证诉求：默认进入 read-only execution；Plan 只用于显式计划请求或边界不清场景。
- case 文本 + 明确 `userId` 和时间窗口，但用户没有显式说“先不查数”：默认进入 read-only execution；只有边界不清、批量扩展、高风险动作或用户显式要求计划时才进入 Plan。
- Plan 模式可以在开头给一句简短专家假设，但不要展开完整 `expert_reasoning_first` 模板。
- 用户明确要求“先从专家视角判断，不查平台”：即使有明确实体，也进入 `expert_reasoning_first`。

### 核心边界

- 不查数。
- 不调内部平台。
- 不访问真实用户数据。
- 不输出“已确认”“确定就是”这类事实结论。
- 可以输出“高度疑似 / 当前最可能 / 需要日志确认 / 证据不足”。
- 必须区分：已知事实、高概率推断、待验证假设、反证可能。
- 不能把关联关系直接等同于风险定性。
- 不能把“设备列表无异常”误解为“账号一定没被盗”。
- 不能把“API 直调”直接等同于“协议破解”。很多场景可能只是复用合法 token 调合法接口。

## expert_reasoning_first answer contract

输出必须包含：

1. 一句话判断。
2. 已知事实。
3. 核心矛盾解释。
4. 候选攻击路径排序。
5. 强区分证据卡。
6. 查询路径建议。
7. 结论置信度与边界。
8. 下一步建议。

强区分证据卡必须能区分至少两个候选路径，不能只写“建议查日志”。
