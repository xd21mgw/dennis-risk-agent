# Tianshi Policy Attribution API-read Run 002 Full Success

## 1. Run Metadata

```yaml
test_type: tianshi_policy_attribution_followup_fix
eventType: USER_REGISTER_NEW
eventId: "5370247893355116990"
queryTime: 1779774526479
policyTreeCode: USER_REGISTER_NEW
policyTreeVersion: 887
policyCode: BS_fake_account_register_thirdPlatformAll_bindphone
policyVersion: 5
overall_result: full_p0_e2e_success
```

Execution boundary:

- real_platform_access=false for this Codex landing step
- dataagent_called=false
- release_package_updated=false
- core_skill_modified=false
- credential_plaintext_output=false
- auto_enforcement=false
- final_risk_classification=false

## 2. Follow-up Fix Summary

The second internal Agent follow-up fixed both previously partial / failed points.

| Previously blocked item | Fix | Result |
| --- | --- | --- |
| `rcpEventFeatureList` returned empty data | Use `featureGroup=""` and precise `_occurTime=1779774526479` as `queryTime` | success, `feature_count=519` |
| `nodeBindPolicyAttribution` missing `policyTreeNodeCode` | Use `GET /v2/rest/pro/policyTree/queryProPolicyTree` and recursively parse the policy tree | success, `policyTreeNodeCode=53187346034508` |

## 3. Complete API Chain

| Step | API | Result | Key output |
| --- | --- | --- | --- |
| 1 | `GET /v2/rest/event/rcpEventDetail` | success | event detail, exact `_occurTime`, real-time feedback, error code, effective policy |
| 2 | `GET /v2/rest/event/rcpEventFeatureList` | success | `feature_count=519`, feature group distribution |
| 3 | `GET /v2/rest/pc/policy/getPolicyVersionListByEvent` | success | policy version context found |
| 4 | `GET /v2/rest/pro/policyTree/queryProPolicyTree` | success | resolved policy tree node |
| 5 | `POST /v2/rest/pc/policy/nodePolicyAttribution` | success | condition-level attribution |
| 6 | `GET /v2/rest/pc/policy/nodeBindPolicyAttribution` | success | node binding attribution |

## 4. Feature List Fix

```yaml
feature_list_fixed: true
queryTime: 1779774526479
featureGroup: ""
feature_count: 519
feature_group_distribution:
  - DERIVE
  - ORIG
  - COUNTER
  - SYS
  - DATASERV
  - OTHER
```

Correction:

- Do not pass Chinese category names such as 主站特征 / 原始类 / 行为类 as `featureGroup`.
- Start with `featureGroup=""`.
- `queryTime` must use exact event `_occurTime`.

Boundary:

- Do not output raw feature values.
- Output feature keys, group distribution, counts, and redacted samples only.

## 5. Policy Tree Node Fix

```yaml
policyTreeNodeCode_resolved: true
resolved_policyTreeNodeCode: "53187346034508"
node_name: 主站三方注册强绑手机号
node_code_source: recursive_queryProPolicyTree_parse
```

Correction:

- Correct policy tree API is `GET /v2/rest/pro/policyTree/queryProPolicyTree`.
- Do not use `/v2/rest/pc/policytree/getPolicyTreeByVersion`.
- Do not guess `policyTreeNodeCode` from `serial`, node name, or `policyCode`.

## 6. Node Binding Attribution Result

```yaml
nodeBindPolicyAttribution_fixed: true
attribution_status: success
node_name: 主站三方注册强绑手机号
returned_fields:
  - nodeName
  - conditionList
  - nodebindingPolicyList
effective_policy: BS_fake_account_register_thirdPlatformAll_bindphone#5
effective_policy_found: true
target_policy_online: true
target_policy_result: true
```

Interpretation:

- The target policy `BS_fake_account_register_thirdPlatformAll_bindphone#5` is online and result=true in this event/node context.
- This completes node-level policy binding attribution for the tested event.
- It still does not imply final cheating classification or enforcement recommendation.

## 7. Evidence Strength

```yaml
evidence_strength: high_for_single_event_policy_attribution
full_p0_e2e_success: true
```

Reason:

- Event detail succeeded.
- Feature snapshot succeeded.
- Policy version lookup succeeded.
- Policy tree node code resolved.
- Condition-level attribution succeeded.
- Node binding attribution succeeded.

## 8. Boundaries

- 策略归因不等于最终作弊定性。
- 不做自动处置。
- 不输出 cookie / token / session / header。
- 不输出身份证、手机号、IP 等敏感原值。
- `updateUser` 不做责任归因。
- rcp 策略归因 REST API 可 HTTP + SSO 调用的结论仅限本次已验证的策略归因 API，不泛化到所有 RCP 接口。

## 9. Current Status

`tianshi_single_event_policy_attribution_api_read_full_p0_e2e_success`
