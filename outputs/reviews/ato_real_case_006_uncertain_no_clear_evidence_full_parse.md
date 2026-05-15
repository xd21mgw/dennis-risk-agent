# ATO Real Case 006 Uncertain No Clear Evidence Full Parse

## 0. Case 基本信息

- case_id: `ATO_CASE_006_UNCERTAIN_NO_CLEAR_EVIDENCE`
- user_id: `5224005946`
- 时间窗口: `2026-04-20 ~ 2026-04-24`
- 业务场景: 盗号申诉 / 证据不足样本
- 试点阶段: v2.4 Data Agent-only 只读试点
- 当前输入类型: 4 组 SQL 完整执行结果聚合摘要
- 当前解析边界: Data Agent-only evidence ready，但结论为证据不足

本轮仅基于用户粘贴的 Data Agent 聚合摘要解析，不调用 Data Agent，不补造未返回数据，不把用户申诉当作事实，不因为申诉称被盗就强判 ATO。

## 1. 当前状态识别

```yaml
status: success
execution_state: execution_result_ready
returned_type: full_sql_execution_aggregate_summary
evidence_ready: true
manual_review_required: true
```

为什么可以进入 evidence 解析：

- 登录/授权全景、设备 IP 汇总、安全事件、发布行为均为 success。
- 已有聚合摘要可用于判断证据强弱、反证、缺失证据和质量风险。
- 但该 case 的 evidence 解析结果不是支持 ATO，而是证据不足。

## 2. 每个 SQL / 查询模块状态和摘要

| 模块 | SQL ID | 状态 | 行数 | 权限 / 字段移除 | 摘要 |
|---|---:|---|---:|---|---|
| 登录/授权全景 | `75020` | success | 1 | 无 | 时间窗口内没有登录记录，只有 1 次密码重置；历史设备 iPhone 14，广东 |
| 设备 IP 汇总 | `75025` | success | 1 | 无 | 密码重置设备为历史设备，活跃 122 天；地区广东 |
| 安全事件 | `75021` | success | 16 | `params` P4 移除 | 1 次密码重置、3 次账号找回、12 次注销尝试；仅高价值账号验证，无盗号标签 |
| 发布行为 | `75015` | success | 5 | `upload_timestamp`、`caption` 无权限 | 04-20~04-21 发布 5 个作品，浙江杭州/宁波，设备 iPhone 17 + iPhone 13 |
| 链路结果 | 聚合链路 | success | 聚合 | 受权限限制 | 密码重置后 4 分钟出现新设备找回；广东重置与浙江发布地区不一致，但缺异常登录链路 |

## 3. data_findings

```yaml
data_findings:
  - 时间窗口内没有登录记录，只有 1 次密码重置。
  - 密码重置使用历史设备 iPhone 14，活跃 122 天。
  - 密码重置地区为广东。
  - 密码重置后 4 分钟出现新设备账号找回 3 次。
  - 2026-04-20 ~ 2026-04-21 有 5 个作品发布。
  - 发布地区为浙江杭州 / 浙江宁波。
  - 发布设备包括 iPhone 17 和 iPhone 13。
  - 广东密码重置与浙江发布存在地区不一致。
  - 2026-04-22 ~ 2026-04-24 有 12 次注销尝试，设备/IP为空。
  - 风控未命中盗号、钓鱼、扫码、短信泄露、密码泄露标签。
  - 无 OAuth / 扫码授权记录。
  - 无换绑 / 改密记录。
```

## 4. speculation_notes

```yaml
speculation_notes:
  - “可能用户跨省移动”是推测。
  - “新设备找回可能是用户本人另一台设备”是推测。
  - “注销尝试可能是用户本人”是推测。
  - “用户申诉称异地登录”不是数据事实。
```

## 5. strong_evidence

```yaml
strong_evidence: []
```

说明：

- 当前没有足够强证据支持 ATO。
- 没有异常登录记录。
- 没有 OAuth / 扫码授权。
- 没有 token/session 接管证据。
- 没有盗号 / 钓鱼 / 密码泄露 / 短信泄露标签。
- 发布行为存在，但缺异常登录或登录态接管链路闭合。

## 6. medium_evidence

以下只能作为中等疑点，不能升级为强证据。

```yaml
medium_evidence:
  - evidence: 密码重置后 4 分钟出现新设备账号找回 3 次。
    supports: 账号安全链路存在异常节奏。
    limitation: 新设备可能是用户本人另一台设备，params 被移除，设备详情不足。
  - evidence: 广东密码重置后浙江发布。
    supports: 地区不一致疑点。
    limitation: 可能是用户跨省移动，缺真实移动轨迹和登录链路。
  - evidence: 12 次注销尝试主体不明。
    supports: 异常账号操作疑点。
    limitation: 设备/IP 为空，无法判断是否本人或系统/流程行为。
  - evidence: 5 个作品发布但内容不可见。
    supports: 下游行为存在。
    limitation: caption 无权限，无法验证内容是否违规，也缺异常登录链路。
```

## 7. weak_evidence

```yaml
weak_evidence:
  - 用户申诉文本，仅作背景。
  - 发布行为存在但缺异常登录链路。
  - 地区不一致但可能有正常解释。
```

## 8. counter_evidence

```yaml
counter_evidence:
  - counter_item: 没有登录记录，无法验证异地登录。
    impact: 不支持申诉中的“异地登录”数据事实。
    whether_closed: partially_closed
  - counter_item: 密码重置使用历史设备。
    impact: 支持本人操作或至少常用设备操作的可能性。
    whether_closed: partially_closed
  - counter_item: 无 OAuth / 扫码授权。
    impact: 不支持扫码/OAuth 型接管。
    whether_closed: closed_for_current_window
  - counter_item: 无盗号 / 钓鱼 / 密码泄露 / 短信泄露标签。
    impact: 不支持明确 ATO 标签定性。
    whether_closed: partially_closed
  - counter_item: 无 token/session 接管证据。
    impact: 不支持登录态被接管路径。
    whether_closed: partially_closed
  - counter_item: 无换绑 / 改密。
    impact: 不支持账号绑定或资料关键变更链路。
    whether_closed: partially_closed
  - counter_item: 疑点均存在正常行为解释。
    impact: 不能排除本人新设备、跨省移动、本人注销或找回操作。
    whether_closed: not_closed
```

## 9. missing_evidence

```yaml
missing_evidence:
  - 实时登录链路。
  - 实时设备指纹。
  - token/session 生命周期。
  - 账号找回设备详情，因 params 移除不可见。
  - 注销操作主体，因设备/IP为空不可确认。
  - 作品内容 / caption 缺失，无法验证内容是否违规。
  - 用户真实地理移动轨迹不可见。
  - 离线表无登录记录的原因不可确认。
```

## 10. permission_notes

```yaml
permission_notes:
  - params(P4) 被移除。
  - upload_timestamp 无权限。
  - caption 无权限。
```

## 11. quality_risks

```yaml
quality_risks:
  - 申诉称异地登录，但离线表无登录记录，可能是申诉不准确、时间窗口不对、实时日志未同步或离线表覆盖不足。
  - 不能把无登录记录解释为没有登录。
  - 广东到浙江的地区差异不能直接等于盗号。
  - 新设备找回可能是本人设备，需更多设备指纹或人工复核。
  - 注销尝试设备/IP为空，主体不明。
  - 作品内容是否违规无法通过当前返回验证。
  - Data Agent-only 为离线取证，不能覆盖实时登录链路和完整 token/session 生命周期。
```

## 12. provider_limitations

```yaml
provider_limitations:
  - Data Agent-only 只能做离线 / Hive 取证。
  - 实时登录链路、设备指纹、token/session、在线关系图谱无法充分覆盖。
  - provider_conclusion_hint 不等于最终人工定性。
  - 离线表没有登录记录不等于实时系统没有登录记录。
```

## 13. conclusion_support

```yaml
conclusion_support:
  level: insufficient_support
  reason: >
    当前无法构建异常登录 → 账号接管 → 发布违规的证据链；
    存在密码重置后新设备找回、广东到浙江发布、注销尝试等疑点，
    但关键 ATO 证据缺失，且疑点可被正常行为解释。
  boundary: >
    不能强判 ATO，也不能反向断言无风险。
provider_conclusion_hint: 证据不足
```

## 14. recommended_next_provider

```yaml
recommended_next_provider:
  generated_by: router_or_dennis_agent
  providers:
    - provider: manual_review_provider
      purpose: 核对用户申诉时间、账号归属、设备归属。
    - provider: realtime_log_provider
      purpose: 补真实登录链路和实时请求。
    - provider: device_fingerprint_provider
      purpose: 验证 iPhone17 / iPhone13 / 新设备找回是否为本人设备。
    - provider: risk_engine_provider
      purpose: 查看完整策略 params 和决策流。
    - provider: content_review_provider
      purpose: 验证 5 个作品内容是否违规。
    - provider: account_recovery_provider
      purpose: 核查账号找回操作详情。
```

## 15. manual_review_required

```yaml
manual_review_required: true
reason:
  - 当前是证据不足样本，不是 ATO 正例。
  - 仍存在中等疑点，需要人工复核申诉时间、设备归属和发布内容。
  - 离线表无登录记录的原因需要确认。
  - 不能把无登录记录当无风险。
```

## 16. Dennis Agent 解释

### 当前最多能下什么结论

```text
证据不足。当前数据无法支持明确 ATO，也不能反向排除全部风险。
```

### 为什么不能判 ATO

- 没有异常登录记录。
- 没有 OAuth / 扫码授权。
- 没有 token/session 接管证据。
- 没有盗号 / 钓鱼 / 密码泄露 / 短信泄露标签。
- 发布行为存在，但缺异常登录 → 登录态接管 → 发布的闭合链路。
- 密码重置使用历史设备，存在本人操作解释。

### 为什么也不能判“无风险”

- 离线表无登录记录不等于实时系统无登录。
- 密码重置后 4 分钟出现新设备找回，有异常节奏。
- 广东密码重置后浙江发布，存在地区不一致。
- 12 次注销尝试设备/IP为空，主体不明。
- caption 和 params 缺失，关键解释信息不足。

### 为什么 Case 006 是反例 / 证据不足样本

Case 001 和 Case 003 都能闭合“异常登录/授权 → 接管 → 发布”链路；Case 006 只能看到账号安全操作和发布行为的并列存在，无法证明接管链路，也存在多个正常解释路径。

### 它对 ATO Skill 的回归价值

- 验证不因用户申诉强判盗号。
- 验证不把无登录记录解释为无风险。
- 验证中等疑点与强证据的边界。
- 验证 Data Agent-only 离线缺口下的降级能力。
- 验证人工复核和后续 provider 的必要性。

### 是否可以关闭 Case 006

可以作为 Data Agent-only ATO 反例 / 证据不足样例关闭，但不能关闭为“无风险”或“最终非盗号”。

### 是否可以进入 ATO coverage review

可以。Case 001、Case 003、Case 006 已覆盖密码登录型正例、扫码/OAuth 型正例、证据不足反例，具备做 ATO coverage review 的基础。

## 17. 与人工备注 / 标签是否一致

人工标签：

```yaml
manual_label: 否
manual_note: 无明确回扫/细分类备注
```

判断：

```yaml
manual_label_consistency:
  supports_manual_label_no_or_insufficient:
    supported_by_data: true
    reason: 缺异常登录、缺 token/session 接管、缺盗号标签，整体证据不足。
  new_strong_ato_evidence_found:
    found: false
    reason: 没有发现能闭合 ATO 链路的强证据。
  needs_human_review:
    needed: true
    reason: 存在密码重置后新设备找回、广东到浙江发布、注销尝试主体不明等中等疑点。
```

## 18. 是否可以关闭 Case 006

```yaml
can_close_case_006_as_dataagent_only_negative_or_insufficient_sample: true
close_as: Data Agent-only ATO 反例 / 证据不足样例
cannot_close_as:
  - 最终无风险。
  - 最终非盗号人工定性。
  - 明确 ATO。
  - 已排除所有风险。
close_condition:
  - 所有 SQL 均已返回聚合摘要。
  - 强证据为空。
  - 中等疑点、反证、缺失证据、质量风险已记录。
  - 保留人工复核入口。
```

## 19. 是否可以进入 ATO coverage review

```yaml
can_enter_ato_coverage_review: true
basis:
  - Case 001: 密码登录 / 非历史设备 / 发布链路正例。
  - Case 003: 扫码/OAuth / Web 新设备 / Token / 发布链路正例。
  - Case 006: 证据不足 / 反例 / 不强判样本。
coverage_value:
  - 验证强证据闭合。
  - 验证 provider limitation 下的降级。
  - 验证反证和正常解释。
  - 验证人工复核边界。
```

## 20. 是否需要回写

```yaml
backwrite_assessment:
  dataagent_markdown_response_parser_v1.md:
    needed: no
    reason: 现有 execution_result_ready、insufficient_support、quality_risks、provider_limitations 规则够用。
  dataagent_sql_execution_followup_template_v1.md:
    needed: no
    reason: SQL 执行状态与聚合摘要模板覆盖本 case。
  ato_expected_evidence_and_boundaries_v1.md:
    needed: optional
    reason: 可选补充“无登录记录不能当无风险”的 ATO 反例规则，但当前已有边界可支持。
  ato_dataagent_question_templates_v1.md:
    needed: no
    reason: 问题模板已支持反例取证。
  account_security_expert_skill.md:
    needed: no
    reason: 不修改核心 Skill；本轮为试点回归沉淀。
```

## 21. 自评

```yaml
self_score: 92
reason:
  - 明确识别为证据不足样本。
  - 没有因申诉强判 ATO。
  - 没有把无登录记录解释为无风险。
  - 区分了数据发现、推测、反证、缺失证据和质量风险。
  - 保留人工复核和后续 provider 边界。
```
