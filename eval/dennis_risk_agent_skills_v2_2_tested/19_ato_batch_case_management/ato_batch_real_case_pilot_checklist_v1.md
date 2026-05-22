# ATO Batch Real-case Pilot Checklist v1

## 1. Pilot 目标

本 checklist 用于下一阶段 3-5 个真实脱敏 ATO case 的小样本验证。目标不是做自动处置或自动策略上线，而是验证 ATO batch input / output contract v1 是否能稳定处理真实脱敏 case，并产出策略同学可读的证据卡、模式摘要、来源覆盖和人工复核边界。

验证目标：

- 验证 batch input / output contract 是否能处理真实脱敏 case。
- 验证 evidence card / pattern summary / source coverage 是否对策略同学有用。
- 验证是否能识别 missing evidence、window gap、permission gap、manual review boundary。
- 验证 candidate strategy direction 是否保持候选方向，不越界到自动上线或自动处置。

执行边界：

- 不调用真实 DataAgent。
- 不访问真实内部平台。
- 不修改 release / outputs/dist。
- 不输出真实敏感信息。
- 不把内部 Agent observation 当成自动处置依据。

## 2. Case 选择标准

推荐输入规模：

- 3-5 个真实脱敏 case。
- 每个 case 必须能映射到 ATO / 疑似账号接管 / 登录后异常操作。

优先选择：

- ATO / 疑似账号接管 case。
- 登录后出现异常发布、改资料、私信、关注、支付、换绑、改密等后置动作的 case。
- 至少 1 个证据完整 case。
- 至少 1 个证据不足 case。
- 至少 1 个登录日志超窗、source gap 或 permission gap case。

暂不建议一开始选择：

- 超复杂跨场景 case，例如同时涉及 ATO、导流互动、活动套利、支付欺诈和内容处罚。
- 缺少 user_id、event_time、abnormal_action 三个核心字段的 case。
- 需要大批量扩散、跨长周期统计或未授权 Hive 查询才能判断的 case。
- 明确不是 ATO 的账号矩阵 / 导流互动 / 养号池 case。

## 3. 脱敏要求

实体脱敏：

- `user_id` 可保留为内部数字 ID 或映射 ID，但不输出手机号、实名、昵称等敏感个人信息。
- `device_id` / did / deviceceid 需脱敏或只保留前后缀。
- IP 只保留脱敏网段，例如 `183.206.xxx.xxx`。
- 手机号只保留后四位或完全隐藏。
- 昵称、头像、简介、外部联系方式只输出模式摘要，不输出敏感明文。

认证与请求脱敏：

- 不输出 cookie / token / session / storageState / header。
- 不输出完整 requestParam / extraParam / full JSON。
- 不输出完整内部 URL 中的敏感参数。

source 引用：

- `raw_reference` 只能使用内部安全引用，例如 `safe_ref://case_001/login_log`。
- 不粘贴敏感原文。
- `model_inference` 只能作为 hypothesis，不能作为 raw evidence。

## 4. 输入字段检查

每个真实脱敏 case 进入 pilot 前必须检查：

| field | requirement | missing handling |
|---|---|---|
| `case_id` | 必填 | missing_case_id，需要补齐 |
| `user_id` | 必填 | missing_user_id，不进入事实结论 |
| `event_time` | 必填 | missing_event_time，不能判断登录日志窗口 |
| `abnormal_action` | 必填 | missing_abnormal_action，不能确认 ATO 后置动作 |
| `device_id` | 如有强建议 | missing_device_id，进入 missing evidence |
| `user_claim` | 如有强建议 | 只能作为 clue，不是强证据 |
| `source_channel` | 强建议 | source_channel_unknown |
| `available_evidence` | 强建议 | no_initial_evidence |
| `missing_evidence` | 强建议 | 由 Agent 补充初始缺口 |
| `notes` | 可选 | 不放敏感原文 |

输入规模检查：

- 3-5 cases：适合 real-case pilot。
- 少于 3 cases：建议转 single / few case analysis。
- 超过 5 cases：仍可作为后续批量分析，但 pilot 阶段建议先抽样。
- 候选实体过多：标记 `too_many_candidates`，先缩小范围。

## 5. 内部 Agent 只读 Observation 范围

内部 Agent 在 pilot 中只做只读 observation，不能做写操作或处置。

允许的只读范围：

| source | readonly scope | boundary |
|---|---|---|
| 档案中心 | 用户基础画像、账号状态、近期行为摘要、负向标签、审核摘要 | API / browser 只读，不点击处置按钮 |
| 统一登录日志 | 登录时间、设备、IP、登录结果、token 生命周期摘要 | 近 7 天 reliable window；超窗标记 offline_hive_required |
| Weapon / Device | user_to_device、device_to_user、设备风险标签 | 设备异常只作为补证，不单独定性用户作弊 |
| 天狮 / 策略平台 | 策略命中、请求级事件摘要 | 只读；no_data 不代表行为不存在 |
| 前端埋点 | 必要时读取用户活跃路径或活跃存在性 | 只作为行为补证，不证明本人操作 |

禁止动作：

- 封禁、解封、限流、放过、改规则、审批、导出明细。
- 自动扩散所有关联账号 / 设备。
- 输出敏感字段明文。

## 6. DataAgent / Hive 触发边界

默认不自动调用 DataAgent。

只生成 Hive query plan 的场景：

- 登录日志超出近 7 天 online reliable window。
- 在线日志窗口不足以覆盖异常时间。
- 需要长周期登录、token、发布审计、行为日志或批量聚合。
- 需要确认同类攻击链路规模、变体或误伤风险。

进入 DataAgent / Hive 的条件：

- 用户明确要求查数或补离线数据。
- 查询范围、字段、脱敏要求和审批边界明确。
- DataAgent 仍只作为 Hive / 数仓取数分析能力，不是万能风控执行器。

禁止：

- Dennis Agent 默认自动调用 DataAgent。
- 将 DataAgent 输出直接变成自动处置。
- 将 Hive query plan 写成已执行结果。

## 7. 输出验收标准

pilot 输出必须包含：

- 每个 case 有 evidence card。
- 每条核心证据有 `evidence_source` / `source_quality`。
- batch pattern summary 能聚合共性，或明确说明无法聚类。
- source coverage 能指出完整、缺失、超窗、blocked 来源。
- missing evidence 明确可补路径。
- candidate strategy direction 不越界。
- manual review boundary 清晰。

禁止误用：

- 不把设备关联直接定性作弊。
- 不把 no_data 当反证。
- 不把 manual_input / model_inference 当 strong evidence。
- 不把后置行为直接当成 ATO 主因。
- 不把内部 Agent observation 当成自动处置依据。

## 8. Pilot 通过标准

通过条件：

- 3-5 个 case 能完成结构化输出。
- 至少识别 1 类共性 pattern，或明确说明无法聚类及原因。
- 能明确哪些 case 需要补数据。
- 能明确哪些 case 暂不建议处置。
- 能输出策略同学可读的下一步建议。
- 输出不包含敏感明文。
- 不调用真实 DataAgent。
- 不自动处置、不自动上线策略。

不通过条件：

- 缺字段 case 被输出为强结论。
- manual_input / model_inference 被当成原始强证据。
- 登录日志超窗 no_data 被当成无异常登录反证。
- 候选策略方向被写成自动上线结论。
- 内部 Agent observation 被直接写成处置依据。

## 9. Pilot 输出建议结构

```yaml
ato_batch_real_case_pilot_output:
  pilot_summary:
  input_quality_check:
  per_case_evidence_cards:
  batch_pattern_summary:
  source_coverage_summary:
  missing_evidence_summary:
  candidate_strategy_direction:
  manual_review_boundary:
  next_actions:
```

## 10. 下一步建议

pilot 通过后可进入：

- 5-20 cases 的标准 batch contract 验证。
- DataAgent / Hive 离线 query plan 评审。
- 策略候选规则卡评审。
- 人工复核样本池建设。

pilot 不通过时：

- 优先修 input contract、source metadata 或 evidence card 模板。
- 不扩大到更多 case。
- 不进入策略方向沉淀。
