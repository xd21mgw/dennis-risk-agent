# L3 Value Candidate Extraction Contract v0.1

## Capability

`l3_value_level_candidate_extractor.py` is the only module that should convert
risk-side source observations into structured L3 candidates. Agent/runtime
prompts should call this module instead of maintaining field extraction rules
in natural language.

## Full Input Contract

Full extraction requires a local JSON file following:

```text
e2e_risk_observation_input_contract_v0_1
```

Core hierarchy:

```text
user_id
  -> source_name
    -> action_or_layer
      -> raw_body
```

Full raw input must preserve:

- nested objects and child paths
- arrays/lists and original elements
- oneRisk/label arrays or maps
- accessibility package/service strings or lists
- sensorList structures or parseable strings
- login `action` / `action_type` enum values
- device/account/login/context keys needed for support counting

## Partial Input Contract

If the input is projected rows, field contrast reports, L4 cards, screenshots,
or manual summaries, the extractor may run only in partial mode. Every partial
candidate must mark:

| field | value |
|---|---|
| `extraction_confidence` | `partial` or `low` |
| `need_raw_confirm` | `true` |
| `extraction_source` | prefixed with `projected_rows:`, `report_reconstructed:`, or `manual_summary:` |

Partial mode cannot be used to claim full raw extraction.

## Output Contract

Output file:

```text
structured_l3_candidates.json
```

Each candidate must include:

| field | required |
|---|---:|
| `candidate_id` | yes |
| `source_name` | yes |
| `platform` | yes |
| `action_or_layer` | yes |
| `field_path` | yes |
| `field_value_or_pattern` | yes |
| `candidate_grain` | yes |
| `field_role_hint` | yes |
| `risk_observed_count` | yes |
| `risk_hit_count` | yes |
| `risk_hit_rate` | yes |
| `supporting_user_ids` | yes |
| `supporting_device_ids` | yes |
| `sample_values` | yes |
| `extraction_source` | yes |
| `extraction_confidence` | yes |
| `need_raw_confirm` | yes |
| `notes` | yes |

Compatibility aliases may be retained for downstream consumers:

- `source_action`
- `layer`
- `field_value`
- `risk_sample_count`
- `risk_covered_count`
- `risk_value_count`
- `risk_value_ratio`

## Role Boundaries

| layer | owns |
|---|---|
| L3 | risk-side value/element/label extraction and risk-side statistics |
| realtime_offline_field_alignment | source/path/canonical/role registry |
| normal_baseline_enricher | normal field/value coverage lookup |
| L4 validator | feature acceptance/rejection validation |
| L5+ | combinations, unpredictability, structure candidates, historical recall |

L3 must not call DataAgent/Hive or realtime platforms.

## Current G-R9 Boundary

The current G-R9 replay remains partial because local complete raw/snapshot
input is missing. The 8 value-level candidates are from manual label summary,
and the 22 field-level fallback candidates are reconstructed from existing L4
cards.
