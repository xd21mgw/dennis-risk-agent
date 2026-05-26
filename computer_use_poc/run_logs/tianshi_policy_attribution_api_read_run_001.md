# Tianshi Policy Attribution API-read Run 001

## 1. 本轮目标

沉淀内部 Agent 返回的单事件策略归因 API-read partial success 结果，形成 Dennis Risk Agent 的轻量策略归因能力文档。

本轮只做本地文档和 run log：

- real_platform_access=false
- dataagent_called=false
- release_package_updated=false
- core_skill_modified=false
- write_action=false
- auto_enforcement=false
- final_risk_classification=false

## 2. 验证输入

```yaml
eventType: USER_REGISTER_NEW
eventId: "5370247893355116990"
event_time: "2026-05-26 13:48:47 Asia/Shanghai"
policyTreeCode: USER_REGISTER_NEW
policyTreeVersion: 887
policyCode: BS_fake_account_register_thirdPlatformAll_bindphone
policyVersion: 5
```

Query time correction:

- `queryTime` 不能使用错误年份时间戳。
- `queryTime` 必须使用事件发生时间的毫秒戳。

## 3. Step Result Summary

| Step | API / Action | Result | Notes |
| --- | --- | --- | --- |
| 1 | rcp REST API over HTTP + SSO | success | REST API 可通过 HTTP + SSO 直接调用 |
| 2 | `GET /v2/rest/event/rcpEventDetail` | success | 事件详情成功 |
| 3 | `GET /v2/rest/pc/policy/getPolicyVersionListByEvent` | success | 策略版本成功 |
| 4 | `POST /v2/rest/pc/policy/nodePolicyAttribution` | success | 条件级归因成功，4 个条件均 true |
| 5 | `GET /v2/rest/event/rcpEventFeatureList` | partial | 返回空 data，标记 `feature_snapshot_empty_or_unavailable` |
| 6 | `GET /v2/rest/pc/policy/nodeBindPolicyAttribution` | blocked | 缺 `policyTreeNodeCode` |

Overall result: `4/6 success`, `1 partial`, `1 blocked`.

## 4. Event Detail Observation

`rcpEventDetail` 成功读取到：

- real_time_feedback: 阻止
- error_code: `217009`
- effective_policy: `BS_fake_account_register_thirdPlatformAll_bindphone#5`
- hit_policies:
  - `BS_Register_nosense_captcha_all#5`
  - `BS_fake_account_register_thirdPlatformAll_bindphone#5`

Interpretation boundary:

- `riskDecision` / real-time feedback 是策略返回动作证据。
- 它不等于最终作弊定性。
- 它不等于自动处置建议。

## 5. Policy Version Observation

`getPolicyVersionListByEvent` 成功返回目标策略版本上下文：

- policyCode: `BS_fake_account_register_thirdPlatformAll_bindphone`
- policyVersion: `5`
- version_found: true

## 6. Condition Attribution Observation

`nodePolicyAttribution` 成功返回条件级归因：

- attribution_status: success
- condition_count: 4
- true_condition_count: 4
- false_condition_count: 0

Interpretation:

- 这足以支持“轻量策略归因证据”。
- 可以解释该策略在该事件中条件是否命中。
- 条件表达式可摘要展示，但特征业务含义仍需要特征字典或人工解释。

## 7. Partial / Blocked Sources

### Feature List

`/v2/rest/event/rcpEventFeatureList` 返回空 data。

Required label:

`feature_snapshot_empty_or_unavailable`

Boundary:

- 不得解释为无特征。
- 不得解释为无风险。
- 不得解释为策略无依据。

### Node Binding Attribution

`/v2/rest/pc/policy/nodeBindPolicyAttribution` blocked。

Blocker:

- missing_required_param: `policyTreeNodeCode`

Boundary:

- 不影响轻量条件归因。
- 影响完整策略树节点绑定归因。

### Policy Tree API

Policy tree API 在 HTTP 直连下 403。

Likely blocker:

- browser secondary auth
- permission gap
- request context gap

Boundary:

- 403 / auth blocker 不得解释为 no_data。

## 8. Evidence Strength

evidence_strength: `medium_for_policy_condition_attribution`

Reason:

- Event detail, policy version, and node policy attribution all succeeded.
- 4/4 conditions true supports condition-level explanation.
- Feature snapshot and node binding remain incomplete.
- Full strategy tree path is not closed.

## 9. Not Done

- 未访问真实平台。
- 未调用 DataAgent。
- 未修改核心 Skill。
- 未更新 release package。
- 未验证 `policyTreeNodeCode` 获取路径。
- 未完成 `nodeBindPolicyAttribution` 成功样例。
- 未进入完整策略树理解能力。

## 10. Conclusion

Current status:

`tianshi_single_event_policy_condition_attribution_api_read_partial_success`

This is enough for lightweight condition-level strategy attribution, but not enough for full policy tree node binding or final risk classification.
