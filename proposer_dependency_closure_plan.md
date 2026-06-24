# Proposer Dependency Closure Plan

Scope: plan only. No Python code was changed, no file was deleted, no `git add` or commit was performed, and no platform/Hive/DataAgent/release/dist/full_runtime action was taken.

## Goal

Make `llm_commonality_proposer.py` a clean proposal-layer module that can later be committed independently from validator/replay/debug/L4/L5 assets.

Target boundary:

- proposer may prepare source-grouped observation inputs, prompt/proposal payloads, fixture/mock outputs, and opt-in LLM preflight.
- proposer must not perform candidate replay, support/miss authority, rule semantics cleanup, L4/L5 ranking, baseline, Hive/L6 replay, or verified strategy judgement.

## Current Dependency Audit

`llm_commonality_proposer.py` currently imports from `commonality_proposal_validator.py`:

| helper_name | current_defined_in | used_by_proposer_for_what | truly_needed_for_proposal | contains_validator_replay_filter_semantics | suggested_handling |
|---|---|---|---:|---:|---|
| `load_json` | `commonality_proposal_validator.py` | Load raw observation input and fixture proposal payloads. | yes | no | `move_to_lightweight_utils` |
| `_coerce_records` | `commonality_proposal_validator.py` | Normalize input JSON into record list before source grouping. | yes | no, but it has input contract assumptions | `move_to_lightweight_utils` |
| `_records_from_e2e_contract` | `commonality_proposal_validator.py` | Indirect helper used by `_coerce_records` for `e2e_risk_observation_input_contract_v0_1`. | yes if that contract remains supported | no | `move_to_lightweight_utils` |
| `_payload_for_record` | `commonality_proposal_validator.py` | Select record payload body from `payload/raw_data/data/snapshot/observation/source_observation`. | yes | no | `move_to_lightweight_utils` |
| `_flatten` | `commonality_proposal_validator.py` | Flatten payload leaves for field path stats and sample values. | yes | no | `move_to_lightweight_utils` |

Conclusion: the imported helpers are raw-record preparation helpers, not validator logic. The problem is ownership and dependency direction: proposer should not import a broad validator that also contains commonality filtering, schema/commonality scoring, replay-like support recomputation, and `candidate_protocol` dependency.

## Recommended New Boundary

Allowed proposer dependencies:

- raw observation / raw record lightweight structural helper
- prompt builder
- semantic lens
- action catalog
- simple value shape / safe preview / redaction helper
- standard library JSON/path/text utilities

Forbidden proposer dependencies:

- candidate replay
- candidate provenance
- rule semantics cleanup
- source baseline / normal baseline
- L4/L5 ranking or task generation
- challenge regression
- P0-7 autonomous rerun
- validator filtering conclusions
- production/verified strategy logic

## Suggested File Structure

Add a minimal helper module:

`computer_use_poc/baselines/normal_baseline/l3_extraction/proposal_record_utils.py`

Allowed content:

- `load_json(path)`
- `coerce_observation_records(data)`
- `records_from_e2e_contract(data)`
- `payload_for_record(record)`
- `flatten_payload(value, prefix="")`
- `source_key(record)` if we want to remove `_source_key` from proposer
- `value_shape(value)` if needed for prompt preview only
- `safe_preview(value, max_len=...)` with credential-token redaction

Do not include:

- candidate replay
- support/miss recomputation
- high-value judgement
- rule semantics cleanup
- baseline / lift / precision
- verified strategy readiness
- L4/L5 ranking
- challenge regression
- P0-7 rerun logic

Recommended import after closure:

```python
from proposal_record_utils import (
    coerce_observation_records,
    flatten_payload,
    load_json,
    payload_for_record,
)
```

Then replace:

- `_coerce_records(...)` -> `coerce_observation_records(...)`
- `_flatten(...)` -> `flatten_payload(...)`
- `_payload_for_record(...)` -> `payload_for_record(...)`

`llm_commonality_proposer.py` should no longer import `commonality_proposal_validator.py`.

## Proposer-Only Test Plan

Add a narrow test:

`computer_use_poc/baselines/normal_baseline/tests/test_llm_commonality_proposer_minimal.py`

Allowed imports:

- `llm_commonality_proposer.py`
- `dynamic_prompt_builder.py`
- `proposal_record_utils.py`
- standard library

Forbidden imports:

- `dynamic_llm_semantic_discovery_runner.py`
- `code_assisted_commonality_runner.py`
- `llm_commonality_shadow_run.py`
- `commonality_proposal_validator.py`
- `semantic_feature_schema.py`
- `candidate_protocol.py`
- L4/L5 modules
- runtime runner
- platform/Hive/DataAgent clients

Test cases:

1. `proposal_record_utils` normalizes list/dict/`records` input into raw records.
2. `proposal_record_utils` supports `e2e_risk_observation_input_contract_v0_1` without validator import.
3. `build_source_observation_groups` groups by source/action, records user IDs, counts field paths, and keeps sample values.
4. `CommonalityProposer(mode="off")` returns source groups and no proposal payloads.
5. `CommonalityProposer(mode="fixture")` loads fixture proposals, caps payloads, and does not call real LLM.
6. `real_llm_preflight(enable_real_llm=False)` returns no-call mock/fixture mode.
7. `dynamic_prompt_builder` reads canonical `dennis_risk_semantic_lens.md` and remaining prompts.
8. per-action/cross-source prompts do not include oracle-only terms; oracle prompt remains final-eval-only.
9. Static dependency guard: proposer/minimal test path must not import validator/debug/L4/L5 modules.

Expected test command after implementation:

```bash
python3 -m pytest computer_use_poc/baselines/normal_baseline/tests/test_llm_commonality_proposer_minimal.py
```

Optional pre-commit smoke:

```bash
python3 -m py_compile \
  computer_use_poc/baselines/normal_baseline/l3_extraction/proposal_record_utils.py \
  computer_use_poc/baselines/normal_baseline/l3_extraction/llm_commonality_proposer.py \
  computer_use_poc/baselines/normal_baseline/l3_extraction/dynamic_prompt_builder.py
```

## Files To Keep Out Of Minimal Commit

Keep out until separately reviewed:

- `computer_use_poc/baselines/normal_baseline/l3_extraction/dynamic_llm_semantic_discovery_runner.py`
- `computer_use_poc/baselines/normal_baseline/l3_extraction/llm_commonality_shadow_run.py`
- `computer_use_poc/baselines/normal_baseline/l3_extraction/code_assisted_commonality_runner.py`
- `computer_use_poc/baselines/normal_baseline/l3_extraction/commonality_proposal_validator.py`, except as source material for moved helpers
- `computer_use_poc/baselines/normal_baseline/l3_extraction/semantic_feature_schema.py`, unless later merged into candidate protocol
- existing broad tests:
  - `computer_use_poc/baselines/normal_baseline/tests/test_dynamic_llm_semantic_discovery.py`
  - `computer_use_poc/baselines/normal_baseline/tests/test_llm_commonality_proposer.py`
- tracked modified L4/L5/runtime files

## Recommended File Changes For Closure

Planned code changes for next execution turn:

1. Add `proposal_record_utils.py` with raw observation helpers copied/narrowed from validator.
2. Update `llm_commonality_proposer.py` imports to use `proposal_record_utils.py`.
3. Keep `llm_commonality_proposer.py` proposal-only; do not add validator/replay/filter semantics.
4. Add `test_llm_commonality_proposer_minimal.py`.
5. Do not modify old broad tests except optionally leave them untouched for future broader stack work.
6. Validate that `dynamic_prompt_builder.py` still reads canonical root `dennis_risk_semantic_lens.md`.

## Acceptance Criteria

Closure passes when:

1. `llm_commonality_proposer.py` no longer imports `commonality_proposal_validator.py`.
2. `test_llm_commonality_proposer_minimal.py` passes independently.
3. `dynamic_prompt_builder.py` uses canonical `dennis_risk_semantic_lens.md`.
4. remaining prompt dependencies are explicit:
   - `prompts/base_blind_discovery_prompt.md`
   - `prompts/cross_source_discovery_prompt.md`
   - `prompts/oracle_posthoc_evaluation_prompt.md`
   - `llm_commonality_proposer_prompt.md`
5. proposer does not import replay/validator/debug/L4/L5 modules.
6. no platform/Hive/DataAgent/release/dist/full_runtime actions are required.
7. a narrow dynamic LLM proposer commit preview can be prepared.

## Risks

- Duplicating helper logic can drift from validator behavior. Mitigation: move helper to shared `proposal_record_utils.py` instead of duplicating privately.
- `e2e_risk_observation_input_contract_v0_1` support may be accidentally dropped. Mitigation: include a fixture test.
- `oracle_posthoc_evaluation_prompt.md` can become leakage if fed into discovery. Mitigation: test and document final-eval-only boundary.
- Existing broad tests will still exist and pass/fail independently; they should not block the minimal proposer commit.
- Real LLM path remains `implemented_not_verified`; no real LLM capability should be claimed.

## Final Decision

- `can_execute_closure`: `true`
- `recommended_file_changes`:
  - add `proposal_record_utils.py`
  - update `llm_commonality_proposer.py` imports/usages
  - add `test_llm_commonality_proposer_minimal.py`
- `files_to_keep_out`:
  - broad runner, shadow runner, code-assisted runner, broad validator, semantic schema, old broad tests, tracked L4/L5/runtime modifications
- `tests_to_add_or_update`:
  - add proposer-only minimal test
- `next_action`: implement closure patch in a separate execution turn, then run proposer-only pytest and py_compile, then prepare a narrow commit preview.
