# ATO Real Case 001 Data Agent Parse

## 0. Case 基本信息

- case_id: `ATO_CASE_001_PASSWORD_KPN_RESWEEP`
- 试点阶段: v2.4 Data Agent-only 只读试点
- 触发 Skill: `account_security_expert_skill`
- 辅助能力: `dataagent_provider`, `human_review`
- 风险场景: 账号安全 / 盗号申诉 / ATO / 疑似密码泄露后异常登录与违规发布
- 输入充分性: case 标识、user_id、异常时间和业务场景已具备；本轮 Data Agent 只返回表检索与 SQL 生成，尚未返回执行结果。

## 1. Data Agent 返回状态识别

```yaml
parser_status: sql_only
execution_state: pending_execution
status_reason: >
  Data Agent 已完成表检索和 5 组取证 SQL 生成，但明确没有执行查询，
  当前在等待授权确认或人工下载 SQL 后执行。
  因此没有真实数据发现、样本统计、登录明细、发布明细或链路关联结果。
```

本次返回不是 `success` 数据证据，也不是 `failed`、`no_permission` 或 `empty_result`。它属于“查询计划已生成但尚未执行”的 `sql_only / pending_execution`。

## 2. returned_type

```yaml
returned_type: sql_only + table_search + query_plan
```

Data Agent 返回内容形态：

- 已识别候选取证数据范围：登录全景、作品发布、换绑操作、账号安全事件。
- 已生成 5 组取证 SQL：登录行为全景、发布作品行为、敏感操作、账号安全事件、登录-发布链路关联。
- 已提供 SQL 下载入口，但没有执行结果。
- 没有返回登录时间、登录方式、设备、IP、地区、发布作品、换绑、账号安全事件或链路关联的实际数据摘要。

## 3. key_findings

```yaml
key_findings:
  - Data Agent 能理解 ATO 取证目标，并将问题拆为登录、发布、换绑、安全事件、登录-发布链路 5 组取证任务。
  - Data Agent 找到了覆盖账号安全 ATO 判定所需的候选数据范围。
  - Data Agent 生成了可供后续执行的只读查询计划。
  - 本轮没有执行 SQL，因此没有真实数据发现。
```

注意：以上是“取证准备进展”，不是风险事实。

## 4. strong_evidence

```yaml
strong_evidence: []
```

原因：

- 没有真实查询执行结果。
- 没有证明“异常登录后短时间内发生违规发布 / 资料变更 / 换绑 / 改密 / 找回”。
- 没有证明“登录方式与历史习惯明显不同”。
- 没有证明“新设备 / 异地 / 非常用 IP / 非常用地区登录”。
- 没有证明“token/session 被踢、复用、异常切换或多端冲突”。
- 没有证明“风控策略命中盗号 / 密码泄露 / 回扫记录与链路一致”。

SQL 生成结果不得进入强证据。

## 5. medium_evidence

```yaml
medium_evidence: []
```

原因：

- Data Agent 没有返回任何已执行的数据摘要。
- 候选表和查询计划只能说明“可以怎样取证”，不能说明“风险已经发生”。

## 6. weak_evidence

```yaml
weak_evidence:
  - 用户申诉称 2026-04-17 发生异常登录且盗号者发布违规视频，但申诉文本只能作为背景，不能作为事实证据。
  - 人工备注称“电商 kpn 站点密码盗号，已回扫”，但人工备注只能作为 golden hint，不能作为事实证据。
  - Data Agent 已生成覆盖登录、发布、换绑、安全事件和登录-发布链路的查询计划，可作为后续补证路径。
```

弱证据解释：

- 用户申诉与人工备注对选 case 有价值，但不能单独支持 ATO 结论。
- SQL 计划可以说明取证方向合理，但没有执行结果前不能转成中/强证据。

## 7. counter_evidence

```yaml
counter_evidence:
  - counter_item: 常用登录方式、常用设备、常用 IP/地区是否与本次一致
    whether_closed: false
    reason: 尚未执行登录全景查询，无法判断。
  - counter_item: 发布行为是否来自历史常用设备或本人持续在线设备
    whether_closed: false
    reason: 尚未执行发布与登录链路关联查询。
  - counter_item: 是否存在正常新设备登录、用户本人误记时间或申诉时间偏差
    whether_closed: false
    reason: 缺真实登录、发布和账号安全事件数据。
  - counter_item: 人工备注中的“已回扫”是否能和数据链路对齐
    whether_closed: false
    reason: 尚未返回回扫记录或账号安全事件执行结果。
```

## 8. missing_evidence

```yaml
missing_evidence:
  - 登录行为实际结果：登录时间、登录方式、设备、IP、地区、风控命中、异常标签。
  - 历史登录基线：用户平时微信/验证码登录的历史模式是否成立。
  - 作品发布实际结果：异常时间附近是否有发布，发布设备和登录设备是否一致。
  - 登录-发布链路执行结果：异常登录到发布之间的时间差、设备一致性、IP一致性、地区一致性。
  - 敏感操作实际结果：换绑、改密、找回、资料变更等是否发生。
  - 账号安全事件实际结果：回扫记录、风险画像、策略命中、账号安全事件是否存在。
  - token/session 证据：是否存在踢 token、复用、多端冲突或异常切换。
  - 实时登录链路和实时设备指纹：Data Agent-only 当前无法充分覆盖。
```

## 9. quality_risks

```yaml
quality_risks:
  - SQL-only：本轮只有查询计划，没有执行结果。
  - 候选表覆盖不等于证据闭合。
  - SQL 下载链接或授权执行状态不是风险事实。
  - 人工备注可能与数据链路不一致，需要执行结果校验。
  - 用户申诉时间和实际异常发生时间可能存在偏差。
  - Data Agent-only 缺少实时登录链路、实时设备指纹和实时策略引擎明细。
```

## 10. provider_limitations

```yaml
provider_limitations:
  - provider: dataagent_provider
    limitation: 当前只完成离线数据表检索和 SQL 生成，未执行取数。
  - provider: dataagent_provider
    limitation: SQL-only 不能作为已查数结果。
  - missing_future_provider: realtime_log_provider
    limitation: 缺实时登录链路和请求级明细。
  - missing_future_provider: device_fingerprint_provider
    limitation: 缺实时设备指纹、设备环境和异常设备确认。
  - missing_future_provider: risk_engine_provider
    limitation: 缺实时策略引擎决策链路，只能等待离线账号安全事件或策略摘要。
```

## 11. conclusion_support

```yaml
conclusion_support:
  level: insufficient_support
  reason: >
    本轮 Data Agent 返回为 sql_only / pending_execution，没有真实执行结果。
    用户申诉和人工备注只能作为背景和 golden hint，不能进入中强证据。
    当前最多说明取证路径设计合理，不能支持“明确盗号”或“高度疑似盗号”。
```

## 12. recommended_next_provider

该字段由 Router / Dennis Agent 生成，不直接采用 Data Agent 的建议。

```yaml
recommended_next_provider:
  generated_by: router_or_dennis_agent
  next_action:
    - dataagent_provider: 授权执行已生成的只读 SQL，或人工下载 SQL 后在数据平台执行。
    - human_review_provider: 执行前人工确认 SQL 只读、时间窗口、user_id、业务动作范围和脱敏输出。
    - future_risk_engine_provider: 若离线结果显示策略命中或回扫链路，需要补策略引擎明细。
    - future_device_fingerprint_provider: 若离线结果显示新设备或设备异常，需要补实时/准实时设备指纹。
```

不建议在未执行 SQL 前进入 Case 003 的真实 Data Agent 执行队列；应先完成 Case 001 的 SQL 执行闭环，验证 parser 能处理真实表格 / 数据摘要。

## 13. manual_review_required

```yaml
manual_review_required: true
reason:
  - 需要人工授权或人工执行 SQL。
  - 需要确认 SQL 是否只读、是否限定 user_id 和推荐时间窗口。
  - 需要确认 Data Agent 返回的候选数据范围是否覆盖 ATO 关键证据。
  - 需要在执行结果返回后再做 Dennis Agent evidence-based judgement。
```

## 14. unified_normalized_evidence

```yaml
normalized_evidence:
  evidence_id: ato_case_001_dataagent_parse_001
  source_case_id: ATO_CASE_001_PASSWORD_KPN_RESWEEP
  source_query_intent_id: ato_case_001_ato_readonly_evidence
  source_provider_request_id: ato_case_001_dataagent_question
  provider: dataagent_provider
  provider_response_id: null
  status: sql_only
  returned_type: sql_only + table_search + query_plan
  evidence_type: ato_readonly_evidence
  applicable_skill:
    - account_security_expert_skill
    - dataagent_provider
    - human_review
  evidence_summary: >
    Data Agent 完成 ATO 取证表检索和 SQL 生成，但没有执行查询。
    当前没有真实数据发现，只能作为待执行取证计划。
  data_findings:
    - 已识别登录、发布、换绑、账号安全事件、登录-发布链路等候选取证范围。
    - 已生成 5 组只读取证 SQL。
  speculation_notes: []
  hypothesis_notes:
    - 如果执行结果显示异常登录后短时间违规发布，才可能支持 ATO 链路。
    - 如果执行结果显示登录方式偏离历史习惯，才可能支持密码泄露路径。
    - 如果执行结果显示回扫记录与链路一致，才可能支持人工备注。
  provider_conclusion_hint: null
  key_findings:
    - 取证计划覆盖登录、发布、敏感操作、账号安全事件和登录-发布链路。
    - 尚无 SQL 执行结果。
  strong_evidence: []
  medium_evidence: []
  weak_evidence:
    - 用户申诉文本，仅作背景。
    - 人工备注“密码盗号，已回扫”，仅作 golden hint。
    - SQL 查询计划，仅作待执行补证路径。
  counter_evidence:
    - 常用登录方式/设备/IP/地区是否一致：未查。
    - 发布行为是否来自常用设备：未查。
    - 回扫备注是否与数据链路一致：未查。
  missing_evidence:
    - 登录行为执行结果。
    - 历史登录基线。
    - 发布作品执行结果。
    - 登录-发布链路执行结果。
    - 敏感操作记录执行结果。
    - 账号安全事件和回扫记录执行结果。
    - token/session 异常执行结果。
  quality_risks:
    - SQL-only 不能作为已查数结果。
    - 人工备注不能作为事实证据。
    - 用户申诉不能作为事实证据。
    - Data Agent-only 缺实时 provider。
  freshness_notes:
    - 已有推荐时间窗口，但本轮未执行查询，无法评价数据新鲜度。
  permission_notes:
    - Data Agent 等待授权执行，当前不是 no_permission，但执行权限尚未实际确认。
  provider_limitations:
    - 当前只完成表检索和 SQL 生成。
    - 缺实时登录链路、实时设备指纹、实时策略引擎明细。
  conclusion_support:
    level: insufficient_support
    reason: SQL-only / pending_execution，无真实数据证据。
  recommended_next_provider:
    generated_by: router_or_dennis_agent
    providers:
      - dataagent_provider
      - human_review_provider
      - future_risk_engine_provider
      - future_device_fingerprint_provider
  manual_review_required: true
  raw_result_reference:
    provider: dataagent_provider
    queryId: null
    sessionId: null
    reference_strength: weak
    replay_supported: false
    note: 用户粘贴的是摘要，不包含 queryId/sessionId；SQL 下载链接不作为可回放证据。
  dennis_final_judgement:
    filled_by_parser: false
```

## 15. Dennis Agent 解释

一句话判断：当前不能判定 ATO，只能确认 Data Agent 已生成一套覆盖关键链路的只读取证计划；必须执行 SQL 后才能进入证据解释。

本质标识：

- 正常用户可能出现：新设备登录、异地登录、登录方式变化、发布作品、资料变更。
- ATO 更关键的是：登录方式或环境突变后，账号控制权发生变化，并在短时间内出现违规发布、资料变更、换绑、改密、找回、token/session 异常等下游动作。
- 最小区分点：异常登录 / 登录态异常与敏感动作之间是否存在可被数据证明的时间链路，并且反证没有推翻。

当前最多能下的结论：

```text
证据不足。Case 001 的取证计划合理，但尚未返回任何真实数据发现。
```

不能强结论的原因：

- SQL 尚未执行。
- 没有登录行为明细。
- 没有发布行为明细。
- 没有登录-发布链路结果。
- 没有回扫记录执行结果。
- 没有 token/session 证据。
- 人工备注“已回扫”尚未被数据侧验证。

补证动作：

1. 人工确认 SQL 只读、限定 user_id、限定推荐时间窗口。
2. 授权 Data Agent 执行，或人工下载 SQL 在数据平台执行。
3. 要求返回数据发现、表格摘要、缺失证据、口径风险，不要求 Data Agent 下最终风控结论。
4. 执行结果返回后，重新解析为 `unified_normalized_evidence`。

治理建议：

- 本轮不输出处罚、冻结、封禁、扣除或策略上线建议。
- 只建议继续只读取证和人工复核。

## 16. 与人工备注/标签是否一致

```yaml
manual_label: 是
manual_note: 电商 kpn 站点密码盗号，已回扫
consistency_with_dataagent_return: not_verifiable_yet
reason: >
  Data Agent 仅生成取证 SQL，没有执行结果。
  因此无法验证“密码盗号”“已回扫”是否与登录、发布、账号安全事件链路一致。
```

当前不一致也不冲突，只是“尚未验证”。

## 17. 是否需要回写 parser / question template / evidence boundaries

```yaml
need_backwrite:
  parser: optional
  question_template: no
  evidence_boundaries: no
```

说明：

- parser 已有 `sql_only` 规则，能正确降级。
- question template 已能让 Data Agent 找到候选数据范围并生成 SQL，说明模板基本有效。
- evidence boundaries 已明确 SQL-only 不得作为证据，暂不需要修改。

可选小增强：

- 在 parser 回归计划中增加 ATO-specific `pending_execution` 子状态，用于区分“SQL-only 且等待授权执行”和“SQL-only 仅生成查询逻辑”。

## 18. 是否可以进入 Case 003

```yaml
can_enter_case_003: not_recommended_yet
reason: >
  Case 001 仍停留在 SQL-only / pending_execution。
  建议先完成 Case 001 的授权执行和真实结果解析，验证 ATO parser 能处理真实数据表格和链路摘要后，再进入 Case 003。
```

如果为了并行提效，也可以准备 Case 003 的 Data Agent question，但不建议把它视为“Case 001 已通过”的下一阶段。
