# Broader New Wave Holdout Protocol

This protocol designs the next generalization validation only. It does not run a holdout, does not access platforms, does not call Hive/DataAgent, does not refresh release/dist/full_runtime, and does not claim verified strategy or full autonomous completion.

## Boundary

- No platform access.
- No Hive/DataAgent.
- No git commit.
- No release/dist/full_runtime refresh.
- No baseline, L6, or Hive replay.
- No verified strategy claim.
- No use of wave4/wave5 cleaned candidates as discovery input.
- No forced candidate generation to pass holdout.
- Protocol-only output cannot prove full autonomous capability.

## Holdout Layers

### 1. positive_holdout

Purpose: validate recall on a new wave that should contain clear high-value candidates.

Examples:
- New account mutation chain samples.
- New device toolchain/runtime template samples.
- New profile/history lure samples.
- New social funnel samples.
- New network environment cluster samples.

Input requirements:
- `wave_id / batch_id`: required.
- `sample_count`: recommended `>=10`, minimum `6` only if source coverage is rich.
- `source coverage`: must include core sources relevant to the hidden pattern plus at least one independent supporting source.
- `raw bundle`: required.
- `P0 foundation artifacts`: must be generated before discovery.
- `human oracle / hidden expected pattern`: required.
- `cleaned candidate set`: not allowed as discovery input.
- `oracle`: final eval only.

Pass intent: recall and replay quality, not strategy verification.

### 2. weak_or_ambiguous_holdout

Purpose: verify layering and restraint when evidence is partial, sparse, or source-gapped.

Expected behavior:
- Output supporting / data_gap / scanner_gap / report_only / replay_partial when appropriate.
- Do not force high-value output.
- Source gaps cannot be treated as no risk.

Input requirements:
- `wave_id / batch_id`: required.
- `sample_count`: recommended `>=8`.
- `source coverage`: may be incomplete, but gaps must be explicit.
- `raw bundle`: required.
- `P0 foundation artifacts`: required.
- `oracle`: recommended, may be partial.
- `cleaned candidate set`: not allowed as discovery input.

### 3. negative_or_noise_holdout

Purpose: validate false-positive control.

Noise examples:
- Schema/top value fixed fields.
- `sdkConfig` / `kconf` / config keys.
- Internal `serverIp` / `clientIp` / `serverInfo` / `kwaidc.com`.
- Pagination near-full-page.
- Default avatar/background URL.
- Fixed `logTags.color`.
- Response wrapper fields, `http_status`, `body_present`, `requestId`, `traceId`.

Expected behavior:
- No high-value candidate.
- Noise is guarded, downgraded to report-only, or suppressed.

## Execution Flow

1. Generate P0 foundation artifacts:
   - `full_action_inventory_raw_diff.json`
   - `parsed_field_inventory.json`
   - `container_parser_coverage_matrix.json`
   - `schema_noise_guard_report.json`

2. Run autonomous cold-start discovery:
   - Allowed inputs: raw diff, parsed inventory, container coverage, schema guard.
   - Forbidden inputs: challenge registry, gap-focused output, cleaned candidates, user historical challenge checklist, oracle/expected pattern.

3. Replay provenance:
   - Recompute support / miss / coverage.
   - Record raw_path / parsed_path.
   - Record schema guard and source gap.

4. Discovery provenance:
   - Mark `cold_start_autonomous`, `targeted`, `taxonomy_cleanup`, or `unknown`.
   - Replay pass alone cannot prove autonomous discovery.

5. Final eval:
   - Oracle / expected pattern can be used only after discovery and replay.
   - Final eval cannot rewrite candidate provenance.

## Metrics

- `autonomous_candidate_count`
- `replay_pass_count`
- `replay_partial_count`
- `replay_failed_count`
- `high_value_count`
- `supporting_count`
- `data_gap_count`
- `report_only_count`
- `false_or_noisy_candidate_count`
- `schema_noise_violation_count`
- `overfit_pattern_count`
- `oracle_recall`
- `oracle_precision`
- `negative_holdout_false_positive_rate`
- `weak_holdout_overclaim_count`
- `full_autonomous_confidence_level: none / low / medium / high`

## Pass Criteria

### positive_holdout_pass

- Core oracle pattern must be hit.
- `oracle_recall >= 0.6`.
- `replay_failed_count = 0`.
- `schema_noise_violation_count = 0`.
- `forbidden_input_used = false`.

Do not require recall `1.0`; use multiple positive waves before raising confidence.

### weak_holdout_pass

- `weak_holdout_overclaim_count = 0`.
- High-value only when there is strong multi-field support.
- Supporting / data_gap / report_only layering is correct.
- Source gap is not treated as no risk.

### negative_holdout_pass

- High-value false positives = `0`.
- Schema/config/internal noise candidates = `0`.
- `schema_noise_violation_count = 0`.
- Report-only guard is respected.

### broader_generalization_pass

Requires all of:
- `positive_holdout_pass = true`
- `weak_holdout_pass = true`
- `negative_holdout_pass = true`
- No forbidden input leakage.
- Hardcoded answer risk no higher than medium.
- At least three distinct holdout batches.
- At least one positive and one negative holdout batch.

## Current Material Assessment

`wave1~wave3` are suitable as weak/ambiguous and negative/noise holdouts, not as positive holdout. After P0-7c, they produce no positive autonomous candidate. That is useful for restraint and noise-suppression validation, but it cannot measure positive recall.

Known gap:
- `wave1` still has P0-3 container coverage foundation gap and must be marked `foundation_gap`.

Positive holdout requirement:
- A new raw bundle with hidden oracle is needed.
- If no new wave exists, `full_autonomous_not_proven=true` must remain.

## Recommended Holdout Batches

1. `holdout_negative_noise_wave1_3`
   - Source: existing wave1~wave3 raw bundles.
   - Purpose: verify schema/config/internal noise does not produce high-value candidates.
   - Can run now: true.

2. `holdout_weak_ambiguous_wave1_3`
   - Source: existing wave1~wave3 raw bundles.
   - Purpose: verify no overclaim when no strong autonomous candidate exists.
   - Can run now: true.

3. `holdout_positive_new_wave`
   - Source: new raw bundle with hidden oracle.
   - Purpose: measure positive recall on unseen patterns.
   - Can run now: false.

## Final Decision

- `can_run_broader_holdout_now: false`
- `required_holdout_data: new positive_holdout raw bundle + hidden oracle + generated P0 foundation artifacts`
- `expected_oracle_needed: true`
- `risk_if_only_using_wave1_3: only restraint/noise suppression can be evaluated; positive autonomous recall cannot be measured`
- `can_claim_full_autonomous_after_protocol_only: false`
- `next_action: wait_for_new_positive_holdout`
