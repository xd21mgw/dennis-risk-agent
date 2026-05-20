# Capability Registry

本文记录 Dennis Risk Agent 在 `computer_use_poc` 阶段沉淀的能力类型。能力不等于平台手脚；部分能力只属于大脑认知层。

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
- 用户提供了 `userId / deviceId / workId / IP / token_id / 时间窗口 / 平台名 / 日志类型 / 查询对象`，并要求“研判下 / 看下 / 查下”。这种场景默认进入 Plan 模式或 read-only execution。
- 用户已经给出结构化平台 observation，需要做证据归纳或结论生成。
- 用户要写工程文档、改代码、生成 release 包。
- 用户只是问概念解释，例如“token 是什么”“OAuth 是什么”。
- 用户要求执行处置、封禁、解封、批量扩散查询。

### 路由优先级

- 明确 case + 明确实体 / 时间 / 查询对象 / 事实验证诉求：默认进入 Plan 模式或 read-only execution。
- case 文本 + 明确 `userId` 和时间窗口，但用户没有显式说“先不查数”：默认进入 Plan 模式。
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
