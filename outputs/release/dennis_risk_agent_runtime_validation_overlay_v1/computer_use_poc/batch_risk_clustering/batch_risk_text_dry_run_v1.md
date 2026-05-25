# Batch Risk Text Dry Run v1

This dry run applies the quality rubric to the five golden sample groups. It is a text-level validation only.

No real platform access, no DataAgent execution, no auth / gateway change.

## Summary Table

| group | selected_mode check | clustering check | matrix check | representative samples | overall |
|---|---|---|---|---|---|
| ATO mixed batch | pass | pass | pass | pass | pass with caution |
| Protocol downgrade | pass | pass | pass | pass | pass with field-semantics caution |
| Interface spike | pass | pass | pass | pass | pass with baseline caution |
| Activity arbitrage | pass | pass | pass | pass | pass |
| Alert secondary attribution | pass | pass | pass | pass | pass |

## Group 1 Dry Run: ATO Mixed Batch

Expected answer should:

- select `batch_clustering_mode`.
- split into credential stuffing candidate, Harmony/OAuth candidate, user-claim-only/source-gap, and normal migration clusters.
- use abnormal matrix directions:
  - password_failure_burst -> new_device_login.
  - login_method=Harmony/OAuth -> password_reset/token_revoke.
  - stable_geo+trusted_device -> no downstream abnormal action.
- sample 4 representatives:
  - credential stuffing candidate.
  - Harmony/OAuth candidate.
  - source-gap user claim.
  - normal migration false positive.

Quality judgement:

- The pack supports the expected multi-cluster output.
- Key risk: response template should force “not one ATO batch” statement for mixed ATO samples.

## Group 2 Dry Run: Protocol Downgrade / Forged Client

Expected answer should:

- select `batch_clustering_mode`.
- split old-version high-frequency, DID mismatch, abnormal mod semantics pending, and frontend activity gap.
- explicitly state `mod=POST` is field content and must not be read as HTTP method without schema.
- separate raw app_version / DID / request frequency from derived ratios and hypotheses.

Quality judgement:

- The pack supports evidence type separation and field semantics boundary.
- Key risk: field dictionary requirement should be prominent in follow-up plan.

## Group 3 Dry Run: Interface Request Spike

Expected answer should:

- select `alert_batch_or_population_analysis_mode`.
- separate crawler/protocol candidate from campaign traffic and monitoring sampling artifact.
- use matrix directions:
  - endpoint=A -> frontend_activity_gap.
  - endpoint=B -> campaign_window.
  - sampling_policy_change -> observed_volume.
  - region -> response_code_429.
- generate DataAgent/Hive aggregation plan without execution.

Quality judgement:

- The pack prevents direct strong crawler conclusion.
- Key risk: baseline handling must remain explicit because spike analysis is easy to overstate.

## Group 4 Dry Run: Activity Arbitrage / Channel Fake Volume

Expected answer should:

- select `large_batch_aggregation_mode`.
- separate channel X candidate from channel Y normal high reward and channel Z low quality.
- output directional matrix:
  - channel=X -> reward_claim.
  - channel=X -> low_retention.
  - channel=X -> device_reuse.
  - channel=Y -> high reward but normal retention.
- avoid generic “channel abnormal” phrasing.

Quality judgement:

- The pack supports the required directional abnormal correlation.
- Key risk: low retention must stay derived evidence / business-quality clue, not black production proof.

## Group 5 Dry Run: Internal Alert Batch Secondary Attribution

Expected answer should:

- select `large_batch_aggregation_mode`.
- treat strategy hit as input evidence, not final judgement.
- split true-positive spam cluster, normal creator false-positive cluster, source timeout cluster, high-impact manual review cluster.
- sample true positive, false positive, source-gap, high-impact, and edge mixed samples.
- recommend rule split, review queue, and monitoring metrics.

Quality judgement:

- The pack supports secondary attribution, not just repeating strategy reason.
- Key risk: answer should always include false-positive and source-gap clusters for strategy recall batches.

## Cross-group Findings

Strengths:

- Threshold policy is adequate.
- Golden samples force multi-cluster reasoning.
- Abnormal correlation matrix is now a risk explanation layer, not just field A -> field B.
- Matrix rows require relation_family, baseline_status, denominator_status, relationship_strength, reverse_check, confounder_check and cannot_conclude_boundary.
- Evidence card template covers raw / derived / inference / claim / missing / blocked / historical.
- Representative sampling covers positive, boundary, false positive, high impact and source gap.

Gaps to consider before release:

- Response template could add a fixed “cluster heterogeneity check” line.
- Pattern summary could add a fixed “baseline_missing_count” field.
- Strategy recommendations could require an explicit “do not auto launch” line in every batch output.
- Golden samples should eventually become machine-checkable YAML, but markdown is sufficient for text-level review.

Post-deepening matrix checks:

- ATO Harmony/OAuth sample should output `entry-path correlation` and `medium_abnormal_correlation`, not strong, until OAuth grant and token raw evidence exist.
- Protocol downgrade sample should output `toolchain correlation`; `mod=POST` must remain field-semantics pending, not HTTP method.
- Activity arbitrage sample should output `business-arbitrage correlation`; without channel denominator it is `batch_internal_concentration`, not strong enrichment.
- Strategy recall sample should output `strategy-feedback correlation` and `selection_bias_risk`.

## Dry-run Decision

The pack can support the intended analysis loop at text/template level:

multi case -> clustering -> representative samples -> abnormal correlation matrix -> attack path hypotheses -> follow-up plan -> strategy recommendations.

It is ready for release packaging consideration after normal release preflight, but not runtime execution enforcement.
