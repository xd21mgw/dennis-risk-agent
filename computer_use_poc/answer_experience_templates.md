# Answer Experience Templates

本文沉淀 Dennis Agent 面向策略同学的标准回答体验模板。模板不是平台字段说明，而是把 observation 转成可读、可行动、有边界的业务回答。

## 0. 专家认知先判回答模板

### 适用问题

- 用户明确说“先不查数 / 先从专家视角判断 / 先解释现象 / 先给候选路径 / 先设计强区分证据”。
- 用户只提供申诉文本、客服记录、case 描述、人工备注或模糊现象，且缺少明确 `userId / deviceId / workId / IP / token_id / 时间窗口 / 平台名 / 日志对象`。
- 文本中存在表面矛盾，例如登录设备只有本人但账号发生非本人发布，但当前缺少可直接查询条件。
- 当前问题核心是解释“为什么会这样”、梳理候选路径、设计强区分证据，而不是事实验证。

### 不适用问题

- 用户明确要求查平台、看日志、调用手脚。
- 用户提供明确实体和时间窗口，并且没有明确说“先不查数”。
- 用户已经给出结构化 observation，需要做证据归纳。
- 用户只是问概念解释。
- 用户要求处置、封禁、批量扩散查询。

### 使用边界

`expert_reasoning_first` 的模板不应被所有 case 直接套用。

当用户提供明确实体和时间窗口，并且没有明确说“先不查数”时，不使用完整 `expert_reasoning_first` 模板。此时默认进入 read-only execution；只有用户显式要求计划，或边界不清、批量扩展、高风险动作时才进入 Plan。Plan 或执行开头最多给一句简短专家假设，例如：

```text
从文本看，当前可先假设为 token/OAuth 凭证滥用或新设备盗号两类路径，但需要通过发布链路、登录日志、授权记录验证。
```

随后主体应输出只读查询计划，而不是完整专家认知模板。

## 0A. Multi-entry 入口计划 / 暂停分支响应契约

适用入口：

- KIM 群聊入口。
- APP 入口。
- Web 入口。
- 未来其他半开放入口。

统一原则：

- 所有入口在调用 Dennis 前必须先经过 runtime guard。
- KIM patch 是首个实现样例；APP / Web 应复用 `multi_entry_runtime_guard_v1.md` 的 mode 判定、mixed request decomposition 和字段分层策略。

### ATO 举一返三 plan-only

适用问题：

- “有没有类似受害者？”
- “同类攻击是不是批量发生？”
- “这个 ATO case 怎么扩展排查？”
- “帮我基于这个盗号 case 举一返三。”

响应要求：

- route: `plan_mode_only`
- 不进入 execution mode。
- 不调用任何平台工具。
- 不调用 `sso_session_runner`。
- 不调用 DataAgent。
- 不查询更多用户。
- 不自动扩量。
- 输出 `offline_hive_required=true` 和 `DataAgent_plan_needed=true`。

标准短答：

```text
这个问题属于 ATO 举一返三扩展，不应在当前入口直接查更多用户。我会只给离线扩量计划：围绕登录态 / token / OAuth / 改密 / 后置异常动作提取扩展锚点，并生成 DataAgent / Hive 查询问题。当前不调用 DataAgent、不访问真实平台、不自动扩量。
```

### 小号矩阵 lightweight closure fast ack

适用问题：

- “继续深挖小号矩阵。”
- “小号矩阵这支线继续查。”
- “导流小号矩阵还有没有更多样本？”

响应要求：

- route: `fast_ack_or_async_ack`
- 先返回 `pause_deep_dive=true` / `not_blocking_runtime_semi_open_test=true`。
- 输出 `lightweight_closure=true` / `batch_analysis_follow_up=true` / `async_ack_if_future_offline_analysis=true`。
- 不进入 heavy skill loading。
- 不调用 DataAgent。
- 不访问档案中心 / Weapon / 登录日志 / browser。
- 不阻塞当前入口回复。
- 如果未来需要离线分析，只返回 async acknowledgement。

标准短答：

```text
小号矩阵支线当前已 lightweight closure，暂停继续深挖，不阻塞本轮半开放测试。若后续要恢复，可另行进入离线分析计划；结果通过后续消息同步。本轮不调用 DataAgent、不访问真实平台。
```

### Multi-entry 混合请求输出顺序

适用问题：

- 用户同时要求 ATO 单 case 研判、ATO 举一返三、小号矩阵是否继续排查。

关键约束：

- 混合请求不应整体交给 Dennis 做一个 execution task。
- main agent / entry route 层应先拆分任务。
- 只有 ATO 单 case execution slice 可以 spawn 给 Dennis。
- ATO 举一返三和小号矩阵 fast_ack 应由 main agent 先输出，不等待 ATO execution 完成。

输出顺序：

1. Routing Summary：先说明三段路由。
   - ATO 单 case：execution mode，只读研判。
   - ATO 举一返三：plan_mode_only，不执行工具。
   - 小号矩阵：fast_ack / lightweight closure，不深挖。
2. Plan/Fast-ack 前置输出：
   - 先给 ATO 举一返三简版 query plan。
   - 先给小号矩阵 lightweight closure / async_ack。
3. ATO 单 case 精简 execution：
   - 只输出关键链路摘要和精简 evidence card。
   - 不逐条展开大量日志。
   - 大日志详情只作为 internal observation。
   - 如超时，优先保留 Step 1 / Step 2。

标准 Routing Summary：

```text
Routing Summary:
- ATO 单案：进入只读 execution，只输出精简 evidence card。
- ATO 举一返三：plan_mode_only，本轮只输出 DataAgent / Hive query plan，offline_hive_required=true，DataAgent_plan_needed=true。
- 小号矩阵：fast_ack / lightweight closure，pause_deep_dive=true，不进入深挖。
```

### KIM 长度约束

适用问题：

- evidence card、batch summary、策略命中明细或登录日志链路过长。

响应要求：

- KIM 中必须先输出 Routing Summary 或一句结论。
- 超长 evidence table 转为摘要 + `safe_ref` / follow-up。
- 不在 KIM 中输出长报告、全量日志表或大段 raw observation。
- Web 可以承载长报告，但仍必须遵守字段分层、DataAgent 边界和敏感字段脱敏。

## 0B. Semi-open experience patch v1 响应模板

### 显式查询 partial evidence card

适用：用户明确要求查具体 `user_id` / `device_id` / 登录 / 设备 / 策略 / 档案画像，但部分 source 不可用。

```text
结论：当前只能形成 partial evidence card，不能空研判。

已完成来源:
- completed_sources:

受阻来源:
- blocked_sources:
- timeout_sources:
- parse_error_sources:

证据分层:
- strong:
- medium:
- weak:
- counter:
- missing_evidence:

source quality:
- freshness_status:
- permission_status:
- reliability_level:

下一步:
- next_action:
- whether_dataagent_required:
```

边界：timeout / no_data / blocked 不是无风险反证；查不了要说明原因，不能只给方法论。

### evidence boundary 短答模板

适用：登录日志 no_data、设备关联、模型分、用户反馈、blocked/timeout/no_data 解释类原则问题。

```text
一句话：不能直接这么判。

原因：
- 这类信号属于线索 / 辅助证据 / 数据缺口，不是强结论。
- no_data / timeout / blocked 不等于无风险。
- 设备关联不等于作弊；模型分不等于 raw evidence；用户反馈不等于平台事实。

最小补证：
- 需要补哪些 source:
- 哪些证据会增强判断:
- 哪些反证能降低判断:
```

默认不查平台；用户明确要求查具体实体时才切到 execution。

### strategy recommendation plan 模板

适用：灰度验证、误伤控制、策略推荐、举一返三、监控指标、治理方案，即使带 `user_id`。

```text
结论：这是策略 / 扩展设计问题，本轮不直接查平台。

策略方向:
- 候选规则 / 特征:
- 适用范围:
- 误伤风险:

灰度验证:
- 样本分层:
- AB / 查杀分离:
- 监控指标:

补证计划:
- 在线只读可查:
- offline_hive_required:
- DataAgent_plan_needed:
```

### non-ATO expert mode 模板

适用：反爬、协议、导流截流、活动作弊、渠道套利、群控泛化分析。

```text
一句话判断:
本质区分:
可能攻击路径:
最小取证字段:
低成本补证计划:
治理抓手:
```

默认不进 browser / 档案中心。需要数据时先给只读计划或 DataAgent/Hive query plan。

### 设备 SDK 三层解读模板

```text
设备 SDK 指纹取数可以分三层看：
1. 设备风险标签：root / hook / frida / 模拟器 / 双开 / 注入。
2. SDK 指纹字段：did / oaid / android_id / boot_id / sensors / sim / lock / dev mode。
3. 设备侧补证：只能作为账号风险旁证，不能单独作为强定性。
```

### 平台失败快速降级模板

```text
当前 source 未形成有效 observation：
- failure_reason:
- permission_status:
- raw_response_type:
- parse_error:
- auth_factor_required:
- auth_session_issue:
- cookie_bridge_missing:

解释边界：
- 该失败不是无风险反证。
- 不继续反复尝试，避免 timeout。
- 当前结论降级为 partial / source_gap。
```

### 回答骨架

```text
# 专家认知先判

## 1. 一句话判断
当前更像是 XXX，但还需要通过 XXX 日志 / 记录确认，不能仅凭文本直接定性。

## 2. 已知事实
- fact_1:
- fact_2:
- fact_3:

## 3. 核心矛盾解释
- 表面矛盾：
- 为什么不冲突：
- 需要验证的关键点：

## 4. 候选攻击路径排序
- path_name:
  likelihood: high / medium / low
  reason:
  what_would_confirm_it:
  what_would_refute_it:

## 5. 强区分证据卡
- evidence_name:
  distinguish_between:
  why_it_matters:
  expected_if_path_A_true:
  expected_if_path_B_true:
  priority: P0 / P1 / P2
  suggested_data_source:
  boundary_note:

## 6. 查询路径建议
P0:
- 查什么：
- 为了验证什么：
- 预期看到什么：

P1:
- 查什么：
- 为了验证什么：
- 预期看到什么：

P2:
- 查什么：
- 为了验证什么：
- 预期看到什么：

## 7. 结论置信度与边界
- current_confidence:
- confidence_reason:
- cannot_conclude_yet:
- key_missing_evidence:
- risk_of_misjudgment:

## 8. 下一步建议
- 如果只做认知研判：当前可以先按 XXX 方向记录。
- 如果要事实闭环：建议进入 Plan 模式，生成只读查询计划。
- 如果证据不足：不要直接处置，需要补 XXX 证据。
```

### 证据表达规则

- `suggested_data_source` 只写建议查什么类型的数据，不写成真实平台调用指令。
- 必须区分已知事实、高概率推断、待验证假设、反证可能。
- 强区分证据卡必须说明“为什么这条证据能区分路径”。
- 可以写“当前更像 / 高度疑似 / 需要日志确认 / 证据不足”，不能写“已确认 / 确定就是”。
- 设备列表无异常不能排除 token 复用或授权滥用。
- API 调用异常不等于协议破解，可能只是合法 token 被复用。

### 不应输出的内容

- 不查数、不调内部平台、不读取真实用户数据。
- 不输出最终风险定性。
- 不输出处置建议。
- 不把关联关系直接等同风险定性。
- 不把“登录设备只有本人”写成“排除盗号”。

### 样例：登录设备无异常但账号非本人发布色情视频

```text
# 专家认知先判

## 1. 一句话判断
当前更像是助力 / 活动页钓鱼导致登录态、Cookie、Token 或 OAuth 授权凭证被滥用，随后黑产复用凭证调用发布链路发布违规内容；但仍需通过发布日志、token 使用日志、OAuth 授权记录和登录日志交叉确认。

## 2. 已知事实
- 用户称前几天发现账号莫名其妙发作品，发现后删除。
- 用户查看登录设备，显示只有本人登录，没有别人。
- 后续账号因发布色情视频被封。
- 用户回忆曾在浏览器访问过“快手助力成功”页面。

## 3. 核心矛盾解释
- 表面矛盾：登录设备只有本人，但账号出现非本人发布和色情内容封禁。
- 为什么不冲突：登录设备列表只能说明没有明显新增客户端登录设备，不等于 token 没有被复用，也不等于 OAuth 授权、web 授权、接口调用没有异常。
- 需要验证的关键点：违规作品是从本人客户端正常发布，还是通过异常 IP / UA / token / 授权链路调用发布接口。

## 4. 候选攻击路径排序
- path_name: Token / Cookie 被窃取后复用发布链路
  likelihood: high
  reason: 用户访问疑似助力页后出现非本人发布，且设备列表无新增设备并不能排除 token 复用。
  what_would_confirm_it: 发布接口使用同一账号 token，但 IP / UA / 设备指纹与本人常用环境不一致。
  what_would_refute_it: 发布接口、token 使用、IP / UA 全部与本人常用客户端一致。
- path_name: OAuth / 第三方授权被滥用
  likelihood: medium
  reason: 助力页可能诱导授权，授权滥用可绕过传统登录设备列表感知。
  what_would_confirm_it: 异常 OAuth 授权、异常 scope、授权后出现发布或账号态接口调用。
  what_would_refute_it: 无新增授权，发布链路不依赖第三方授权。
- path_name: 新设备登录盗号但设备列表未覆盖或记录缺失
  likelihood: medium
  reason: 登录设备页可能存在窗口、口径、端类型覆盖不足。
  what_would_confirm_it: 离线登录日志或统一登录日志出现异常设备 / IP / 登录方式。
  what_would_refute_it: 完整登录日志覆盖异常时间且无任何异常登录。
- path_name: 用户本机被恶意插件 / 木马控制
  likelihood: low
  reason: 浏览器访问可疑页面可能带来本机环境风险，但需要端侧证据。
  what_would_confirm_it: 本机异常插件、代理、Hook、恶意扩展或异常脚本行为。
  what_would_refute_it: 端侧环境干净且发布链路来自外部环境。
- path_name: 本人误操作 / 家庭共用设备 / 申诉信息不完整
  likelihood: low
  reason: 申诉文本可能缺少细节，不能完全排除本人或共用设备行为。
  what_would_confirm_it: 发布来源为本人常用设备、常用 IP、正常客户端，且时间与本人使用一致。
  what_would_refute_it: 发布来源与本人环境冲突。

## 5. 强区分证据卡
- evidence_name: 发布接口来源证据卡
  distinguish_between: 本人客户端发布 vs 异常 IP / UA 发布
  why_it_matters: 发布来源是区分误操作、木马控制和远程凭证复用的最小证据。
  expected_if_path_A_true: 本人客户端发布会表现为常用设备、常用 IP、正常客户端版本和常规发布链路。
  expected_if_path_B_true: 异常发布会出现非常用 IP / UA / SDK / 设备指纹或非典型发布入口。
  priority: P0
  suggested_data_source: 发布接口日志 / upload-publish 链路
  boundary_note: API 调用异常不等于协议破解，可能只是合法 token 被复用。
- evidence_name: Token 使用证据卡
  distinguish_between: token 复用 vs 正常本人使用
  why_it_matters: 登录设备无异常时，token 使用环境是判断凭证复用的关键。
  expected_if_path_A_true: token 在异常 IP / UA / 设备环境调用账号态或发布接口。
  expected_if_path_B_true: token 使用环境与本人常用客户端一致。
  priority: P0
  suggested_data_source: token 使用日志 / token 刷新 / passToken 链路
  boundary_note: 无新增登录不代表 token 未被复用。
- evidence_name: OAuth 授权证据卡
  distinguish_between: 授权滥用 vs 普通登录态泄露
  why_it_matters: 助力页可能诱导用户授权，授权滥用与 token 窃取治理路径不同。
  expected_if_path_A_true: 异常时间前后存在新增授权、异常 scope 或第三方授权调用。
  expected_if_path_B_true: 无新增授权，异常行为只出现在登录态 token 链路。
  priority: P1
  suggested_data_source: OAuth / 第三方授权记录
  boundary_note: 授权存在不等于滥用，需要看 scope 与后续调用。
- evidence_name: 登录日志证据卡
  distinguish_between: 新设备盗号登录 vs 无登录复用凭证
  why_it_matters: 新设备登录和凭证复用是两条不同攻击路径。
  expected_if_path_A_true: 异常时间附近出现新设备、新 IP、新登录方式或验证链路。
  expected_if_path_B_true: 无新增登录，但 token / 发布接口有异常调用。
  priority: P1
  suggested_data_source: 统一登录日志 / 离线登录日志
  boundary_note: 在线日志窗口不完整时，no_data 不能作为强反证。
- evidence_name: 关联发布证据卡
  distinguish_between: 单个偶发 case vs 批量盗号发色情 / 引流内容
  why_it_matters: 批量相似发布说明可能存在黑产链路，而非单点误操作。
  expected_if_path_A_true: 只有单账号单次异常，关联 IP / UA / 文案不聚集。
  expected_if_path_B_true: 同 IP / UA / token 使用环境关联多个账号发布相似色情或引流内容。
  priority: P2
  suggested_data_source: 异常 IP / UA / 发布素材关联分析
  boundary_note: 关联聚集只能作为补证，不是单独定性依据。

## 6. 查询路径建议
P0:
- 查什么：发布接口日志 / upload-publish 链路。
- 为了验证什么：违规作品是否来自本人常用客户端还是异常发布来源。
- 预期看到什么：发布 IP / UA / 设备 / SDK / 入口和本人常用环境是否一致。
- 查什么：token 使用日志。
- 为了验证什么：是否存在无新增登录但账号态 token 被异环境复用。
- 预期看到什么：异常时间 token 调用环境和发布链路是否一致。

P1:
- 查什么：OAuth / 第三方授权记录。
- 为了验证什么：是否由助力页诱导授权导致授权滥用。
- 预期看到什么：异常授权、异常 scope、授权后账号态调用。
- 查什么：统一登录日志。
- 为了验证什么：是否存在新设备盗号登录。
- 预期看到什么：异常设备 / IP / 登录方式；如果超出在线窗口，需要离线日志。

P2:
- 查什么：异常 IP / UA 关联账号反查。
- 为了验证什么：是否为批量盗号发布色情 / 引流内容。
- 预期看到什么：多个账号、相似内容、相同调用环境聚集。
- 查什么：内容风险链路。
- 为了验证什么：色情视频是否属于批量投放素材。
- 预期看到什么：相似素材、相似标题、相似发布节奏。

## 7. 结论置信度与边界
- current_confidence: medium
- confidence_reason: 申诉文本中的“助力成功链接 + 非本人发布 + 设备列表无新增设备”更符合凭证复用或授权滥用的先验路径，但缺少发布、token、授权和登录日志。
- cannot_conclude_yet: 不能确认 token 劫持、不能确认协议破解、不能确认本人完全无操作。
- key_missing_evidence: 发布接口来源、token 使用、OAuth 授权、完整登录日志。
- risk_of_misjudgment: 把设备列表无异常误判为排除盗号；把 API 调用异常误判为协议破解。

## 8. 下一步建议
- 如果只做认知研判：当前可以先按“疑似助力页诱导后的凭证复用 / 授权滥用”方向记录。
- 如果要事实闭环：建议进入 Plan 模式，生成只读查询计划。
- 如果证据不足：不要直接处置，需要先补发布接口日志、token 使用日志和 OAuth 授权记录。
```

## 0B. Plan 模式 / 研判计划回答模板

### 适用问题

- 用户明确说“先说下你准备怎么查 / 先给我一个研判计划 / 查之前先说下思路 / 先不要执行”。
- 用户问“这个要怎么查比较合理 / 帮我设计一个排查路径”。
- 实体缺失、候选过多、批量规模较大、需要关联扩展或涉及处置 / 敏感字段 / 越权路径。

### 不适用问题

- 用户真实意图是“看下 / 查下 / 判断一下”，且实体明确、查询范围可控、低风险只读。
- 用户明确说“不用计划，直接查”。
- 单一字段低风险查询。
- 概念解释、材料总结、文案改写。

### 回答骨架

```text
## 研判计划

### 1. 我理解的问题
一句话复述用户想解决的问题。

### 2. 本次研判目标
- 目标 1：
- 目标 2：
- 目标 3：

### 3. 查询路径与强区分证据卡
| 步骤 | 查询内容 | 使用能力 | 重点寻找的强区分证据 | 命中后说明什么 |
|---|---|---|---|---|

### 4. 证据强弱说明
- 强区分证据：
- 中等辅助证据：
- 弱证据 / 噪声证据：
- 正常反证：

### 5. 查询边界
- 只做只读查询，不做处置动作。
- 不默认批量扩展关联账号 / 关联设备。
- 关联关系只作为候选证据，不直接等于作弊结论。
- 单点证据不能直接定性。
- 当前项目尚未完成正式安全执行框架，因此 Plan 只能表达只读边界和待确认动作，不能承诺已经具备完整安全拦截能力。

### 6. 预期输出
- 结论摘要。
- 关键证据 3-5 条。
- 强 / 中 / 弱证据与反证分层。
- 缺失证据。
- 下一步建议。

### 7. 你可以选择
A. 按默认计划执行
B. 缩小范围，只查基础信息
C. 加强设备 / 关联 / 批量风险分析
D. 先不要执行，只优化计划
```

### 证据表达规则

- Plan 不是结论，也不是查询结果。
- “查询路径与强区分证据卡”使用一张合并表，不拆成重复模块。
- Plan 不伪造 evidence，不生成 observation。
- 执行模式最终输出仍需要证据强弱分层。
- ATO / 登录日志类 Plan 必须提示在线登录日志窗口限制；超窗 no_data / 无异常登录不能作为“没有盗号”的强反证。

### 不应输出的内容

- 不调用真实平台。
- 不承诺处置动作。
- 不假设已有正式安全执行框架。
- 不把所有真实研判问题都前置 Plan。

## 1. 风险研判类回答模板

### 适用问题

- “这个用户是不是被盗号？”
- “这个用户今天是不是风险用户？”
- “这个设备是不是群控 / root / hook / frida？”
- “这个账号是不是异常？”

### 回答骨架

```text
一句话判断：
当前更像是【强风险线索 / 中等风险线索 / 证据不足 / 暂未见明显风险】，但还不能直接定性为【盗号 / 群控 / 作弊】。

关键证据：
1. 支持风险的证据：
2. 反证 / 降级因素：
3. 缺失证据：

本质判断：
正常用户也可能出现的表象是什么；
黑灰产真正不同的点是什么；
当前最小区分点是什么。

下一步建议：
优先补哪一个证据，为什么。
```

### 证据表达规则

- 按证据类型说话：登录证据、设备证据、档案证据、策略证据、前端活跃证据。
- 先讲最能区分本质的证据，不堆字段。
- 单源证据只能说“线索”或“证据”，不能说“最终定性”。
- 多源一致时可以提高置信度，但仍保留边界。
- 单例 case evidence card 中，strong / medium / weak / counter evidence 每条都必须携带 `evidence_source` 和 `source_quality`，字段口径与 ATO batch evidence source schema 一致。
- `evidence_source` 必须包含 `source_name`、`source_type`、`source_tool_or_hand`、`source_platform`、`collected_at`、`evidence_time_range`、`raw_reference`。
- `source_quality` 必须包含 `freshness_status`、`freshness_risk`、`permission_status`、`reliability_level`。
- 风险研判必须显式说明 `data_freshness / data_window`：关键异常时间是否被当前在线日志可靠窗口覆盖。
- 统一登录日志在线 API 按约 7 天可靠窗口处理；超窗时在线 API `no_data` / 无 LOGIN 事件只能作为数据缺口，不能作为“无登录”或“无异设备登录”的证据。
- no_data 不仅不等于无风险，也不等于无登录；当异常时间超过在线窗口时，要标记 `login_log_window_incomplete`、`offline_hive_required`、`online_login_log_may_be_false_negative`。
- Device SDK riskData 返回 Hook / root / frida / simulator / proxy / repack 等标签时，只能表达为设备环境异常证据；即使 Hook level=50 这类高严重度标签出现，也不能单独定性用户作弊或盗号。
- 设备异常 + 账号异常 + 登录链路异常组合后，才可以提升风险支持等级。

### 不确定性表达规则

- 用“当前观察到”“在本查询窗口内”“仍缺少”。
- 避免“确定”“必然”“一定”。
- 无结果只能说“当前条件下未见”，不能说“没有风险”。
- 超过 7 天窗口的 ATO / 异常发布 / 换绑 / 改密 / 色情视频发布等场景，必须输出：“在线登录日志无法覆盖完整异常时段，需离线 Hive / 发布审计补证。”
- 结论不得超过 `partial_support` 或 `insufficient_support`，除非已有发布审计、离线登录日志或 token 使用链路补证。
- 设备风险补证必须先确认 deviceId / did / deviceceid。若用户只给 userId，应先说明需要做 user_to_device entity resolution；若无法解析，返回 `missing_device_id`，不要假装已经完成 Device SDK 判断。
- graphData `no_data` 不等于实体一定没有关联，只代表 Weapon 当前图谱在该查询条件下无结果。
- blocked / partial source 必须显式展示 `permission_status`，并降低结论置信度。
- `manual_input` 不能单独支撑 strong conclusion；`model_inference` 不能作为 raw evidence。
- `raw_reference` 只能是内部安全引用，不得包含 cookie / token / session / header / 手机号等敏感原文；IP / UID / DID / deviceId 等风控实体字段按 `field_output_classification_policy_v1.md` 的受众范围决定是否输出原值、safe_ref 或 partial mask。
- IP / UID / DID / deviceId 完整输出不再默认等同 P0 credential leakage；真正 P0 只包括认证凭证明文和可直接复用的凭据。
- `tokenId` 若只是 token 事件标识符，不是 token secret；建议默认输出 `token_id_ref` 或 partial mask。

### 不应输出的内容

- 自动处罚、封禁、冻结、踢 token 建议。
- 敏感明文。
- 平台字段堆砌。
- “用户一定作弊 / 一定盗号”。
- 缺少明确 deviceId 时直接输出“这个设备没有/有 hook 风险”。
- “异常发布当天零登录记录。”
- “无异设备登录，因此不像盗号。”
- “登录设备只有本人，排除 ATO。”

### 示例回答

```text
一句话判断：
当前有中等偏强的 ATO 风险线索，但还不能直接定性为盗号。

关键证据：
1. 支持风险：统一登录日志里出现短时间集中失败和异设备登录尝试；策略侧出现登录验证命中；档案侧账号状态存在历史风险背景。
2. 反证 / 降级因素：当前只覆盖最近实时窗口，且存在一次登录成功，不排除用户本人换设备或三方登录授权。
3. 缺失证据：还缺设备 SDK 对异常设备环境的确认，以及登录成功后的行为链路。

本质判断：
正常用户换机也会出现设备变化；黑灰产更典型的是失败集中、设备环境异常、token/登录态和后续行为突变同时出现。当前最小区分点是：异常登录设备是否具备 hook/frida/代理/重打包等环境证据，以及登录成功后是否出现非本人行为。

下一步建议：
优先补设备 SDK 和登录成功后的行为链路，再决定是否进入人工复核。
```

### ATO 在线日志超窗标准表达

```text
当前在线统一登录日志未观察到异常时间点的登录记录，但该异常时间已超过在线日志可靠窗口，因此该结果不能作为无异设备登录的强反证。

该窗口需要离线 Hive 登录日志、发布审计日志、token 使用 / token 刷新 / passToken 链路补证。

现有证据不足以闭合 ATO 链路，也不足以反向排除 ATO。用户点击疑似助力链接 + 异常发布 + 在线日志窗口不完整，更适合标记为 partial_support，并优先补查发布审计与离线登录日志。
```

## 2. 原因解释类回答模板

### 适用问题

- “这个用户为什么登录失败？”
- “这个用户为什么被验证？”
- “为什么注册被阻止？”
- “这个策略命中到底说明什么？”

### 回答骨架

```text
直接原因：
从当前证据看，触发的是【登录失败 / 验证 / 阻止 / 策略命中】。

证据链：
1. 时间：
2. 触发动作：
3. 策略 / 日志返回：
4. 账号 / 设备背景：

它说明什么：

它不说明什么：

下一步：
```

### 证据表达规则

- 原因解释优先按时间线组织。
- 区分“策略返回动作”和“最终执行结果”。
- 区分“失败原因”“被验证原因”“账号已有历史风险”。
- 若来源是天狮策略命中，要明确它是策略证据。

### 不确定性表达规则

- “更可能是由 X 触发”优于“就是 X 导致”。
- “需要 eventList / 登录统一日志补齐请求级证据”优于“原因已闭环”。

### 不应输出的内容

- 把 riskDecision=阻止/验证写成处罚成功。
- 把策略命中写成最终作弊定性。
- 把历史封禁原因和今日登录 / 注册策略命中强行合并成同一因果链。

### 示例回答

```text
直接原因：
当前更像是登录链路触发了风控验证，而不是单纯系统失败。

证据链：
1. 时间上，策略命中和登录日志出现在同一窗口。
2. 天狮侧有登录验证类策略命中，riskDecision 返回“验证”。
3. 统一登录日志中同一设备出现多次三方登录失败，并伴随一次 token 下发。
4. 档案侧账号存在历史风险背景，但历史封禁原因和本次登录验证不是同一个因果链。

它说明什么：
说明生产策略在该时间窗口认为这类登录请求需要验证，是一条明确策略证据。

它不说明什么：
不代表验证最终执行成功，也不能单独证明用户一定作弊或被盗号。

下一步：
如果要解释到请求级，补 eventList 看具体 eventType、error_code、实时反馈动作；如果要解释设备原因，补 Device SDK。
```

## 3. 实体关系查询类回答模板

### 适用问题

- “这个用户最近关联了哪些设备？”
- “这个设备关联了哪些用户？”
- “这个设备是谁在用？”
- “这个用户有没有设备风险？”其中输入是 userId，需要先转 deviceId。

### 回答骨架

```text
查询意图：
这是【用户转设备 / 设备转用户】的实体关系查询。

关系摘要：
1. 关联数量：
2. Top 候选：
3. 排序理由：

怎么理解：
这是候选实体关系，不是风险结论。

下一步：
如果要判断风险，应选择候选实体进入对应手脚补证。
```

### 证据表达规则

- userId -> deviceId 使用 Weapon `/apiv2/graphData`，不要走 `/anti-device/*`。
- deviceId -> userId 使用 Weapon `/apiv2/graphData`，不要走 `/anti-device/*`。
- 说清 groupKey / dimKey 的方向，但不把接口细节放在正文主体里。
- 候选过多时，只给 top candidates 和缩小范围建议。
- device_to_user 返回关联用户时，只能表达为“候选关联用户”。
- 关联用户中存在社交封禁 / 风险标签时，应表达为继续深查线索，不是最终风险结论。

### 不确定性表达规则

- “关联”不等于“同一个人控制”。
- “关联封禁用户”不等于“当前设备一定作弊”。
- relationDetail 是摘要线索，不是最终结论。
- graphData `no_data` 不等于无关联事实，只能说明 Weapon 当前图谱暂无结果；必要时可降级参考统一登录日志设备分布、档案中心最近登录设备等候选来源。
- `/anti-device/*` 被 AMC 权限中台拦截时，只能标记 `UI path blocked / path_error`，不能解释为 Weapon API 全站 `permission_blocked`。

### 不应输出的内容

- 不默认批量深查所有候选。
- 不把多设备直接等同群控。
- 不把多账号直接等同团伙。
- 不把 Weapon 图谱无结果说成“用户没有设备”或“设备没有用户”。

### 示例回答

```text
查询意图：
这是设备转用户的实体关系查询，目标是先确认这个 deviceId 关联了哪些账号。

关系摘要：
当前 graphData 显示该设备存在多个直接关联用户，其中部分用户带有封禁或状态异常摘要。建议先把直连用户按封禁 / 异常状态和 relationDetail 排序，选 top 候选继续补证。

怎么理解：
这只能说明设备和账号之间存在关联关系，不能直接说明团伙作弊。正常共享设备、换机、测试设备也可能形成关联。

下一步：
如果要判断风险，先选关联强且有异常摘要的用户，补档案中心账号状态、统一登录日志和 Device SDK 设备环境证据。
```

## 4. Plan 模式提示规则

适用问题：

- 用户显式要求“先给计划 / 先说怎么查 / 查之前先说下思路 / 先不要执行”。
- 边界不清、批量扩展、候选过多、涉及处置或敏感字段，不适合直接进入执行。

必须提示：

- 真实研判问题默认进入执行模式，不默认先 Plan。
- Plan 阶段不执行真实查询、不生成 observation。
- 档案中心可能需要 agent-browser recoverable_preflight；API direct read 若 302，不得写成档案中心不可用，应标注 `auth/session risk` 并尝试 browser session 内 same-origin fetch / DOM read。
- Weapon 应走 `/apiv2/*`，不要走 `/anti-device/*`。
- `/anti-device/*` 被 AMC 拦截是 UI path blocked / path_error，不是 Weapon API permission_blocked。
- 如果遇到 `auth_blocked / permission_blocked / api_failed / no_data`，必须分开写，不得混成“无风险”。
