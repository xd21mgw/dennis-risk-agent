# fastQueryHbase Strategy Hit Contract v1

## Capability Positioning

`fastQueryHbase` provides a strategy hit overview for a `sourceId` within a bounded time window. It is the first choice when the user asks whether an entity or request was hit by production risk-control / anti-cheating strategies.

## Applicable Questions

- Was this `sourceId` hit by risk-control strategy?
- Was it hit by production strategy?
- Why was it blocked or verified at the strategy-evidence level?
- Is there strategy hit evidence in this time window?

## Input Fields

```yaml
source_id:
start_time_ms:
end_time_ms:
fixed_event_type_codes:
  - BS
  - ANTICRAWL
  - ACTIVITY_ANTISPAM
  - ACCOUNT
  - FLOW_ANTISPAM
limit:
```

## Output Fields

```yaml
query_status:
has_strategy_hit:
raw_record_count:
production_policy_hit_count:
risk_decision_distribution:
event_type_distribution:
risk_type_distribution:
sample_hits:
evidence_strength:
```

## Judgement Rules

- `status=200` and `message=成功` means `query_status=success`.
- Non-empty `data` means `raw_record_count > 0`.
- Any `hitProductionPolicy=true` means `has_strategy_hit=true`.
- `production_policy_hit_count` counts records where `hitProductionPolicy=true`.
- `riskDecision` should be summarized as strategy-returned action distribution, not final enforcement success.

## Evidence Interpretation

- Production policy hit is strong strategy evidence.
- Strategy evidence must still be reconciled with login, profile, device, frontend behavior, user claim, and offline aggregation evidence when making a risk judgement.
- No hit in the queried window does not mean no risk.
- No hit in the queried window does not mean no behavior occurred.

## Boundaries

- Does not parse strategy trees.
- Does not explain why a strategy configuration condition was triggered.
- Does not reconstruct hit path.
- Does not interpret strategy versions, experiments, or grey release.
- Does not replace DataAgent / Hive for batch, trend, denominator, or cross-day analysis.
