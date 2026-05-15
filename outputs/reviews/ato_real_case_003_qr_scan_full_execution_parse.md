# ATO Real Case 003 QR Scan Full Execution Parse

## 0. Case 基本信息

- case_id: `ATO_CASE_003_QR_SCAN_GROUND_PROMO_RESWEEP`
- user_id: `2861890219`
- 时间窗口: `2026-04-18 00:00 ~ 2026-04-20 23:59`
- 试点阶段: v2.4 Data Agent-only 只读试点
- 触发 Skill: `account_security_expert_skill`
- 当前输入类型: 4 组 SQL 完整执行结果 + 登录-授权-发布链路聚合摘要
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

- 登录/授权全景、安全事件、设备 IP 汇总、发布行为均为 success。
- 发布行为已返回 5 行聚合结果，登录-授权-发布链路已能闭合到设备、IP、地区和时间差层面。
- 仍存在 `upload_timestamp`、`caption`、`params` 等权限限制，但这些进入 `permission_notes` 和 `quality_risks`，不阻断 evidence 阶段。

## 2. 每个 SQL / 查询模块状态和摘要

| 模块 | SQL ID | 状态 | 行数 | 权限 / 字段移除 | 摘要 |
|---|---:|---|---:|---|---|
| 登录/授权全景 | `74853` | success | 18 | 无 | 9 次 OAuth 授权 + 4 次扫码相关登录；04-19 13:20-13:23 四分钟内集中 15 次行为；3 个设备，含 2 个 Web 新设备 |
| 安全事件 | `74851` | success | 18 | `params` P4 高敏移除 | 策略名包含 `stealAccount`；命中扫码/Web 登录欺诈相关策略；策略决策流明细不可见 |
| 设备 IP 汇总 | `74860` | success | 12 | 无 | 登录 100% 河南濮阳；多设备、多 IP；发布为山东青岛 |
| 发布行为 | `74854` | success | 5 | `upload_timestamp`、`caption` 无权限 | 04-20 5 个作品，Web 新设备2发布，山东青岛，当天全部删除 |
| 登录-授权-发布链路 | 聚合链路 | success | 2 | 受发布字段权限限制 | OAuth/扫码 → Web 新设备登录 → Token 生成 → 跨省发布 → 当天删除链路成立 |

## 3. data_findings

```yaml
data_findings:
  - 9 次 OAuth 授权 + 4 次扫码相关登录。
  - 2026-04-19 13:20-13:23 四分钟内集中发生 15 次行为。
  - 2 个 Web 新设备首次出现，活跃天数为 0。
  - Web 新设备获得 Token。
  - login_type 包含 OAuth 授权和扫码相关行为。
  - 策略名明确包含 stealAccount。
  - 命中 stealAccount_qrLogin_accept_teen_alert。
  - 命中 stealAccount_web_qrlogin_nohis_tag。
  - 命中 webLogin_fraud_login_monitor_1_onlyFuxin。
  - 2026-04-20 出现 5 个作品发布。
  - 作品发布设备与 Web 新设备2一致。
  - 发布 IP / 地区为山东青岛，与登录河南濮阳跨省不一致。
  - 5 个作品当天全部删除。
  - 2026-04-20 出现 3 次密码重置尝试且被风控拦截。
  - 无换绑、无改密、无找回记录。
```

## 4. speculation_notes

```yaml
speculation_notes:
  - “地推扫码欺诈”是基于批量扫码、风控策略、人工备注形成的推测，不是直接数据事实。
  - “山东德州是攻击者来源”未被数据验证，数据中是山东青岛。
  - “已回扫”不是数据发现；离线表未验证回扫记录。
```

## 5. strong_evidence

```yaml
strong_evidence:
  - evidence: OAuth 授权 → Web 新设备登录 → Token 生成 → 登录态接管链路成立。
    supports: 扫码/OAuth 型账号接管核心入口链路。
    limitation: 实时扫码二维码内容和完整 token 生命周期仍不可见。
  - evidence: 2 个 Web 新设备首次出现，活跃天数为 0。
    supports: 新设备接管风险。
    limitation: 需要设备指纹侧进一步确认设备环境。
  - evidence: 策略名直接包含 stealAccount。
    supports: 数据层明确盗号风险标记。
    limitation: params P4 被移除，决策流明细不可见。
  - evidence: 命中 stealAccount_qrLogin_accept_teen_alert、stealAccount_web_qrlogin_nohis_tag、webLogin_fraud_login_monitor_1_onlyFuxin。
    supports: 扫码/Web 登录盗号与欺诈监控链路。
    limitation: 策略命中仍需人工解释和后验复核。
  - evidence: 登录态接管后 2026-04-20 发生 5 个作品发布。
    supports: 接管后下游敏感动作。
    limitation: upload_timestamp 和 caption 无权限，精确时间和内容不可验证。
  - evidence: 发布设备与 Web 新设备2一致。
    supports: Web 新设备2从登录态接管延伸到发布动作。
    limitation: 仍需内容审核确认作品性质。
  - evidence: 5 个作品当天全部删除。
    supports: 批量发布后快速删除的异常行为。
    limitation: 删除原因和操作者字段受限。
  - evidence: 登录河南濮阳，发布山东青岛，跨省异地操作。
    supports: 接管后跨省发布环境异常。
    limitation: 登录阶段本身不异地，因为河南濮阳等于注册地。
```

## 6. medium_evidence

```yaml
medium_evidence:
  - evidence: 4 分钟内多次 OAuth / 扫码相关行为。
    supports: 批量扫码 / 授权异常节奏。
    limitation: 不能单独证明地推场景。
  - evidence: 多设备、多 IP、多个 token。
    supports: 多环境接管和扩散风险。
    limitation: 仍需实时 token 生命周期验证。
  - evidence: 2026-04-20 密码重置尝试 3 次且被拦截。
    supports: 用户事后找回 / 异常后补救线索。
    limitation: 用户意图需结合申诉和人工复核确认。
  - evidence: 登录地区河南濮阳与人工备注部分吻合。
    supports: 人工备注中的河南濮阳线索。
    limitation: 不支持登录阶段异地。
```

## 7. weak_evidence

```yaml
weak_evidence:
  - 用户申诉称不知情，仅作背景。
  - 人工备注“扫码地推 / 已回扫”，仅作 golden hint。
  - 山东德州线索未被数据验证，只能作为弱证据或未验证线索。
```

## 8. counter_evidence

```yaml
counter_evidence:
  - counter_item: 登录地区 100% 河南濮阳，与注册地一致。
    impact: 不支持登录阶段异地。
    whether_closed: partially_closed
  - counter_item: 无换绑、无改密、无找回。
    impact: 不支持通过账号绑定/资料关键变更证明控制权转移。
    whether_closed: partially_closed
  - counter_item: 山东德州线索未命中，实际为山东青岛。
    impact: 人工情报城市精确度存在偏差。
    whether_closed: partially_closed
  - counter_item: 回扫记录未被离线表验证。
    impact: “已回扫”不能作为数据事实。
    whether_closed: not_closed
```

## 9. missing_evidence

```yaml
missing_evidence:
  - 作品精确时间戳缺失。
  - 作品内容 / caption 缺失，无法验证内容是否违规。
  - params P4 移除，策略决策流明细不可见。
  - 扫码二维码内容和实时扫码流程日志不可见。
  - 回扫记录离线表未验证。
  - token/session 的实时生命周期仍需在线系统进一步验证。
  - kuaishou.server.webday7 来源未被当前摘要直接验证。
```

## 10. permission_notes

```yaml
permission_notes:
  - upload_timestamp 无权限。
  - caption 无权限。
  - params P4 高敏字段被移除。
```

## 11. quality_risks

```yaml
quality_risks:
  - 作品内容是否违规无法验证。
  - 山东德州与山东青岛城市不一致，人工情报精确度存在偏差。
  - 安全事件表与登录全景表存在重复，增量信息有限。
  - 2026-04-18 无登录记录，可能真无或有分区 / 数据覆盖问题。
  - 策略命中不等于最终人工定性。
  - Data Agent-only 为离线取证，无法覆盖实时扫码流程和完整 token 生命周期。
```

## 12. provider_limitations

```yaml
provider_limitations:
  - Data Agent-only 只能做离线 / Hive 取证。
  - 实时扫码流程、二维码内容、token/session 生命周期、在线关系图谱无法充分覆盖。
  - provider_conclusion_hint 不等于最终人工定性。
  - 内容审核结论和作品违规细节不由当前 Data Agent 聚合摘要直接证明。
```

## 13. conclusion_support

```yaml
conclusion_support:
  level: data_supports_ato_suspicion
  reason: >
    扫码/OAuth授权、新 Web 设备、Token 生成、stealAccount 策略命中、
    发布设备一致、发布行为闭环、批量发布后删除，共同支持扫码/OAuth 型账号接管嫌疑。
  boundary: >
    不直接等同最终人工定性；作品内容、回扫记录、实时扫码流程、
    token/session 生命周期和山东德州线索仍缺失或未验证。
provider_conclusion_hint: 数据支持盗号嫌疑（扫码欺诈 / OAuth 型账号接管）
```

## 14. recommended_next_provider

```yaml
recommended_next_provider:
  generated_by: router_or_dennis_agent
  providers:
    - provider: manual_review_provider
      purpose: 人工复核内容违规、申诉与数据一致性。
    - provider: risk_engine_provider
      purpose: 查看完整策略 params 和决策流。
    - provider: realtime_log_provider
      purpose: 验证实时扫码流程和 token/session 生命周期。
    - provider: device_fingerprint_provider
      purpose: 确认 Web 新设备和设备指纹风险。
    - provider: content_review_provider
      purpose: 验证 5 个作品内容是否确为违规。
    - provider: relation_graph_provider
      purpose: 如需进一步验证地推 / 团伙扩散。
```

## 15. manual_review_required

```yaml
manual_review_required: true
reason:
  - Data Agent-only 输出不能替代最终人工定性。
  - caption / 内容字段无权限，作品违规细节需人工或内容审核侧确认。
  - params P4 被移除，策略决策流需进一步解释。
  - 人工备注“山东德州”“已回扫”“kuaishou.server.webday7”未被当前数据完全验证。
```

## 16. Dennis Agent 解释

### 当前最多能下什么结论

```text
数据层支持扫码/OAuth 型 ATO / 账号接管嫌疑，且核心链路较完整；但仍不能直接等同最终人工盗号定性。
```

### 为什么 Case 003 比 partial 阶段更强

- 登录/授权、设备 IP、安全事件、发布行为均已完成。
- 发布行为已返回 5 个作品，且当天全部删除。
- 链路能从 OAuth/扫码授权、新 Web 设备、Token 生成，闭合到发布设备与 Web 新设备2一致。
- 策略名明确包含 `stealAccount`，不是普通异常标签。

### 为什么支持“扫码/OAuth 型 ATO 嫌疑”

- 04-19 四分钟内集中出现 OAuth / 扫码相关行为。
- 2 个新 Web 设备活跃天数为 0，并获得 Token。
- 命中 `stealAccount_qrLogin_accept_teen_alert` 和 `stealAccount_web_qrlogin_nohis_tag`。
- 登录态接管后，Web 新设备2在山东青岛发布 5 个作品并当天全部删除。
- 04-20 用户出现 3 次密码重置尝试且被风控拦截，和异常后补救链路方向一致。

### 为什么不能把“山东德州 / 已回扫”当作数据事实

- 数据中山东德州为 0 条，实际发布地为山东青岛。
- 回扫记录离线表无此字段，未被当前数据验证。
- 这两项只能作为人工备注和 golden hint，不进入事实证据。

### 哪些证据支持人工备注

- 支持“扫码欺诈 / OAuth 型账号接管嫌疑”：OAuth/扫码行为、新 Web 设备、Token 生成、stealAccount 策略命中、发布行为闭环。
- 支持“河南濮阳”：登录 100% 河南濮阳。
- 部分支持“山东线索”：发布在山东青岛，省份吻合但城市不同。

### 哪些证据修正人工备注

- “山东德州”被修正为“山东青岛”。
- “已回扫”未被离线表验证。
- `kuaishou.server.webday7` 未被当前摘要直接验证。
- 登录阶段不是异地，登录河南濮阳与注册地一致；异地发生在发布阶段，河南濮阳 → 山东青岛。

### 是否建议关闭 Case 003

建议可以作为 Data Agent-only ATO 试点闭环成功样例关闭，但不是作为最终人工盗号定性关闭。

关闭口径：

- Data Agent-only 已完成从 SQL 执行到 full execution evidence 的闭环。
- 数据层支持扫码/OAuth 型 ATO / 账号接管嫌疑。
- 权限限制、质量风险、人工备注修正均已记录。

不能关闭为：

- 最终人工盗号定性。
- 已验证山东德州来源。
- 已验证回扫记录。
- 已验证作品内容违规。

### 是否可以进入 Case 006

可以进入 `ATO_CASE_006_UNCERTAIN_NO_CLEAR_EVIDENCE`。

原因：

- Case 001 验证了密码登录型链路。
- Case 003 验证了扫码/OAuth 型链路。
- Case 006 是反例 / 不确定样本，适合测试不因申诉直接强判和反向排除能力。

## 17. 与人工备注 / 标签是否一致

人工备注：`欺诈 / 扫码欺诈 / 山东德州扫码地推，已回扫，河南濮阳，kuaishou.server.webday7`

```yaml
manual_note_consistency:
  qr_scan_or_oauth_ato_suspicion:
    supported_by_data: true
    reason: OAuth/扫码行为、新 Web 设备、Token 生成、stealAccount 策略命中、发布行为闭环。
  henan_puyang:
    verified_by_data: true
    reason: 登录地区 100% 河南濮阳。
  shandong_dezhou:
    verified_by_data: false
    reason: 数据中 0 条德州记录，实际发布在山东青岛。
  resweep:
    verified_by_data: false
    reason: 回扫记录离线表未验证。
  kuaishou_server_webday7:
    verified_by_data: false
    reason: 当前聚合摘要未直接验证该来源。
```

人工备注只能作为 golden hint，不得当作数据事实。

## 18. 是否可以关闭 Case 003

```yaml
can_close_case_003_as_dataagent_only_pilot: true
can_close_as_final_manual_ato_judgement: false
close_condition:
  - 所有 SQL / 查询模块均已返回聚合摘要。
  - 登录/授权、新设备、Token、策略命中、发布行为、登录发布链路均可进入 evidence。
  - Dennis Agent 已输出数据层 evidence judgement。
  - 权限限制、质量风险、人工备注修正均已记录。
cannot_close_as:
  - 最终人工盗号定性。
  - 已验证山东德州来源。
  - 已验证回扫记录。
  - 已验证作品内容违规。
```

## 19. 是否可以进入 Case 006

```yaml
can_enter_case_006: true
next_case: ATO_CASE_006_UNCERTAIN_NO_CLEAR_EVIDENCE
reason: >
  Case 001 和 Case 003 已分别覆盖密码登录型、扫码/OAuth 型正例链路。
  Case 006 可用于验证反例/不确定样本，测试 Dennis Agent 是否避免因用户申诉直接强判。
```

## 20. 是否需要回写

```yaml
backwrite_assessment:
  dataagent_markdown_response_parser_v1.md:
    needed: no
    reason: 现有 execution_result_ready、provider_conclusion_hint、permission_notes、quality_risks 规则够用。
  dataagent_sql_execution_followup_template_v1.md:
    needed: optional
    reason: 可选补充“full execution + 人工备注修正”的示例，但不是阻塞。
  ato_expected_evidence_and_boundaries_v1.md:
    needed: no
    reason: 强/中/弱证据、反证、Data Agent-only 边界规则覆盖本 case。
  ato_dataagent_question_templates_v1.md:
    needed: no
    reason: 问题模板已支持扫码/OAuth ATO 取数闭环。
```

## 21. 自评

```yaml
self_score: 92
reason:
  - 完整区分数据发现、推测、缺失证据、权限限制和质量风险。
  - 没有把申诉或人工备注当事实。
  - 明确修正山东德州与山东青岛不一致。
  - 明确已回扫未被离线表验证。
  - 保留 Data Agent-only provider hint 与最终人工定性的边界。
```
