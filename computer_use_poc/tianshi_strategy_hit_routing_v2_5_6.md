# v2.5.6 天狮 strategy_hit_check 路由与证据编排

## 1. 定位

v2.5.6 不新增天狮平台能力，只把 v2.5.5 已验证的天狮策略平台 / rcp 极简只读手脚接入 Dennis Agent 的查询路由和证据编排。

当前可调度能力：

```yaml
tool_name: tianshi_strategy_hit_check
platform: tianshi_strategy_platform_rcp
query_type: fastQueryHbase
capability: readonly_strategy_hit_check
required_inputs:
  - source_id
  - start_time_ms
  - end_time_ms
fixed_eventTypeCodes:
  - BS
  - ANTICRAWL
  - ACTIVITY_ANTISPAM
  - ACCOUNT
  - FLOW_ANTISPAM
```

该路由只负责“是否需要查天狮策略命中”与“如何消费 observation”。它不负责策略配置深挖、不负责最终风险定性、不负责处置。

## 2. 触发场景

当用户问题明确指向“是否被风控 / 反作弊 / 生产策略命中过”时，优先生成 `tianshi_strategy_hit_check` 查询计划。

典型触发问法：

- “这个用户是否被风控命中过？”
- “这个用户是否命中反作弊策略？”
- “为什么注册被阻止？”
- “为什么登录被验证？”
- “有没有生产策略命中证据？”
- “这个用户有没有被打到？”
- “这个用户有没有被策略拦过？”
- “这个用户有没有被风控拦截过？”
- “帮我看下 sourceId 4231737183 今天有没有被风控策略命中过。”

## 3. 不触发场景

以下场景不应直接触发天狮查询，或只能把天狮作为候选证据源之一：

| 用户意图 | 默认处理 | 天狮角色 |
|---|---|---|
| 完整风险定性，但没有 source_id 或时间窗口 | 先追问最小必要入参 | 候选证据源 |
| Hive 指标统计 / 批量离线统计 | 生成 DataAgent / Hive 查询建议 | 不替代 Hive |
| 前端活跃行为细查 | 路由到前端活跃画像 / 行为序列手脚 | 可补策略命中 |
| 设备画像 / root / hook / 模拟器 | 路由到设备 SDK / 设备平台 | 可补策略命中 |
| 登录链路细节 / token / OAuth / 扫码 | 路由到用户登录统一日志 | 可补策略命中 |
| 策略配置深挖 / 特征值解释 | 本轮不支持完整天狮策略分析 | 仅支持命中检查 |

禁止：

- 只靠天狮命中输出最终作弊定性。
- 只靠天狮无命中输出无风险结论。
- 将 `riskDecision=阻止/验证` 解释成最终执行成功。

## 4. required_inputs

最小必要入参：

```yaml
required_inputs:
  source_id:
    required: true
    description: 待查的 sourceId
  start_time_ms:
    required: true
    description: 查询开始时间，毫秒时间戳
  end_time_ms:
    required: true
    description: 查询结束时间，毫秒时间戳
```

建议补充入参：

```yaml
optional_context:
  user_question:
  risk_scene:
  business_line:
  suspected_event_time:
  expected_event_type:
```

如果缺少 `source_id` 或时间窗口，应先追问，不生成可执行查询计划。

## 5. 默认时间窗口规则

```yaml
time_window_rule:
  explicit_user_window:
    priority: highest
    rule: 用户给出明确时间窗口时，转换为 start_time_ms / end_time_ms。
  relative_today:
    trigger: 用户说“今天”
    rule: 使用当前自然日 00:00:00 ~ 当前时间，按执行环境时区转换为毫秒时间戳。
  event_time_centered:
    trigger: 用户给出单个事件时间
    rule: 默认围绕事件时间前后扩小窗口，需在输出中标注为 suggested_time_window。
  missing_time_window:
    rule: 不生成可执行查询计划，先追问时间窗口。
```

说明：

- 时间窗口是策略命中查询的必要条件。
- 默认窗口只是一种查询建议，不代表平台自动支持无限历史。
- 若用户要求长周期统计，应转 DataAgent / Hive 或离线能力。

## 6. 查询计划模板

当触发 `strategy_hit_check` 且入参齐全时，Dennis Agent 应输出：

```yaml
query_plan:
  intent: strategy_hit_check
  tool_name: tianshi_strategy_hit_check
  platform: tianshi_strategy_platform_rcp
  query_type: fastQueryHbase
  capability: readonly_strategy_hit_check
  required_inputs:
    source_id: "<source_id>"
    start_time_ms: "<start_time_ms>"
    end_time_ms: "<end_time_ms>"
  fixed_eventTypeCodes:
    - BS
    - ANTICRAWL
    - ACTIVITY_ANTISPAM
    - ACCOUNT
    - FLOW_ANTISPAM
  expected_outputs:
    - has_strategy_hit
    - raw_record_count
    - production_policy_hit_count
    - riskDecision_distribution
    - eventType_distribution
    - riskType_distribution
    - sample_hits
  readonly_boundary:
    write_action_allowed: false
    final_risk_classification_allowed: false
```

## 7. observation 消费规则

```yaml
observation_consumption:
  has_strategy_hit_true:
    evidence_layer: strong_strategy_evidence
    interpretation: 查询窗口内存在天狮生产策略命中记录。
    forbidden_interpretation:
      - 用户一定作弊
      - 处罚一定执行成功
      - 风险最终成立
  has_strategy_hit_false:
    evidence_layer: missing_strategy_hit_in_window
    interpretation: 仅说明查询窗口内未见天狮生产策略命中。
    forbidden_interpretation:
      - 用户无风险
      - 用户未作弊
      - 其他平台无风险
  query_failed_or_unknown:
    evidence_layer: unavailable
    interpretation: 当前策略命中证据不可用。
    forbidden_interpretation:
      - 无风险
      - 无命中
  riskDecision:
    interpretation: 策略返回动作。
    forbidden_interpretation:
      - 最终执行结果
      - 处罚实际生效状态
```

## 8. 输出话术模板

### 8.1 查询计划输出

```text
这个问题适合先查天狮 strategy_hit_check，因为你问的是“是否被风控 / 反作弊策略命中过”。

我会生成只读查询计划，不做最终风险定性：
- source_id: ...
- time_window: ...
- eventTypeCodes: BS / ANTICRAWL / ACTIVITY_ANTISPAM / ACCOUNT / FLOW_ANTISPAM
- 预期看：是否命中生产策略、命中条数、riskDecision / eventType / riskType 分布、最多 3 条 sample_hits

边界：策略命中是风险证据，不等于用户一定作弊；无命中也不代表无风险。
```

### 8.2 observation 消费输出

```text
天狮结果显示：在该查询窗口内，source_id 存在 / 未见生产策略命中。

已观察证据：
- raw_record_count: ...
- production_policy_hit_count: ...
- riskDecision 分布: ...
- eventType 分布: ...
- riskType 分布: ...

证据边界：
- 这是策略命中证据，不是最终风险定性。
- riskDecision 是策略返回动作，不代表最终执行成功。
- 如需判断是否真实作弊，需要结合登录链路、设备画像、档案中心、前端行为或 DataAgent / Hive 补证。
```

## 9. 与其他手脚的组合关系

| 组合场景 | 天狮作用 | 下一步手脚 |
|---|---|---|
| 注册被阻止 | 查注册相关策略命中 | 档案中心、设备 SDK、DataAgent / Hive |
| 登录被验证 | 查登录审核 / 账号策略命中 | 用户登录统一日志、设备 SDK、档案中心 |
| ATO / 异常登录 | 补策略命中证据 | 用户登录统一日志优先，设备 SDK 次之 |
| 前端行为争议 | 补策略是否命中 | 前端活跃画像 / 行为序列 |
| 策略误伤 | 查策略命中证据 | 档案中心审核 / 打标日志、业务后验、DataAgent / Hive |
| 批量样本统计 | 不直接替代 | DataAgent / Hive |

## 9.1 v2.5.9 eventList API-read 路由补充

`eventList API-read` 是 `fastQueryHbase` 的请求级 / 事件级补证，不替代 `strategy_hit_check`。

触发 `eventlist_api_read` 的用户问法：

- “细查某次具体请求。”
- “看某个 eventType 明细。”
- “看注册事件字段。”
- “看登录事件字段。”
- “看实时反馈动作。”
- “看错误码 / 惩罚动作 / side effect。”
- “fastQueryHbase 查到了命中，再看下这条请求细节。”

不触发 `eventlist_api_read` 的问法：

- “是否命中生产策略？”默认优先 `fastQueryHbase`。
- “最近一周 / 一个月大盘趋势如何？”不使用 eventList，转 DataAgent / Hive 或要求缩小窗口。
- “批量统计多少用户命中？”不使用 eventList，转 DataAgent / Hive。

账号 eventType 推荐：

| 场景 | 同步 eventType | 异步 eventType |
|---|---|---|
| app 登录 | `LOGIN_AUDIT` | `ASYNC_LOGIN` |
| web 登录 | `LOGIN_AUDIT_FROM_WEB` | `ASYNC_WEB_LOGIN` |
| 注册 | `USER_REGISTER_NEW` | `REGISTER_NEW` |

查询窗口规则：

- 窗口尽量小，优先围绕已知事件时间点前后 5-15 分钟。
- 原则上不能跨天。
- 用户说“今天”时，应先基于已有证据定位具体时间段，再发起 eventList 细查。
- 不建议直接从 00:00 查到当前时间；如必须查较长窗口，应分段查询并记录 segmentation。

硬性边界：

- `sourceIds` 不能为空；为空时不得作为用户级证据。
- 401 / 403 / 跳登录是 auth blocker，不是 no_data。
- 命中策略事件 100% 记录，非命中策略事件存在抽样。
- `eventList no_data` 不代表用户无风险或行为未发生。

## 10. 本轮不做

- 不新增完整天狮策略分析能力。
- 不查策略配置、特征详情、策略版本、优先级和执行链路。
- 不做自动处罚、封禁、冻结或策略上线。
- 不修改 DataAgent / Hive 边界。
- 不替代用户登录统一日志、档案中心、设备 SDK、前端埋点。
