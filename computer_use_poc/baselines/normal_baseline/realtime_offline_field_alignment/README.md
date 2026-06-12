# Realtime/Offline Field Alignment

This module is the unified field alignment layer between realtime source
observations and offline Hive / normal baseline fields.

It owns:

- source alias resolution
- field alias resolution
- canonical source and canonical field path
- field family and field role classification
- Weapon action and platform separation
- deterministic alignment metadata for L3, `normal_baseline_enricher`, and L4

It does not claim full Weapon coverage. The current registry contains seed
mappings from G-R9 plus login log aliases needed by L4 v0.1.4.

## Deterministic First

`field_alignment_resolver.py` resolves by:

1. confirmed source alias
2. seed field mapping
3. exact canonical path
4. parent/container and role rules
5. unresolved / human review when evidence is insufficient

Model-assisted semantic alignment is allowed only as a candidate generation
step outside confirmed registry writes. A model-only match must be recorded as
`model_assisted_likely_match`, `need_human_review=true`, and must not become a
confirmed match without path, sample value, business semantics, and distribution
evidence.

## Weapon Boundary

Weapon fields preserve two dimensions:

- `weapon_action`: `oneRisk | raw_data | unknown`
- `platform`: `android | ios | unknown`

`raw_data` contains detailed/device raw fields such as `cpuInfo`, `oneIpInfo`,
`sensorList`, `vendorIds`, and `vendorSecHw`. The 9 G-R9 seed mappings are all
registered as `weapon_action=raw_data`, `platform=android`.

`oneRisk` contains Weapon profile/label fields. The `oneRisk` prefix is not a
result signal by itself. Factual labels such as `oneRiskNoSim` and
`oneRiskLaunchLess10` are `factual_device_label`; conclusion fields such as
`riskScore`, `riskDecision`, and `modelDecision` are `result_signal`.

## Consumers

- `normal_baseline_enricher.py` calls `resolve_field()` before baseline lookup.
- `l4_candidate_validator.py` calls the resolver for source/path normalization
  and prefers `classify_field_role()` for role decisions.
- The old `offline_field_alignment` module is kept only as a compatibility
  import shim.
