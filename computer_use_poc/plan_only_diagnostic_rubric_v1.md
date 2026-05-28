# Plan-only Diagnostic Rubric v1

## Purpose

`plan_only_diagnostic` is used to diagnose Dennis Risk Agent capability failures before touching live platforms. It separates "brain / routing / orchestration design" from runtime config, runner, auth, and output-contract failures.

Plan-only diagnostics can prove whether the intended route and source plan are coherent. They cannot prove that live runtime config, safeBins, auth state, or source wrappers are working.

## Scoring Dimensions

Each dimension is scored `0-5`.

| dimension | score 5 means | common deductions |
|---|---|---|
| `intent_routing_score` | Correctly classifies intent, mode, and mixed slices. | Single case execution misrouted to plan-only; strategy recommendation misrouted to execution; small-batch mixed request not split. |
| `source_plan_score` | Selects correct P0 / explicit target / conditional sources and boundaries. | DataAgent/Hive not per-call authorized; browser in P0 default path; explicit strategy-hit request not treated as target source. |
| `orchestration_score` | Defines source order, checkpointing, fallback, partial output, and no automatic expansion. | P0/P1 failure lacks fallback; small batch expands beyond provided users; source failures not represented as source_quality. |
| `evidence_reasoning_score` | Separates raw evidence, strategy hit, inference, counter evidence, and missing evidence. | no_data treated as no-risk counter evidence; strategy hit treated as final judgement; no source-window boundary. |
| `output_contract_score` | Requires evidence card / source_quality / routing_metadata for execution, and routing_metadata for plan-only. | plan-only lacks routing_metadata; execution lacks evidence_card/source_quality; missing_evidence/caveats/next_action absent. |

## Failure Layer Enum

- `config/runtime`
- `intent/routing`
- `source_orchestration`
- `evidence_reasoning`
- `output_contract`
- `no_issue`

## Deduction Rules

- Single user risk / ATO execution request is classified as pure plan-only: deduct intent/routing.
- Strategy recommendation / gray rollout question enters execution without explicit "查": deduct intent/routing.
- 2-9 user mixed ATO + expansion request is not split into `small_batch_execution_with_checkpoint` plus `plan_mode_only`: deduct intent/routing and orchestration.
- DataAgent/Hive is described as automatically allowed after one consent or after P0/P1 insufficiency: deduct source_plan and orchestration.
- Browser / DOM / SPA is placed in P0 default path when API runner / API direct exists: deduct source_plan.
- Archives Center user analysis is downgraded to P1/P2 in ATO single-case planning: deduct source_plan and orchestration.
- Abnormal publish / non-owner publish / content operation is involved but publish list, publish time, publish device, and publish source chain are not P0-conditional: deduct source_plan.
- API direct is treated as the source priority criterion: deduct source_plan. API direct first is only access-method preference among comparable evidence sources.
- `source_priority` and `access_method` are not separated: deduct output_contract and orchestration.
- Browser is used as a general default replacement: deduct orchestration and runtime boundary.
- A core source that requires browser cookie activation / SPA / same-origin fetch is downgraded only because it is not pure API direct: deduct source_plan.
- Weapon riskData is fixed as unconditional P0 before any deviceId has been resolved: deduct orchestration.
- Explicit strategy-hit question does not make Tianshi strategy hit an explicit target source: deduct intent/routing.
- Stop condition allows skipping explicit target source, archives user analysis in ATO, or publish chain in abnormal-publish cases: deduct orchestration.
- no_data / timeout / blocked / auth_failed is used as low-risk / no-risk evidence: deduct evidence_reasoning.
- Strategy hit, model score, blacklist, or rule name is used as final judgement: deduct evidence_reasoning.
- Plan-only output lacks `routing_metadata`: deduct output_contract.
- Execution output lacks `evidence_card` / `source_quality` / `routing_metadata`: deduct output_contract.
- Source failure has no partial evidence / fallback / missing_evidence: deduct orchestration and output_contract.

## Final Diagnostic Status

- `plan_can_enter_execution`: route, source plan, boundaries, and output contract are coherent; execution may proceed after runtime health gates.
- `plan_blocked_before_execution`: route or source plan is wrong; fix before live execution.
- `needs_runtime_health_check`: plan is coherent, but runner / safeBin / auth / live config must be checked before execution.
- `needs_codex_fix`: mother-body docs, validators, templates, or regressions need changes.
- `needs_internal_agent_verification`: mother-body is coherent but live agent behavior must be re-tested.

## Plan -> Execution Gate

Before moving from plan-only diagnostic to execution:

1. `routing_mode` is correct.
2. `source_plan` is correct.
3. DataAgent/Hive is not executed by default and remains per-call authorized.
4. Browser is not a P0 default source; API runner / API direct comes first.
5. Source priority and access method are separated; core evidence sources are not downgraded only because they require controlled browser cookie activation / same-origin fetch.
6. no_data and strategy-hit evidence boundaries are explicit.
7. Output contract is explicit.
8. Plan-only response includes `routing_metadata` with:
   - `execution_mode=plan_mode_only`
   - `platform_called=false`
   - `dataagent_called=false`
   - `reason_not_executed`

If plan passes but execution fails, first triage `config/runtime`, `runner/safeBin/auth`, and `source_orchestration`. Do not immediately label it a brain / routing failure.

If execution succeeds but the conclusion is wrong, first triage `evidence_reasoning` and `output_contract`.

## Canonical Diagnostic Examples

### Single ATO + Strategy Hit

Question: `544963630 这个 case 有没有策略命中能辅助判断？如果是被盗号，应该重点看哪些证据？`

Expected:

- `single_entity_execution_mode` or diagnostic plan for that execution.
- Strategy hit is an explicit target source because the user explicitly asks for it.
- Minimal target sources: Tianshi strategy hit + login log + Archives Center user analysis.
- Weapon graphData as ATO cross-validation; Weapon riskData only after graphData / login log / publish chain / track-analysis yields a deviceId.
- No default DataAgent/Hive.
- Browser is not a general P0 replacement; controlled browser cookie activation / same-origin fetch can be the access method for an evidence-critical P0 source such as Archives Center.
- `strategy_hit_not_final_judgement`.
- `no_data_not_risk_exclusion`.

### ATO Publish / Time Window Inference

Expected:

- `time_window_inference` is a P0 pre-step; do not use the latest 7 days as the only window when event time is missing.
- Time anchors include user report time, Archives user analysis device/account changes, audit log time and reason, recent publish time, publish device time, strategy hit time, login event time, device first seen time, and frontend activity time.
- Audit reason guides investigation direction and window selection; it is not final ATO evidence.
- Abnormal publish makes publish time and publish device P0 anchors; look backward to login / scan / OAuth / device switch / token-session / strategy hit and forward to audit / punishment / complaint.

### Small Batch ATO + Expansion

Question: five users suspected ATO, same attack type and expansion direction.

Expected:

- Split into `small_batch_execution_with_checkpoint` and `plan_mode_only`.
- No automatic expansion beyond provided users.
- DataAgent/Hive query plan only until explicitly authorized.
- Shared anchors: device/IP/strategy/time/channel/front-backend activity.
- No strong gang / attack-cluster conclusion without cross-source evidence.

### Strategy Recommendation / OAuth Gray Rollout

Question: how to gray-test and control false positives for scan/OAuth ATO.

Expected:

- `strategy_recommendation_plan_mode` / `plan_mode_only`.
- `platform_called=false`.
- `dataagent_called=false`.
- No execution because the user mentions possible future IDs.
- If IDs are later provided with "查", split execution and plan slices.
- `routing_metadata` is still required even when no source_quality detail is needed.
