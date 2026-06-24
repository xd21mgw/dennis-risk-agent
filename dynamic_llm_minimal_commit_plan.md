# Dynamic LLM Proposer Minimal Commit Plan

Scope: plan only. No code change, file deletion, `git add`, commit, platform access, Hive/DataAgent call, or release/dist/full_runtime refresh was performed.

## Overall Judgement

- `dynamic_llm_route_worth_keeping`: `true`
- `minimal_active_proposer_possible`: `true`
- `can_prepare_minimal_commit`: `false`
- reason: the active proposer is close to a clean proposal layer, but its current imports and tests still pull in broader validator/debug/L4/L5 assets. A clean minimal commit needs one follow-up refactor or a deliberate decision to include a narrowed validator.

The dynamic LLM proposer line is worth preserving as a future L3 Agent brain proposal layer, not as a replacement for the committed P0 foundation. Its correct boundary is:

- responsible for: source grouping, prompt/proposal input assembly, fixture/mock proposal path, opt-in real LLM preflight, raw proposal payload shaping
- not responsible for: support/miss replay, candidate provenance, rule semantics cleanup, baseline/L6/Hive replay, verified strategy, full autonomous proof
- current real LLM status: `implemented_not_verified`; no real LLM capability should be claimed until an adapter/client path is executed and tested with concrete evidence

## Active Proposer Minimal Closure

Logical minimal proposer assets:

- `computer_use_poc/baselines/normal_baseline/l3_extraction/llm_commonality_proposer.py`
- `computer_use_poc/baselines/normal_baseline/l3_extraction/llm_commonality_proposer_prompt.md`
- `computer_use_poc/baselines/normal_baseline/l3_extraction/dynamic_prompt_builder.py`
- `computer_use_poc/baselines/normal_baseline/l3_extraction/dennis_risk_semantic_lens.md`
- `computer_use_poc/baselines/normal_baseline/l3_extraction/action_catalog_builder.py`
- `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/base_blind_discovery_prompt.md`
- `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/cross_source_discovery_prompt.md`
- `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/oracle_posthoc_evaluation_prompt.md`

These files are not sufficient for a clean commit as-is because `llm_commonality_proposer.py` imports helper functions from `commonality_proposal_validator.py`.

As-is dependency that blocks a narrow commit:

- `computer_use_poc/baselines/normal_baseline/l3_extraction/commonality_proposal_validator.py`

Recommended handling: do not include the broad validator in the minimal proposer commit yet. First split its raw-record helper functions (`load_json`, `_coerce_records`, `_payload_for_record`, `_flatten`) into a small shared helper or move equivalent private helpers into the proposer, then add minimal tests. That requires code changes, so it is out of scope for this plan-only turn.

## Prompt Dependencies

`dynamic_prompt_builder.py` currently depends on:

- `action_catalog_builder.py`
- canonical root lens: `dennis_risk_semantic_lens.md`
- `prompts/base_blind_discovery_prompt.md`
- `prompts/cross_source_discovery_prompt.md`
- `prompts/oracle_posthoc_evaluation_prompt.md`

The three remaining prompt files are real dependencies of the current builder. They should be included only if the builder is included. `oracle_posthoc_evaluation_prompt.md` has higher leakage risk because it is for final eval only; the commit must document that it cannot be fed into discovery prompts.

## Files Not In This Minimal Commit

Do not include:

- `computer_use_poc/baselines/normal_baseline/l3_extraction/dynamic_llm_semantic_discovery_runner.py`
- `computer_use_poc/baselines/normal_baseline/l3_extraction/llm_commonality_shadow_run.py`
- `computer_use_poc/baselines/normal_baseline/l3_extraction/code_assisted_commonality_runner.py`
- `computer_use_poc/baselines/normal_baseline/l3_extraction/commonality_proposal_validator.py` until narrowed/split
- `computer_use_poc/baselines/normal_baseline/l3_extraction/semantic_feature_schema.py`
- tracked modified L4/L5/runtime files
- old broad tests as-is

Reasons:

- `dynamic_llm_semantic_discovery_runner.py`: broader debug/experimental runner, not a minimal proposer asset.
- `llm_commonality_shadow_run.py`: shadow/audit workflow, not required for proposal preparation.
- `code_assisted_commonality_runner.py`: overlaps with deterministic replay/provenance and should not be bundled into minimal LLM proposer.
- `commonality_proposal_validator.py`: useful but too broad; overlaps with candidate replay/rule semantics and imports `candidate_protocol.py`.
- `semantic_feature_schema.py`: likely future schema asset, but overlaps with candidate protocol and needs a separate schema decision.
- tracked L4/L5/runtime files: unrelated dirty worktree; do not mix into dynamic LLM commit.

## Test Commitability

- `test_llm_commonality_proposer.py`: not suitable for minimal commit as-is. It imports `code_assisted_commonality_runner.py`, `commonality_proposal_validator.py`, `llm_commonality_shadow_run.py`, tracked L3/L4/L5 modules, and L5 generator.
- `test_dynamic_llm_semantic_discovery.py`: not suitable for minimal commit as-is. It validates the broader debug runner and `semantic_feature_schema.py`, not just proposer/prompt assembly.

Needed before a clean commit:

- a small proposer-only test for `build_source_observation_groups`
- a no-call real LLM preflight test proving default behavior is mock/fixture/offline
- a prompt-builder test proving canonical lens + remaining prompt dependencies are read and oracle prompt is final-eval only
- no dependency on debug runner, shadow runner, code-assisted runner, tracked L4/L5 changes, or L5 generator

## File Matrix

| file_path | minimal role | suggested_action | reason |
|---|---|---|---|
| `computer_use_poc/baselines/normal_baseline/l3_extraction/llm_commonality_proposer.py` | proposal layer | `keep_for_dynamic_llm_commit_after_dependency_split` | Correct long-term boundary, but currently imports broad validator helpers. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/llm_commonality_proposer_prompt.md` | proposer runtime prompt | `keep_for_dynamic_llm_commit_after_review` | Needed by `load_runtime_prompt()` and real HTTP adapter path; must be reviewed for no verified/baseline claims. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/dynamic_prompt_builder.py` | prompt assembly | `keep_for_dynamic_llm_commit` | Reads canonical lens and prompt templates; no model call. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/dennis_risk_semantic_lens.md` | canonical semantic lens | `keep_for_dynamic_llm_commit` | Long-term semantic lens asset. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/action_catalog_builder.py` | action family catalog | `keep_for_dynamic_llm_commit_after_user_accepts_canonical_catalog` | Replaces deleted YAML prompt/catalog fragments; used by prompt builder. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/base_blind_discovery_prompt.md` | required prompt dependency | `keep_for_dynamic_llm_commit_after_review` | Required by builder; should be reviewed for leakage and stale assumptions. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/cross_source_discovery_prompt.md` | required prompt dependency | `keep_for_dynamic_llm_commit_after_review` | Required by cross-source prompt builder. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/oracle_posthoc_evaluation_prompt.md` | final eval prompt | `uncertain_need_user_review` | Required by builder but high leakage risk if misused as discovery input. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/commonality_proposal_validator.py` | broad validator | `merge_into_existing_or_split_helpers` | Current proposer depends on helpers, but validator overlaps with replay/rule semantics. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/dynamic_llm_semantic_discovery_runner.py` | broad runner | `keep_debug_only` | Useful as historical experimental runner, not minimal proposer. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/llm_commonality_shadow_run.py` | shadow run | `keep_debug_only` | Not required for proposer; may be useful later for shadow eval. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/code_assisted_commonality_runner.py` | code-assisted executor | `merge_later_or_keep_debug_only` | Overlaps with deterministic replay/provenance; avoid in minimal commit. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/semantic_feature_schema.py` | feature schema | `merge_later` | Potential long-term schema asset but overlaps with candidate protocol. |
| `computer_use_poc/baselines/normal_baseline/tests/test_llm_commonality_proposer.py` | broad integration test | `do_not_commit_as_minimal` | Pulls validator, code-assisted, shadow, L4/L5. |
| `computer_use_poc/baselines/normal_baseline/tests/test_dynamic_llm_semantic_discovery.py` | broad runner test | `do_not_commit_as_minimal` | Tests debug runner and schema, not minimal proposer. |

## Dependency Blockers

1. `proposer_depends_on_broad_validator`
   - severity: `high`
   - detail: `llm_commonality_proposer.py` imports `_coerce_records`, `_flatten`, `_payload_for_record`, `load_json` from `commonality_proposal_validator.py`.
   - impact: cannot commit proposer alone without either including the broad validator or doing a small helper split.

2. `prompt_builder_depends_on_catalog_and_prompts`
   - severity: `medium`
   - detail: `dynamic_prompt_builder.py` imports `FAMILY_PROMPTS` / `card_for_action` and reads three prompt files plus canonical lens.
   - impact: the builder must be committed with catalog, lens, and prompts as one unit.

3. `tests_are_broader_than_minimal`
   - severity: `high`
   - detail: current tests validate the broad experimental stack, not only the proposer.
   - impact: a minimal commit needs new or narrowed tests.

4. `oracle_prompt_leakage_guard_needed`
   - severity: `medium`
   - detail: oracle posthoc prompt is a builder dependency but must only be used in final eval.
   - impact: commit docs/tests must lock this boundary before including it.

## Three Options

### Option A: Prepare Minimal Proposer Commit After Narrowing

Target: make `llm_commonality_proposer.py` independently committable as proposal-only layer.

Includes after small follow-up refactor:

- proposer
- proposer prompt
- prompt builder
- canonical lens
- action catalog
- three prompt templates
- new proposer-only tests
- small shared observation helper or local proposer helpers

Excludes:

- dynamic runner
- shadow runner
- code-assisted runner
- broad validator
- semantic schema
- tracked L4/L5/runtime modifications

Risk: small refactor required; until tests are narrowed, commit is not ready.

Recommended: yes, but not in this no-code-change turn.

### Option B: Commit Broader Dynamic LLM Stack

Target: commit current experimental stack as-is.

Includes:

- proposer
- prompt builder
- action catalog
- lens/prompts
- validator
- code-assisted runner
- shadow runner
- dynamic semantic discovery runner
- semantic schema
- broad tests

Risk: high. This would mix proposal, validation, shadow, debug runner, and schema responsibilities; it also increases overlap with committed P0 replay/provenance.

Recommended: no.

### Option C: Pause Dynamic LLM, Handle Tracked L4/L5/Runtime Old Changes

Target: avoid expanding dynamic LLM surface until helper split/test narrowing is done.

Includes:

- no dynamic LLM commit
- separate review of tracked modified L4/L5/runtime files

Risk: dynamic LLM assets remain untracked and can drift.

Recommended: acceptable if the priority is to reduce dirty tracked files first.

## Final Recommendation

- `can_prepare_minimal_commit`: `false`
- `recommended_next_action`: split proposer raw-record helpers or accept a narrowed validator dependency, then add proposer-only tests; do not commit the broad dynamic LLM stack as-is.
- `keep_for_next_commit`: proposer, proposer prompt, prompt builder, canonical lens, action catalog, three remaining prompts, after dependency/test cleanup.
- `exclude_now`: debug runner, shadow runner, code-assisted runner, semantic schema, broad tests, tracked L4/L5/runtime changes.
- `user_review_required`: oracle prompt boundary, action catalog as canonical catalog, whether to split helper module or include narrowed validator.
