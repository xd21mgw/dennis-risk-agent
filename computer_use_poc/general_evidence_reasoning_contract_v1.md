# General Evidence Reasoning Contract v1

This contract applies to Dennis Risk Agent risk judgement across account security, protocol attack, group control, anti-crawler, activity anti-cheating, traffic diversion, traffic anti-cheating, strategy attribution, and batch risk clustering.

It is not ATO-specific. `62950989` is retained as one account-security bad-case instance, but the rules below are general judgement discipline.

## Core Rules

### no_data_not_risk_exclusion

No source returning `no_data` can independently exclude risk. `no_data` must be recorded as source state with its time window, filters, and coverage boundary.

### strategy_hit_not_final_judgement

Strategy hit, rule hit, model score, blacklist hit, risk tag, or confidence level is a lead or cross-validation direction. It is not a final risk judgement by itself.

### raw_evidence_first

Prioritize raw behavior evidence, entity relation, time sequence, and device/IP/action consistency over policy names or high-level scores.

### evidence_type_separation

Every evidence item must identify its type:

- `raw_evidence`
- `strategy_hit`
- `model_score`
- `inference`
- `user_claim`
- `counter_evidence`
- `missing_evidence`

Do not mix inference with source observation. Do not write hypotheses as confirmed facts.

### conclusion_recompute_after_new_evidence

When new evidence arrives, recompute the conclusion. Do not keep an obsolete first judgement after Hive, DataAgent, strategy attribution, platform retry, or manual evidence changes the evidence set.

### source_window_boundary

Every source must expose time window and coverage. Out-of-window or out-of-scope evidence must be marked `missing_evidence`, `source_gap`, or `required_offline_check`.

### partial_not_final

When sources are incomplete, blocked, stale, timed out, or partial, the conclusion must be one of:

- `partial_support`
- `insufficient_support`
- `needs_more_evidence`

Do not make final strong conclusions from partial evidence.

### user_visible_evidence_gate

In evidence mode, the user-visible answer must include:

- a natural-language `evidence_card` or evidence-chain summary;
- concise `source_quality` boundary;
- `missing_evidence` and `next_action`;
- conclusion boundary.

Full `routing_metadata` is internal audit material. It appears only in debug,
run log, regression, YAML output, or when the user explicitly requests raw
routing / execution metadata.

## Scenario Examples

### Account Security / ATO

Login log `no_data`, strategy hit, or Hive pending result is not final proof. Use login chain, device consistency, token / OAuth / scan chain, publish audit, and time sequence.

### Protocol Attack

Interface no_data, missing frontend behavior, or one abnormal field such as `mod=POST` is not enough. Use request shape, version distribution, device identity, frontend/backend consistency, and time sequence.

### Group Control / Device Risk

Device tag or group-control score is not enough. Verify multi-account shared device/IP, behavior rhythm, task synchronization, app/runtime environment, and relation graph.

### Anti-crawler

QPS rise, UA anomaly, or single strategy hit is not enough. Verify interface path, account/IP/device aggregation, request distribution, cost pattern, and normal traffic baseline.

### Activity Anti-cheating

Strategy hit or reward anomaly is not enough. Verify register-active-task-reward-withdraw chain, channel quality, device/IP aggregation, and control/holdout comparison.

### Traffic Diversion

Report or strategy hit is not enough. Verify relation chain, private message / profile / comment / search / external link behavior, and content-to-conversion path.

### Traffic Anti-cheating

Exposure/click/conversion anomaly is not enough. Verify traffic source, placement, device/IP/account aggregation, conversion path, RTA/RTB consistency, and downstream value.

### Strategy Attribution

Policy attribution explains why a policy hit in an event. It does not prove user cheating or business risk by itself.

### Batch Risk Clustering

Co-occurrence, top strategy, top node, shared IP/BSSID/device, or historical context is only a cluster lead until joined with current-batch evidence and denominator checks.

Batch attack judgement uses exactly three runtime modes:

- `full_observation_mode` for 2-10 entities.
- `sample_expand_validate_mode` for >10 urgent / unknown / same-origin
  validation when no wide-table result exists yet.
- `wide_table_aggregate_mode` for wide table, feature, coverage, precision,
  strategy, historical review, DataAgent/Hive or large statistical analysis
  intent.

Shared batch evidence boundaries:

- `entity_resolution_first` is required before login, Weapon, Track, content,
  strategy or warehouse aggregation reasoning.
- `source_commonality_card` must precede multi-source fusion for realtime batch
  observation.
- `wide_table_aggregate_report` is a statistics package, not a final risk
  judgement.
- DataAgent/Hive pending or planned queries are not verified evidence.
- DataAgent/Hive execution requires explicit authorization for each query scope.
- Strategy hit alone is not final judgement.
- no_data, timeout, auth_failed, blocked, body gap and source window gaps are not
  no-risk counter evidence.
- Representative samples do not prove full population coverage; full-batch
  coverage requires offline validation or replay.
- Wide-table correlation does not equal a complete attack-chain fact.
- Dennis recommends strategy candidates and validation paths; it does not
  auto-launch strategy or dispose users.

## General Evidence Card Schema

```yaml
evidence_card:
  conclusion:
  confidence:
  conclusion_state: partial_support | insufficient_support | needs_more_evidence | data_supports_risk | data_against_risk
  strong_evidence:
    - evidence_type:
      source:
      source_quality:
      time_window:
      statement:
  medium_evidence: []
  weak_evidence: []
  counter_evidence: []
  missing_evidence: []
  completed_sources: []
  source_quality:
    completed_sources: []
    no_data_sources: []
    blocked_sources: []
    auth_failed_sources: []
    timeout_sources: []
    parse_error_sources: []
    partial_sources: []
    stale_sources: []
    missing_sources: []
  recompute_state:
    recomputed_after_new_evidence: true | false
    previous_conclusion:
    changed_by:
  next_action:
  routing_metadata:
    user_visible_default: false
    shown_only_when: debug | run_log | regression | explicit_metadata_request
```
