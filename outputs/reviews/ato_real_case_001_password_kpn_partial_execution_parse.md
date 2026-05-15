# ATO Real Case 001 Partial Execution Parse

## 0. Case 基本信息

- case_id: `ATO_CASE_001_PASSWORD_KPN_RESWEEP`
- 试点阶段: v2.4 Data Agent-only 只读试点
- 触发 Skill: `account_security_expert_skill`
- 当前输入类型: Data Agent SQL execution follow-up 聚合摘要
- 当前解析边界: partial execution result，不是 final case conclusion

本轮仅基于用户粘贴的 Data Agent 聚合摘要解析，不调用 Data Agent，不补造 74735 / 74737 的结果，不把用户申诉或人工备注当作事实。

## 1. 当前状态识别：partial_execution_result_ready

```yaml
status: partial
execution_state: partial_execution_result_ready
returned_type: partial_sql_execution_result
reason: >
  74733、74734、74736 已返回执行状态和部分聚合发现；
  74735 发布行为和 74737 链路关联仍 pending，且关键字段无权限，影响重大。
  因此可对已完成 SQL 生成局部 evidence，但不能做最终 ATO 结论。
conclusion_support:
  level: local_highly_suspicious_abnormal_login_but_overall_insufficient
manual_review_required: true
```

## 2. 每个 SQL ID 的状态

| SQL ID | 查询目的 | 状态 | 权限 / 字段情况 | 是否可进入 evidence |
|---|---|---|---|---|
| `74733` | 换绑 | success, 0 行 | 无权限裁剪 | 可作为反证 / 缺少敏感操作证据 |
| `74734` | 登录全景 | success, 2 行 | 无权限裁剪 | 可进入局部 evidence |
| `74736` | 安全事件 | success, 2 行 | `params` 高敏字段被移除 | 可进入局部 evidence，但需记录权限风险 |
| `74735` | 发布行为 | pending | `upload_timestamp` / `caption` / `delete_user_id` 无权限，重大影响 | 不可进入 evidence |
| `74737` | 登录-发布链路关联 | pending | 同 74735，重大影响 | 不可进入 evidence |

## 3. 可进入 evidence 的结果

来自已完成 SQL：`74733`、`74734`、`74736`。

```yaml
data_findings:
  - 时间窗口内仅 2026-04-17 有登录记录，04-16 / 04-18 无记录。
  - 4 次登录均为密码登录，0 次微信 / 验证码。
  - APP 设备为非历史环境，is_his_env=false，did_active_day=0，设备为 HUAWEI TAS-AN00。
  - APP 登录 IP 归属河南郑州，与注册地一致，城市活跃 999 天。
  - 11 小时内出现 APP → Web，两个不同设备 + 两个不同 IP。
  - 可见范围内未发现 token/session 复用或劫持线索。
  - 无换绑、无改密、无找回记录。
  - 策略命中账号安全监控、风险城市新设备、异常登录通知、高异常记录。
  - 存在 USER_SET_RISK_LEVEL_SHUFFULE 和 SEND_AQUILA_PUNISH。
  - 存在 risk_did_login_loose=true 和 risk_did_login_strict=true。
  - 未直接命中“盗号 / 密码泄露 / 钓鱼 / 短信泄露”等直接标签。
  - 离线表未直接命中“回扫”标签。
```

## 4. 暂不能进入 evidence 的结果

```yaml
not_evidence_yet:
  - 74735 发布行为：pending，且关键字段 upload_timestamp / caption / delete_user_id 无权限。
  - 74737 登录-发布链路关联：pending，且依赖发布行为关键字段，权限缺口重大。
  - 用户申诉中“盗号者发布违规视频”：申诉文本不是事实证据。
  - 人工备注“已回扫”：未被离线表直接命中，不能当作数据发现。
```

## 5. strong_evidence

这里的 strong evidence 只支持“异常登录 / 账号接管风险信号”，不支持最终 ATO 闭环。

```yaml
strong_evidence:
  - evidence: APP 登录来自非历史设备环境，is_his_env=false 且 did_active_day=0。
    supports: 异常登录环境 / 新设备风险。
    limitation: 还缺发布行为和登录-发布链路。
  - evidence: 存在 risk_did_login_loose=true 和 risk_did_login_strict=true。
    supports: 设备登录风险信号。
    limitation: 风险信号不等于盗号事实。
  - evidence: 策略命中风险城市新设备、异常登录通知、高异常记录。
    supports: 账号安全异常登录侧风险。
    limitation: 策略命中不等于最终风险事实，且 params 高敏字段被移除。
```

## 6. medium_evidence

```yaml
medium_evidence:
  - evidence: 4 次登录均为密码登录，0 次微信 / 验证码。
    supports: 与用户声称“平常使用微信或验证码登录”方向一致。
    limitation: 用户申诉不是事实；仍需历史登录基线验证是否长期如此。
  - evidence: 11 小时内 APP → Web，两个不同设备 + 两个不同 IP。
    supports: 短时多环境切换。
    limitation: 无法单独证明非本人操作或账号接管。
  - evidence: USER_SET_RISK_LEVEL_SHUFFULE 和 SEND_AQUILA_PUNISH 事件存在。
    supports: 安全事件/处置链路存在。
    limitation: params 被移除，具体原因和事件语义不足。
```

## 7. weak_evidence

```yaml
weak_evidence:
  - 用户申诉称异常登录和违规发布，仅作背景。
  - 人工备注“电商 kpn 站点密码盗号，已回扫”，仅作 golden hint。
  - 时间窗口内仅 2026-04-17 有登录记录，与 suspicious_event_time 同日，但不能单独证明盗号。
```

## 8. counter_evidence

```yaml
counter_evidence:
  - counter_item: APP 登录 IP 归属河南郑州，与注册地一致，城市活跃 999 天。
    impact: 异地/非常用城市风险被削弱，不能只按地域异常强判。
    whether_closed: partially_closed
  - counter_item: 可见范围内未发现 token/session 复用或劫持线索。
    impact: 暂不支持 token/session 被盗路径。
    whether_closed: partially_closed
  - counter_item: 无换绑、无改密、无找回记录。
    impact: 暂不支持通过账号资料/绑定关系变化证明控制权转移。
    whether_closed: partially_closed
  - counter_item: 未直接命中“盗号 / 密码泄露 / 钓鱼 / 短信泄露”等直接标签。
    impact: 不能直接按明确 ATO 标签定性。
    whether_closed: partially_closed
  - counter_item: 离线表未直接命中“回扫”标签。
    impact: 人工备注“已回扫”尚未被数据发现验证。
    whether_closed: partially_closed
```

## 9. missing_evidence

```yaml
missing_evidence:
  - 74735 发布行为结果：是否存在异常登录后违规发布，发布时间、发布设备、作品维度摘要。
  - 74737 登录-发布链路关联：登录到发布的时间差、设备一致性、IP一致性、地区一致性。
  - 发布行为关键字段权限：upload_timestamp / caption / delete_user_id 当前无权限，影响重大。
  - 安全事件 params 字段：高敏字段被移除，无法解释 USER_SET_RISK_LEVEL_SHUFFULE 和 SEND_AQUILA_PUNISH 的具体原因。
  - 历史登录基线：用户长期是否确实主要使用微信 / 验证码，而本次为密码登录。
  - 实时登录链路、实时设备指纹、实时策略引擎明细。
  - 直接回扫记录或可验证的回扫链路。
```

## 10. quality_risks

```yaml
quality_risks:
  - partial execution：关键 SQL 74735 / 74737 尚未完成。
  - permission impact：发布行为关键字段无权限，且标记为重大影响。
  - security event params removed：安全事件原因无法完整解释。
  - Data Agent-only limitation：离线聚合不能替代实时登录链路、实时设备指纹和实时策略引擎。
  - user_claim_not_fact：用户申诉不能作为事实证据。
  - manual_note_not_fact：人工备注不能作为事实证据。
  - strategy_hit_not_fact：策略命中和处置事件不等于风险事实，需要后验链路。
```

## 11. permission_notes

```yaml
permission_notes:
  - 74735 发布行为中 upload_timestamp / caption / delete_user_id 无权限，影响重大。
  - 74737 链路关联依赖同类发布字段，当前无法完成核心链路闭合。
  - 74736 安全事件 params 高敏字段被移除，影响对安全事件具体原因的解释。
  - 74733 / 74734 无权限裁剪。
```

## 12. provider_limitations

```yaml
provider_limitations:
  - provider: dataagent_provider
    limitation: 当前只返回部分 SQL 的离线聚合摘要，仍是 partial execution。
  - provider: dataagent_provider
    limitation: 发布行为和链路关联仍 pending，关键字段权限缺失。
  - missing_future_provider: realtime_log_provider
    limitation: 缺实时登录链路和请求级明细。
  - missing_future_provider: device_fingerprint_provider
    limitation: 缺实时设备指纹和设备环境细节。
  - missing_future_provider: risk_engine_provider
    limitation: 缺实时策略引擎明细和处置原因解释。
```

## 13. conclusion_support

```yaml
conclusion_support:
  level: local_highly_suspicious_abnormal_login_but_overall_insufficient
  supports:
    - 局部支持异常登录 / 新设备风险 / 账号接管嫌疑。
  does_not_support:
    - 不支持明确盗号结论。
    - 不支持关闭 Case 001。
    - 不支持“已回扫”为数据事实。
  reason: >
    已完成 SQL 显示密码登录、非历史 APP 设备、风险 did 登录标记和账号安全策略事件，
    但发布行为与登录-发布链路仍 pending 且关键字段无权限。
    ATO 强证据要求“异常登录 + 下游敏感动作链路”闭合，目前只完成登录侧和部分安全事件侧。
```

## 14. recommended_next_provider

由 Router / Dennis Agent 生成，不直接采用 Data Agent 结论。

```yaml
recommended_next_provider:
  generated_by: router_or_dennis_agent
  next_action:
    - dataagent_provider: 继续轮询 74735 / 74737，要求返回聚合摘要或明确失败/无权限/超时状态。
    - dataagent_provider: 对 74735 / 74737 申请必要字段权限，或改写为可用字段的聚合口径。
    - dataagent_provider: 请求 74736 对被移除 params 的可解释脱敏摘要，至少说明事件类型、触发原因类别、时间。
    - human_review_provider: 人工确认发布字段权限是否可开、是否能用脱敏聚合替代。
    - future_risk_engine_provider: 若需要解释 SEND_AQUILA_PUNISH / 风险等级事件，再补策略引擎明细。
    - future_device_fingerprint_provider: 若需要强化非历史设备证据，再补实时/准实时设备指纹。
```

## 15. manual_review_required

```yaml
manual_review_required: true
reason:
  - 当前是 partial execution，不是 evidence_ready。
  - 发布行为和链路关联是 ATO 闭环关键证据，仍 pending。
  - 发布字段权限缺失影响重大。
  - 安全事件 params 被移除，事件语义不完整。
  - 需要人工确认是否申请字段权限或使用脱敏聚合替代。
```

## 16. Dennis Agent 解释

一句话判断：

```text
当前局部高度疑似异常登录 / 账号接管风险，但整体仍证据不足，不能关闭 Case 001 为明确 ATO。
```

本质标识：

- 正常用户也可能出现：密码登录、新设备、APP 与 Web 切换、同注册地城市登录。
- ATO 更关键的是：登录方式或设备环境突变后，短时间内出现非本人敏感动作，尤其是违规发布、资料变更、换绑、改密、找回或 token/session 异常。
- 当前最小区分点缺口：发布行为和登录-发布链路还没返回，无法证明“异常登录后违规发布”由异常环境触发。

证据解释：

- 登录侧较强：非历史 APP 设备、did_active_day=0、risk_did_login_loose/strict 均为 true、命中风险城市新设备/异常登录通知/高异常记录。
- 账号控制权变化侧不足：无换绑、无改密、无找回；可见范围无 token/session 复用或劫持线索。
- 下游作恶链路未闭合：发布行为和登录-发布链路仍 pending，且关键字段无权限。
- 人工备注未验证：离线表未直接命中回扫标签，所以“已回扫”不能进入事实证据。

## 17. 当前最多能下什么结论

```text
局部结论：高度疑似异常登录 / 新设备账号接管风险。
整体结论：证据不足，暂不能明确支持盗号 / ATO。
```

不能升级为明确 ATO 的原因：

- 缺发布行为结果。
- 缺登录-发布链路关联。
- 缺直接盗号 / 密码泄露 / 钓鱼 / 短信泄露标签。
- 缺回扫数据发现。
- 缺实时链路与设备指纹。

## 18. 为什么不能关闭 Case 001

- 74735 发布行为 pending，且字段无权限。
- 74737 链路关联 pending，且依赖发布字段。
- ATO 强证据要求“异常登录 + 下游敏感动作链路”闭合，目前只完成登录侧异常和部分安全事件侧。
- 反证仍存在：同注册地城市、无换绑/改密/找回、无 token/session 劫持线索、无直接盗号标签。
- 人工备注“已回扫”没有被离线数据直接验证。

## 19. 下一步是继续轮询还是优化 SQL

建议“继续轮询 + 同步优化权限/SQL”。

优先级：

1. 继续轮询 74735 / 74737，直到返回 completed / failed / no_permission / timeout 的明确状态。
2. 对 74735 / 74737 的关键字段权限做处理：
   - 优先申请脱敏聚合权限；
   - 如无法开权限，改写为不依赖 `caption` / `delete_user_id` 的聚合口径；
   - 对 `upload_timestamp` 需至少提供可用于时间链路的脱敏时间桶或时间差。
3. 请求 74736 返回 params 的脱敏解释摘要，用于解释安全事件具体含义。
4. 等 74735 / 74737 有结果后重新进入 parser evidence 阶段。

## 20. 是否可以进入 Case 003

```yaml
can_enter_case_003: conditionally_yes
condition: >
  可以并行准备或启动 Case 003 的 Data Agent 取数，但不能把 Case 001 视为已完成。
  如果资源有限，优先补齐 Case 001 的 74735 / 74737，因为它们决定 ATO 链路是否闭合。
```

理由：

- Case 001 已验证 Data Agent 能返回登录侧和安全事件侧部分证据，parser 可处理 partial execution。
- 但 Case 001 尚未完成关键链路闭合，不应作为“首例已通过”的信号。
- 并行 Case 003 有价值，可测试扫码 / OAuth / token 链路，但必须独立记录状态。
