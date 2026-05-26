# Overlay Answer Experience Templates

This file contains the minimal response templates needed for the runtime validation overlay.

## Strategy Governance Template

Structure:

1. Summary.
2. Event or policy context.
3. Policy detail.
4. Policy tree asset.
5. Single-event attribution.
6. Release record.
7. Conclusions that cannot be made.
8. Next actions.

Required boundaries:

- Policy detail can show expression, but expression is not complete business causality.
- Policy tree asset is not a specific event hit path.
- Policy attribution is not final cheating judgement.
- Release record is not risk judgement.
- Online status does not mean every event will hit.
- Empty policy-level punishment list does not prove there is no punishment; binding layer may contain actions.
- Operator fields are tracing fields only, not responsibility judgement.
- Do not output sensitive original values.
- No write, launch, approval, or enforcement action.

## Strategy Hit Inventory Template

Structure:

1. Summary.
2. Query scope.
3. Event distribution.
4. Feedback / riskDecision distribution.
5. TOP policies.
6. TOP nodes.
7. TOP conditions.
8. Policy cooccurrence.
9. Representative events.
10. Gaps and boundaries.
11. Next actions.

Required boundaries:

- Strategy hit is not final risk judgement.
- High-frequency policy does not prove the policy is correct.
- High-frequency node does not prove the node is wrong.
- Cooccurrence is a risk-perception signal, not group or attack-path conclusion.
- no_data / timeout / blocker cannot be interpreted as no risk.
- Strong confidence label is not final judgement.
- Operator fields are tracing fields only.
- No sensitive original values and no write action.

## Live Attach Candidate Template

Structure:

1. Summary.
2. Query scope.
3. Attach event distribution.
4. Hit policy overview.
5. Representative events.
6. Condition-level attribution path.
7. Known gaps.
8. Conclusions that cannot be made.
9. Next actions.

Required boundaries:

- This is beta / partial candidate, not full success.
- `event_detail_partial` must be visible when detail is unavailable.
- Detail timeout is not no_data.
- `nodePolicyAttribution` path can supplement an empty tree node response, but source must be marked.
- Strategy hit is not final risk judgement.

## Business Security Scene Asset Map Template

Structure:

1. Summary.
2. Covered domains.
3. Verified scenes.
4. Partial scenes.
5. Candidate-only scenes.
6. High-value next validation scenes.
7. Parameter gaps.
8. Boundaries.
9. Next actions.

Required boundaries:

- Asset map is not an online execution ability.
- Finding an eventType does not mean attribution is validated.
- Finding a policy tree does not mean the strategy is currently hitting.
- Strategy existence is not risk existence.
- Do not trigger platform execution.

## ANTICRAWL Candidate Query-plan Template

Structure:

1. Current status: candidate-only.
2. Known ANTICRAWL eventType family.
3. Required inputs: source_id / eventId / time window / interface.
4. Suggested chain: hit overview, event detail supplement, representative event detail, representative attribution.
5. Current gaps.
6. Boundaries.

Required boundaries:

- Not executable runtime.
- No hit sample means no attribution claim.
- Interface abnormality is not automatically crawler evidence.

## Real-name Feature Service Partial Contract Template

Structure:

1. Summary.
2. Current available capability.
3. Parameters and mapping.
4. Field output status.
5. Redacted summary that can be output.
6. Fields that cannot be output.
7. Conclusions that cannot be made.
8. Next actions.

Parameter notes:

- access path: `/v2/rest/testCase/run`
- foreign key: `EB_USER_REAL_NAME_VERILY__1`
- case type: `FEATURE`
- event type: `TEST_TOOL_EVENT_TYPE`
- `sourceId` maps to userId.
- `activityName` maps to call condition.
- required `activityName`: `MERCHANT_NEWSHOP_OPEN_AWARD`
- service-side `sid` is filled by feature configuration.

Allowed output:

- real-name verification presence flag.
- ID presence flag.
- province-level summary.
- city-level availability flag.
- age bucket.
- gender summary.
- redaction flag.

Forbidden output:

- raw ID number.
- ID prefix.
- name.
- full birth date.
- phone number.
- full IP.
- detailed address.

Required boundaries:

- Real-name existence does not prove本人操作.
- Missing real-name data does not prove black-market behavior.
- Province match with publish IP does not independently exclude ATO.
- Province mismatch does not independently prove ATO.
- Age and gender cannot be standalone risk evidence.
- Identity-derived information must be combined with login, device, publish path, historical behavior, and content evidence.
