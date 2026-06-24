# Profile History Lure Regression Plan

This is a plan only. No code, tests, platform calls, Hive/DataAgent calls, git commit, release refresh, or verified strategy claim is included.

## Objective

Prevent future waves from missing profile lure evidence when current profile is empty but historical audit payloads, login submission params, user-analysis request params, or private-message contact scripts contain diversion text.

Canonical family: `profile_lure_payload`.

## Inputs

- `profile_lure_expected_path_registry.json`
- P0 foundation artifacts:
  - `parsed_field_inventory.json`
  - `container_parser_coverage_matrix.json`
  - `full_action_inventory_raw_diff.json`
  - `schema_noise_guard_report.json`
- Optional source coverage audit for source status and timeout/auth boundaries.

## Regression Cases

| case_id | fixture/source | expected status | expected signal | acceptance criteria |
|---|---|---|---|---|
| `new_holdout_C_review_history_lure` | new_holdout_C | `profile_lure_detected` | `archives_review_logs.desc.original_user_payload` | Detect 8/8 historical profile/intro `.cc` lure payload; emit `raw_text_preview`, `normalized_text`, `normalization_steps`, `matched_lure_tokens`; distinguish enforcement description from original user payload. |
| `D2_login_params_lure` | D2 | `profile_lure_detected` | `login_logs_search.logContent.params.data` | Detect 15/15 current submission payload from nested `logContent.params.data`; parser chain must include logContent JSON and nested params JSON; no hidden oracle or candidate name input. |
| `current_profile_empty_history_payload_hit` | derived from C/D2 pattern | `profile_lure_detected` | history/login path hit despite empty current profile | Empty current profile must be emitted as `business_field_gap` or supporting context, not as no-evidence; history/login payload remains high-value discovery evidence. |
| `archives_user_analysis_source_gap` | auth_failed/timeout source status | `source_gap` | `archives_user_analysis.requestParam.data` unavailable | If user analysis is auth_failed, timeout, blocked, or not_called, regression must not output `true_no_evidence`; it must preserve source gap and expected path not checked. |
| `requestParam_raw_present_parse_failed` | synthetic parser failure fixture | `parser_gap` | requestParam raw exists but no parsed child | If raw container exists and parser fails, emit parser gap with parse_error/path; do not claim no lure. |
| `profile_lure_path_drift` | synthetic equivalent sibling path | `path_drift` | payload moved from registered path to sibling/new path | If parser succeeds and semantically similar text appears under a new path, emit path drift and suggested registry update, not true no evidence. |
| `private_message_low_specificity` | private message greeting-only fixture | `true_no_evidence` or report-only | private message content | Generic greeting without contact/diversion token cannot become high-value; if reported, level must be report-only. |
| `private_message_contact_script` | private message contact phrase fixture | `profile_lure_detected` or supporting contact diversion | private message content | Repeated contact intent text must be detected with raw/normalized/tokens; default level supporting unless tied to profile mutation/enforcement chain. |
| `url_ocr_qr_unimplemented` | URL/OCR/QR needed but unavailable | `needs_more_source` | URL/OCR/QR | This phase only marks URL/OCR/QR as data_gap; regression must not claim QR/OCR/domain closure. |

## Expected Normalized Observation Shape

Every positive or reportable text observation should emit:

```json
{
  "raw_text_preview": "short original excerpt",
  "normalized_text": "deterministically normalized text",
  "normalization_steps": [
    "unicode_nfkc",
    "strip_zero_width_and_invisible_joiners",
    "collapse_whitespace_and_newlines"
  ],
  "matched_lure_tokens": [
    {"group": "contact_platform", "token": "微信"},
    {"group": "diversion_carrier", "token": ".cc"}
  ]
}
```

The raw preview must be retained separately from normalized text. Normalization is for matching, not for replacing evidence.

## Drift Gate Flow

For each wave, evaluate registry paths in this order:

1. Check source status: completed, auth_failed, timeout, blocked, not_called.
2. Check raw container presence.
3. Check parser success and parse error count.
4. Check expected parsed path presence.
5. Normalize text and emit required text fields.
6. Match lure tokens and diversion semantics.
7. Split `archives_review_logs.desc` into `original_user_payload` and `enforcement_description`.
8. Emit exactly one gate status per path family:
   - `profile_lure_detected`
   - `true_no_evidence`
   - `source_gap`
   - `parser_gap`
   - `path_drift`
   - `business_field_gap`
   - `needs_more_source`

`true_no_evidence` is only allowed when required sources completed, raw was present, parser succeeded, expected paths were checked, and no lure tokens or semantics were found.

## Acceptance Criteria

- D2 must pass with `login_logs_search.logContent.params.data` detected as current submission payload.
- new_holdout_C must pass with `archives_review_logs.desc.original_user_payload` detected as historical profile lure payload.
- `archives_review_logs.desc.enforcement_description` must be supporting only unless original submitted payload is also present.
- Current profile empty must never suppress history/login/requestParam hits.
- Private-message generic greeting must not be upgraded to high-value.
- URL/OCR/QR must remain `needs_more_source` / `data_gap`; no implementation or closure is claimed.
- Source gaps and parser gaps must not be reported as no-risk or no-evidence.

## Future Implementation Target

Later implementation can add:

- `test_profile_history_lure_regression.py`
- registry-driven path scanner
- deterministic text normalization helper
- drift gate report integrated with parser drift detector

Do not start implementation until this plan is explicitly approved for coding.

