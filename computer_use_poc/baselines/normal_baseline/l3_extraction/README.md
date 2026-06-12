# L3 Value Candidate Extraction Skill v0.1

This directory is the fixed L3 value-level candidate extraction module for the
normal-baseline/L4 validation flow.

## Boundary

L3 owns only risk-side candidate extraction and risk-side statistics:

```text
raw observation
  -> L3 value candidate extraction
  -> realtime_offline_field_alignment resolver
  -> normal_baseline_enricher
  -> L4 validator
  -> L4 cards
```

L3 does not:

- run normal-baseline comparison
- make L4 decisions
- build L5/L6/L7 combinations
- implement unpredictability-anom
- run historical recall
- recommend strategy actions
- access realtime platforms, DataAgent, or Hive

## Input

Full mode accepts local JSON following:

```text
computer_use_poc/baselines/normal_baseline/e2e_contracts/e2e_risk_observation_input_contract_v0_1.md
```

The canonical input hierarchy is:

```text
user_id -> source -> action/layer -> raw_body
```

Required source/action families when available:

| source | action/layer |
|---|---|
| `weapon_android` | `raw_data` |
| `weapon_android` | `oneRisk` / `weapon_one_risk` |
| `weapon_ios` | `raw_data` |
| `weapon_ios` | `oneRisk` |
| `login_logs` / `login_logs_search` | `login` |
| `infra_user_action_log` | `login` |
| `passport_action_log` | `passport` / `user_analysis` if participating |

Markdown tables, field contrast reports, projected rows, or manual summaries
are not full raw input. They may only be used in partial mode and must mark:

- `extraction_confidence=partial` or `low`
- `extraction_source=projected_rows:*`, `report_reconstructed:*`, or
  `manual_summary:*`
- `need_raw_confirm=true`

## Output

Output is structured L3 candidates JSON. Each candidate must satisfy
`l3_value_candidate_extraction_schema_v0_1.yaml`.

Minimum fields:

| field | meaning |
|---|---|
| `candidate_id` | Stable candidate id |
| `source_name` | Canonical source where possible |
| `platform` | `android`, `ios`, or `unknown` |
| `action_or_layer` | Source action/layer such as `raw_data`, `oneRisk`, or `login` |
| `field_path` | Canonical/full field path |
| `field_value_or_pattern` | Value, element, label, anchor marker, or pattern marker |
| `candidate_grain` | Extraction grain enum |
| `field_role_hint` | Risk-side role hint; L4 remains authoritative for decisions |
| `risk_observed_count` | Risk-side observed denominator |
| `risk_hit_count` | Risk-side hit count |
| `risk_hit_rate` | Risk-side hit rate |
| `supporting_user_ids` | Risk users supporting the candidate |
| `supporting_device_ids` | Device anchors supporting the candidate |
| `sample_values` | Small value sample |
| `extraction_source` | Raw/partial provenance |
| `extraction_confidence` | `high`, `partial`, or `low` |
| `need_raw_confirm` | Whether complete raw is still required |
| `notes` | Boundary notes |

## Candidate Grains

| input type | candidate_grain |
|---|---|
| field only fallback | `field_presence` |
| scalar | `scalar_value` |
| enum | `enum_value` |
| list/array element | `array_element` |
| oneRisk/label array | `label_value` |
| object/map child | `object_child_value` |
| parser-needed value pattern | `value_pattern` |
| ID/UUID/DID/device id | `high_cardinality_anchor` |
| unsupported complex value | `unsupported_complex_value` |

## Fixed Extraction Rules

1. Scalar fields emit `field_path + value`.
2. Enum fields emit `field_path + enum_value`.
3. Lists/arrays emit one candidate per element.
4. oneRisk/label arrays emit one candidate per label.
5. Objects/maps flatten to full child path and value.
6. Accessibility fields parse package/service elements where possible; complex
   list-of-object values become `unsupported_complex_value` with
   `parser_needed=true`.
7. High-cardinality leaves such as `xm1`, `xm3`, `did`, `device_id`, `uuid`,
   and token-like ids emit `high_cardinality_anchor` and redact direct values
   to `__anchor_value_redacted__`.
8. Result-signal leaves such as `riskScore`, `riskDecision`, `policyHit`, and
   `modelDecision` can be emitted but must carry `field_role_hint=result_signal`.
9. oneRisk prefix does not imply result signal.

## CLI

Full raw/snapshot mode:

```bash
python3 computer_use_poc/baselines/normal_baseline/l3_extraction/l3_value_level_candidate_extractor.py \
  --input-raw-json path/to/e2e_risk_observation_input.json \
  --output computer_use_poc/baselines/normal_baseline/l3_extraction/structured_l3_candidates.json \
  --summary-md computer_use_poc/baselines/normal_baseline/l3_extraction/structured_l3_candidates_summary.md
```

Current G-R9 partial mode:

```bash
python3 computer_use_poc/baselines/normal_baseline/l3_extraction/l3_value_level_candidate_extractor.py \
  --input-l4-cards computer_use_poc/baselines/normal_baseline/l4_validation/real_l4_validation_cards_from_gr9_v0_1_4.json \
  --include-gr9-label-summary \
  --output computer_use_poc/baselines/normal_baseline/l3_extraction/structured_l3_candidates_from_gr9_value_level_v0_1.json \
  --summary-md computer_use_poc/baselines/normal_baseline/l3_extraction/structured_l3_candidates_summary_v0_1.md
```

## Tests

Focused tests live in:

```text
computer_use_poc/baselines/normal_baseline/tests/test_l3_value_level_candidate_extractor.py
```

They cover oneRisk labels, nested raw_data objects, accessibility parsing,
login enum extraction, high-cardinality anchors, result-signal hints, partial
mode, schema validation, and L3/L4 compatibility fields.
