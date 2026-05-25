# Batch Risk Quality Rubric v1

## Scoring

Total: 100 points. A batch risk clustering answer is usable at 80+, strong at 90+, and should be revised below 80.

| dimension | points | scoring question |
|---|---:|---|
| 1. Threshold and mode selection | 10 | Does it choose the correct mode for entity count and user intent? |
| 2. Correct clustering | 12 | Does it split heterogeneous cases instead of collapsing them into one risk conclusion? |
| 3. Directional abnormal correlation matrix | 12 | Does it output relation family, A -> B direction, baseline policy, strength grading, reverse/confounder checks and cannot-conclude boundary? |
| 4. Evidence type separation | 12 | Does it separate raw evidence, derived evidence, model inference, user claim, missing evidence and blocked evidence? |
| 5. Similarity boundary | 8 | Does it avoid same-gang judgement from similarity alone? |
| 6. Historical context boundary | 8 | Does it prevent historical case evidence from contaminating current batch facts? |
| 7. no_data / timeout / blocked boundary | 8 | Does it avoid using source gaps as no-risk counter evidence? |
| 8. Representative sampling | 8 | Does it select 3-5 representative samples with clear sample types? |
| 9. Executable follow-up plan | 8 | Does it propose concrete online observation and DataAgent/Hive query fields without executing them? |
| 10. Strategy / monitoring / grey / manual review | 8 | Does it propose usable controls with false-positive and review boundaries? |
| 11. Readability and length control | 6 | Is it readable for strategy analysts and concise enough for the channel? |

## Pass Criteria

Minimum pass:

- selected_mode is correct.
- at least 2 clusters when input is heterogeneous.
- abnormal correlation matrix has directionality.
- representative samples include at least one high-confidence, one boundary or false-positive, and one source-gap sample when present.
- cannot-conclude boundary is explicit.
- no credential / sensitive plaintext output.

## Automatic Fail Conditions

Any of the following should fail the answer regardless of score:

- Claims all cases are one gang only from similarity.
- Treats model_inference as raw evidence.
- Treats user_claim as strong evidence.
- Treats no_data / timeout / blocked as no-risk counter evidence.
- Uses historical case evidence as current batch fact.
- Calls or implies real DataAgent / platform execution when task is text-level planning.
- Outputs cookie / token / session / header / phone / API key.
- For 10+ entities, defaults to one-by-one online lookup without justification.
- For 50+ entities, skips aggregation / DataAgent-Hive query plan.

## Detailed Rubric

### 1. Threshold and mode selection

Full score requires:

- 1-2 -> `single_entity_execution_mode`.
- 3-4 -> `small_multi_case_execution_mode`.
- 5-9 -> `small_batch_mode`.
- 10-49 -> `batch_clustering_mode`.
- 50-499 -> `large_batch_aggregation_mode`.
- 500+ -> `alert_batch_or_population_analysis_mode`.
- Strategy / grey / false-positive design intent overrides entity-count execution.

### 2. Correct clustering

Full score requires:

- Multiple clusters for mixed inputs.
- Explicit cluster names and coverage.
- Counter / false-positive cluster when normal explanations exist.
- Source-gap cluster when evidence is unavailable.

### 3. Directional abnormal correlation matrix

Full score requires each important relation to include:

- `relation_family`.
- `relation_direction`.
- observed pattern.
- evidence basis.
- baseline status.
- denominator status.
- enrichment signal.
- coverage ratio.
- directionality.
- reverse check result.
- confounder risk.
- false-positive risk.
- relationship strength.
- attack path hypothesis.
- evidence level.
- required follow-up.
- cannot-conclude boundary.

Matrix-specific scoring:

| subdimension | points | requirement |
|---|---:|---|
| relation family | 2 | Uses infrastructure, toolchain, entry-path, behavior-chain, business-arbitrage, or strategy-feedback correctly. |
| baseline policy | 2 | Uses historical / control / strategy-population baseline when available; marks `baseline_missing` or `only_current_batch_available` when not. |
| relationship strength | 2 | Chooses strong / medium / weak / hypothesis_only / not_enough_evidence according to evidence and baseline. |
| reverse and confounder checks | 2 | Includes reverse_check, time alignment, denominator, confounder, selection bias, business explanation and source quality. |
| denominator discipline | 2 | Does not claim strong enrichment without denominator; emits `denominator_required` when missing. |
| cannot-conclude boundary | 2 | States what cannot be concluded from the matrix row. |

Required baseline policy:

- strong enrichment requires historical normal baseline or same-period control group, plus raw evidence and pseudo-correlation checks.
- only current batch available -> `batch_internal_concentration`, not strong enrichment.
- baseline_missing -> hypothesis_only or weak unless very strong raw evidence join key exists.
- strategy recall batch -> `selection_bias_risk` is mandatory.

Automatic matrix failures:

- Uses `baseline_missing` and still claims strong enrichment.
- Uses only current batch and calls it strong abnormal enrichment.
- Omits denominator status.
- Omits reverse/confounder checks.
- Omits `cannot_conclude_boundary`.
- Treats `mod=POST` as HTTP method without field dictionary.
- Fails to mark strategy recall batch selection bias.

### 4. Evidence type separation

Full score requires:

- raw evidence is current input or current observation only.
- derived evidence is clearly labeled as aggregate / ratio / distribution.
- model inference is hypothesis-only.
- user claim is weak.
- missing evidence and blocked evidence are explicit.
- historical similar pattern is not current evidence.

### 5. Similarity boundary

Full score requires:

- Similar surface patterns are not enough for same-gang judgement.
- Same-source / same-infra judgement requires join key, shared device/IP/entry/version/toolchain or behavior chain.

### 6. Historical context boundary

Full score requires:

- Current batch evidence is separated from historical pattern.
- New batch_id / entities / time window / risk domain triggers fresh_context.

### 7. no_data / timeout / blocked boundary

Full score requires:

- no_data is data gap or source limitation.
- timeout / blocked / partial source is `source_gap`.
- Over-window login no_data is not counter evidence.

### 8. Representative sampling

Full score requires 3-5 samples for 10+ entities:

- high-confidence positive.
- boundary / ambiguous.
- suspected false positive.
- high-impact when present.
- source-gap when present.

### 9. Executable follow-up plan

Full score requires:

- Concrete fields.
- Time windows.
- Group-by dimensions.
- Hypotheses to validate.
- Online readonly observation separated from DataAgent/Hive plan.
- No real execution in text dry-run.

### 10. Strategy / monitoring / grey / manual review

Full score requires:

- Candidate controls tied to clusters.
- False-positive controls.
- Monitoring indicators and rollback signals.
- Manual review queue boundaries.
- No auto launch / auto disposition.

### 11. Readability and length control

Full score requires:

- Conclusion first.
- Pattern and matrix before long detail.
- Evidence cards concise.
- KIM output can be shortened; Web/report output can expand.
