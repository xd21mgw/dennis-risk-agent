# ATO Real Case 001 Full Execution Parse

## 0. Case 基本信息

- case_id: `ATO_CASE_001_PASSWORD_KPN_RESWEEP`
- 试点阶段: v2.4 Data Agent-only 只读试点
- 触发 Skill: `account_security_expert_skill`
- 当前输入类型: 5 组 SQL 完整执行结果聚合摘要
- 当前解析边界: Data Agent-only evidence ready，不是最终人工定性

本轮仅基于用户粘贴的 Data Agent 聚合摘要解析，不调用 Data Agent，不补造未返回数据，不把用户申诉或人工备注当作事实。

## 1. 当前状态识别

```yaml
status: success
execution_state: execution_result_ready
returned_type: full_sql_execution_aggregate_summary
evidence_ready: true
manual_review_required: true
```

为什么不再是 `partial_execution_result_ready`：

- 74733 换绑、74734 登录全景、74735 发布行为、74736 账号安全事件、74737 登录发布链路均已返回执行状态和聚合摘要。
- 74735 / 74737 已返回结果，发布行为和登录发布链路可以纳入 evidence。
- 仍存在字段权限限制，但这属于 `permission_notes` 和 `quality_risks`，不再阻断进入 evidence 阶段。

## 2. 每个 SQL ID 的状态和摘要

| SQL ID | 查询目的 | 状态 | 聚合摘要 | 证据使用方式 |
|---|---|---|---|---|
| `74733` | 换绑 | success, 0 行 | 无换绑记录；同步视为无改密、无找回记录的反证侧发现 | 可作为“未发现敏感账号资料变更”的反证 |
| `74734` | 登录全景 | success, 2 行 | 4 次登录均为密码登录；APP 非历史设备；11 小时内 APP → Web，多设备多 IP；风险 did 标记和异常登录相关风控命中 | 可进入强/中 evidence |
| `74735` | 发布行为 | success, 2 行 | 异常登录后有 2 条作品发布；内容和精确时间受字段权限限制 | 可进入强 evidence，但内容违规细节缺失 |
| `74736` | 账号安全事件 | success, 2 行 | 存在账号安全监控、风险城市新设备、异常登录通知、高异常记录；存在 USER_SET_RISK_LEVEL_SHUFFULE 和 SEND_AQUILA_PUNISH；`params` 被移除 | 可进入中/强 evidence，但策略原因明细受限 |
| `74737` | 登录发布链路 | success, 2 行 | 发布设备与 Web 登录设备一致；发布设备与 APP 登录设备不一致；发布 IP / 地区与登录 IP / 地区不一致 | 可进入强 evidence |

## 3. data_findings

```yaml
data_findings:
  - 4 次登录均为密码登录，0 次微信 / 验证码 / 扫码。
  - APP 设备为非历史环境，did_active_day=0。
  - 11 小时内 APP → Web，2 设备 + 2 IP。
  - 风控命中账号安全监控、风险城市新设备、异常登录通知、通用高异常记录。
  - 存在 USER_SET_RISK_LEVEL_SHUFFULE 和 SEND_AQUILA_PUNISH。
  - risk_did_login_loose=true，risk_did_login_strict=true。
  - 异常登录后有 2 条作品发布。
  - 发布设备与 Web 登录设备一致。
  - 发布设备与 APP 登录设备不一致。
  - 发布 IP / 地区与登录 IP / 地区不一致。
  - 无换绑、无改密、无找回。
```

## 4. speculation_notes

```yaml
speculation_notes:
  - “可能密码泄露”是推测；数据支持密码登录和异常登录链路，但未直接命中“密码泄露”标签。
  - “可能账号被接管”是推测；数据支持账号接管嫌疑，但最终仍需人工复核。
  - “人工备注已回扫”不是数据发现；离线表未直接验证回扫标签。
```

## 5. strong_evidence

```yaml
strong_evidence:
  - evidence: 异常登录后存在 2 条作品发布，登录后发布行为链路成立。
    supports: 异常登录后下游敏感动作链路。
    limitation: 作品精确时间戳和内容字段受权限限制。
  - evidence: 发布设备与 Web 登录设备一致。
    supports: Web 登录与发布动作之间存在设备链路。
    limitation: 仍需人工复核 Web 登录是否为异常接管环境。
  - evidence: 4 次登录均为密码登录，0 次微信 / 验证码 / 扫码。
    supports: 与用户声称平常微信/验证码登录存在冲突方向。
    limitation: 用户申诉不是事实；还需要历史长期登录基线支持。
  - evidence: APP 非历史设备，did_active_day=0，且 risk_did_login_loose/strict 均为 true。
    supports: 非历史设备 + 风险设备登录信号。
    limitation: did_active_day 是设备维度，不能和城市活跃天数混用。
  - evidence: 风控命中账号安全监控、风险城市新设备、异常登录通知、通用高异常记录。
    supports: 账号安全风险链路。
    limitation: 策略命中不等于风险事实，且 params 明细缺失。
  - evidence: 发布设备与 APP 登录设备不一致，发布 IP / 地区与登录 IP / 地区不一致。
    supports: 登录后发布行为跨设备 / 跨地区异常。
    limitation: 需要人工解释 APP → Web 切换是否存在正常业务场景。
```

## 6. medium_evidence

```yaml
medium_evidence:
  - evidence: 11 小时内 APP → Web，2 设备 + 2 IP。
    supports: 短时间多设备多 IP 切换。
    limitation: 多端切换本身不必然等于 ATO。
  - evidence: 风控策略命中，但 params 高敏字段被移除。
    supports: 风险事件存在。
    limitation: 缺完整策略决策流明细。
  - evidence: APP 登录设备与发布设备不一致。
    supports: 下游发布与早前 APP 登录环境不一致。
    limitation: Web 登录设备与发布设备一致，需解释 Web 登录是否异常。
  - evidence: 发布 IP / 地区与登录环境不一致。
    supports: 发布动作环境异常。
    limitation: 缺精确发布时间和更细粒度链路。
```

## 7. weak_evidence

```yaml
weak_evidence:
  - 用户申诉文本，仅作背景，不作为事实证据。
  - 人工备注“电商 kpn 站点密码盗号，已回扫”，仅作 golden hint。
  - “已回扫”但离线表无验证字段，不能作为数据事实。
  - 内容违规原因无法验证，因为 caption / 内容字段无权限。
```

## 8. counter_evidence

```yaml
counter_evidence:
  - counter_item: APP 登录 IP 地区 = 注册地。
    impact: 不支持 APP 登录异地。
    whether_closed: partially_closed
  - counter_item: 无换绑、无改密、无找回。
    impact: 不支持通过账号绑定/资料关键变更证明控制权转移。
    whether_closed: partially_closed
  - counter_item: 无直接“盗号 / 密码泄露 / 钓鱼 / 短信泄露”标签。
    impact: 不能把链路证据直接等同标签命中。
    whether_closed: partially_closed
  - counter_item: 可见范围内无 token/session 复用或劫持线索。
    impact: 暂不支持 token/session 被盗路径。
    whether_closed: partially_closed
```

## 9. missing_evidence

```yaml
missing_evidence:
  - 作品精确时间戳缺失。
  - 作品内容 / caption 缺失，无法验证内容是否违规。
  - params 高敏字段移除，策略决策流明细不可见。
  - token/session 劫持需要实时系统或在线图谱。
  - 前端 SDK / 协议攻击排查超出 Data Agent 能力。
  - 回扫记录离线表未验证。
  - 电商 kpn 站点来源未被当前聚合摘要验证。
```

## 10. permission_notes

```yaml
permission_notes:
  - upload_timestamp 无权限。
  - caption 无权限。
  - delete_user_id 无权限。
  - params 高敏字段被移除。
```

## 11. quality_risks

```yaml
quality_risks:
  - 发布时间只能按日期估算，无法精确到秒级或分钟级。
  - 内容是否违规无法通过当前返回验证。
  - 04-16 / 04-18 登录记录缺失可能是真无，也可能有数据分区 / 日志覆盖问题。
  - did_active_day=0 与城市活跃 999 天存在口径差异：前者是设备维度，后者是城市维度，不能混用。
  - 策略命中不等于风险事实，需要结合后验链路和人工复核。
  - Data Agent-only 为离线聚合，不能覆盖实时登录链路、实时设备指纹、在线 token/session 图谱。
```

## 12. provider_limitations

```yaml
provider_limitations:
  - Data Agent-only 只能做离线 / Hive 取证。
  - 实时登录链路、实时设备指纹、token/session、在线关系图谱无法充分覆盖。
  - Data Agent 输出 provider_conclusion_hint，不替代最终人工判定。
  - 内容审核结论和内容违规细节不由当前 Data Agent 聚合摘要直接证明。
```

## 13. conclusion_support

```yaml
conclusion_support:
  level: data_supports_ato_suspicion
  reason: >
    异常登录 + 非历史设备 + 密码登录 + 风控命中 + 异常登录后发布行为 + 发布设备与 Web 登录设备一致，
    核心链路在数据层面已闭合，支持 ATO / 账号接管嫌疑。
  boundary: >
    不能直接等同最终盗号定性；内容违规细节、作品精确时间、完整策略 params、
    token/session 实时链路和电商 kpn 来源仍缺失。
provider_conclusion_hint: 数据支持盗号嫌疑
```

## 14. recommended_next_provider

```yaml
recommended_next_provider:
  generated_by: router_or_dennis_agent
  providers:
    - provider: manual_review_provider
      purpose: 人工复核内容违规、申诉与数据一致性、最终 case 标签。
    - provider: realtime_log_provider
      purpose: 如需进一步验证 token/session、实时登录链路。
    - provider: device_fingerprint_provider
      purpose: 如需确认实时设备指纹和包环境。
    - provider: risk_engine_provider
      purpose: 如需查看完整策略决策流 params。
    - provider: content_review_provider
      purpose: 如需验证发布内容是否确为违规内容。
```

## 15. manual_review_required

```yaml
manual_review_required: true
reason:
  - Data Agent-only 输出不能替代最终人工定性。
  - caption / 内容字段无权限，内容违规细节需人工或内容审核侧确认。
  - params 高敏字段被移除，策略决策流需进一步解释。
  - 人工备注中的“已回扫”和“电商 kpn 站点来源”未被当前数据发现验证。
```

## 16. Dennis Agent 解释

### 当前最多能下什么结论

```text
数据层支持 ATO / 账号接管嫌疑，且强于 partial 阶段；但仍不能直接等同最终人工盗号定性。
```

### 为什么比 partial 阶段更强

- 74735 发布行为已返回结果，确认异常登录后有 2 条作品发布。
- 74737 登录发布链路已返回结果，确认发布设备与 Web 登录设备一致。
- 登录侧、风险事件侧、发布侧、登录发布链路侧都已有聚合摘要，核心链路从“登录异常”推进到“异常登录后下游发布”。

### 为什么仍不能直接等同最终人工定性

- 作品精确时间戳缺失，发布时间只能按日期估算。
- caption / 内容字段无权限，无法验证内容是否违规。
- 策略 params 被移除，策略决策原因不可见。
- token/session 实时链路和在线图谱不在 Data Agent-only 覆盖范围内。
- 人工备注“已回扫”和“电商 kpn 站点来源”未被当前离线表验证。

### 哪些证据支持人工备注

人工备注：“电商kpn站点密码盗号，已回扫”。

支持“密码盗号嫌疑”的数据：

- 4 次登录均为密码登录，0 次微信 / 验证码 / 扫码。
- APP 非历史设备，did_active_day=0。
- 风控命中账号安全监控、风险城市新设备、异常登录通知、通用高异常记录。
- risk_did_login_loose=true，risk_did_login_strict=true。
- 异常登录后有 2 条作品发布，发布设备与 Web 登录设备一致。

### 哪些证据未能验证人工备注

- 未直接命中“盗号 / 密码泄露 / 钓鱼 / 短信泄露”标签。
- 离线表未验证“已回扫”。
- 当前聚合摘要未验证“电商 kpn 站点来源”。
- 内容违规原因未验证。

### 是否建议关闭 Case 001

建议可以作为 Data Agent-only ATO 试点闭环成功样例关闭，但不是作为“最终人工盗号定性”关闭。

关闭条件：

- 关闭口径限定为：Data Agent-only 试点已完成从 SQL-only → SQL execution → full execution evidence → Dennis evidence interpretation 的闭环。
- 结论限定为：数据层支持 ATO / 账号接管嫌疑。
- 后续人工定性、内容违规确认、策略明细解释不在本轮 Data Agent-only 闭环内。

### 是否可以进入 Case 003

可以进入 `ATO_CASE_003_QR_SCAN_GROUND_PROMO_RESWEEP`。

原因：

- Case 001 已跑通完整执行链路。
- parser 已能处理 full execution aggregate summary。
- Case 003 可测试扫码 / OAuth / token / 异地链路，与 Case 001 的密码登录路径互补。

## 17. 与人工备注 / 标签是否一致

人工备注：`电商kpn站点密码盗号，已回扫`

```yaml
manual_note_consistency:
  password_takeover_suspicion:
    supported_by_data: true
    reason: 密码登录、非历史设备、风险登录标记、异常登录后发布行为、发布设备与 Web 登录设备一致。
  resweep:
    verified_by_data: false
    reason: 离线表未直接命中“回扫”标签或可验证回扫链路。
  ecommerce_kpn_source:
    verified_by_data: false
    reason: 当前聚合摘要未返回电商 kpn 站点来源证据。
```

人工备注只能作为 golden hint，不得当作数据事实。

## 18. 是否可以关闭 Case 001

```yaml
can_close_case_001_as_dataagent_only_pilot: true
can_close_as_final_manual_ato_judgement: false
close_condition:
  - 5 组 SQL 均返回聚合摘要。
  - 登录、风险事件、发布行为、登录发布链路均可进入 evidence。
  - Dennis Agent 已输出数据层 evidence judgement。
  - 权限限制、质量风险、未验证人工备注均已记录。
remaining_gaps:
  - 内容违规细节。
  - 完整策略 params。
  - token/session 实时链路。
  - 回扫记录。
  - 电商 kpn 来源。
```

## 19. 是否可以进入 Case 003

```yaml
can_enter_case_003: true
next_case: ATO_CASE_003_QR_SCAN_GROUND_PROMO_RESWEEP
reason: >
  Case 001 已完成 Data Agent-only 闭环，Case 003 可用于验证扫码 / OAuth / token / 异地链路。
```

## 20. 是否需要回写

```yaml
backwrite_assessment:
  dataagent_markdown_response_parser_v1.md:
    needed: no
    reason: 现有 execution_result_ready / evidence_ready、permission_notes、quality_risks 规则够用。
  dataagent_sql_execution_followup_template_v1.md:
    needed: optional
    reason: 可选补充 full execution aggregate summary 的标准输出示例，但不是阻塞。
  ato_expected_evidence_and_boundaries_v1.md:
    needed: no
    reason: 强/中/弱证据和边界规则覆盖本 case。
  ato_dataagent_question_templates_v1.md:
    needed: no
    reason: 问题模板已支持 ATO 取数闭环。
```

## 21. 自评

```yaml
self_score: 91
reason:
  - 区分了数据发现、推测、权限限制和质量风险。
  - 没有把申诉和人工备注当事实。
  - 纳入了发布行为和登录发布链路。
  - 给出 Data Agent-only 成功闭环与最终人工定性的边界。
  - 未输出处罚、冻结、封禁、扣除或策略上线建议。
```
