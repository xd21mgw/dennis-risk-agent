# Remaining Worktree Audit

Scope: read-only audit plus requested report files. No git add, no commit, no delete, no platform access, no Hive/DataAgent, no release/dist/full_runtime refresh.

## Overall Conclusion
- `can_commit_anything_now`: `false`
- `recommended_next_commit_group`: `none_immediate; choose cleanup/dynamic_LLM/runtime_track before staging`
- `files_recommended_for_delete`: one of the duplicate Dennis semantic lens docs after choosing canonical location
- `files_recommended_for_separate_commit`: `computer_use_poc/runtime_case_execution_runner.py`, `AGENTS.md`, `computer_use_poc/baselines/normal_baseline/src/normal_baseline_enricher.py`, `dynamic LLM proposer stack only after pruning/consolidation`
- `files_need_user_review`: `computer_use_poc/baselines/normal_baseline/l3_extraction/l3_value_level_candidate_extractor.py`, `computer_use_poc/baselines/normal_baseline/l3_extraction/dynamic_llm_semantic_discovery_runner.py`, `computer_use_poc/baselines/normal_baseline/l3_extraction/llm_commonality_shadow_run.py`, `computer_use_poc/baselines/normal_baseline/l3_extraction/code_assisted_commonality_runner.py`, `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/**`
- `files_should_not_commit`: `/private/tmp/**`, `release/dist/full_runtime outputs`, `debug/historical dynamic LLM runners before pruning`, `duplicate prompt/lens docs before canonicalization`

## Git Summary

- tracked modified files: `11`
- untracked files: `18`
- dynamic LLM tests: `41 passed in 0.61s`

## File Matrix

| file_path | status | category | suggested_action | recommended_commit_group | reason |
|---|---|---|---|---|---|
| `AGENTS.md` | modified | A.tracked_modified_files / C.docs_runtime_policy | uncertain_need_user_review | runtime_policy_guard_separate_review | Broad agent policy change is valuable but affects all future behavior; it should not be bundled with dynamic LLM or L4/L5 changes. |
| `computer_use_poc/runtime_case_execution_runner.py` | modified | A.tracked_modified_files / runtime | separate_commit | runtime_raw_observation_contract | Useful for future raw-bundle quality and D1/D2-style contracts, but it touches core execution runner and needs dedicated review/tests. Do not mix with dynamic LLM modules. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/README.md` | modified | A.tracked_modified_files / C.docs_notes_prompts | separate_commit | dynamic_llm_l3_integration_docs | Documentation aligns with dynamic LLM/L3 integration, not the already-committed P0 foundation. Commit with the dynamic LLM protocol work if retained. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/candidate_protocol.py` | modified | A.tracked_modified_files | merge_into_existing | dynamic_llm_l3_l4_protocol_refactor | It is a real protocol expansion, but overlaps with P0 candidate replay/provenance fields. Needs schema consolidation before commit. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/l3_l4_candidate_pooling.py` | modified | A.tracked_modified_files | separate_commit | dynamic_llm_l3_l4_protocol_refactor | Depends on candidate_protocol changes and untracked dynamic proposal fields; cannot be committed alone. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/l3_value_level_candidate_extractor.py` | modified | A.tracked_modified_files | uncertain_need_user_review | dynamic_llm_l3_integration_requires_decision | Tracked file now depends on untracked modules. It may be valid if dynamic LLM route continues, but it should not be committed until proposer/validator responsibilities are clarified against P0 replay/provenance. |
| `computer_use_poc/baselines/normal_baseline/l5_candidate_generation/l5_value_path_candidate_generator.py` | modified | A.tracked_modified_files | separate_commit | dynamic_llm_l4_l5_integration | Reasonable downstream propagation, but tied to candidate_protocol and dynamic LLM semantics. Commit with L3/L4 protocol changes only after review. |
| `computer_use_poc/baselines/normal_baseline/src/normal_baseline_enricher.py` | modified | A.tracked_modified_files | separate_commit | normal_baseline_enricher_hygiene | Small hygiene fix unrelated to dynamic LLM and P0 foundation. Can be a tiny standalone commit after targeted test review. |
| `computer_use_poc/baselines/normal_baseline/tests/fixtures/p0_5_discovery_only_candidates.json` | modified | A.tracked_modified_files / D.tests_fixtures | separate_commit | dynamic_llm_l4_l5_regression_tests | Fixture now encodes the high-commonality threshold used by modified L4/L5 logic. Commit with the protocol/test group, not alone. |
| `computer_use_poc/baselines/normal_baseline/tests/test_l5_value_path_candidate_generator.py` | modified | A.tracked_modified_files / D.tests_fixtures | separate_commit | dynamic_llm_l4_l5_regression_tests | Test aligns with modified L5 gate and should travel with L5/protocol changes. |
| `computer_use_poc/baselines/normal_baseline/tests/test_p0_5_discovery_only_regression.py` | modified | A.tracked_modified_files / D.tests_fixtures | separate_commit | dynamic_llm_l4_l5_regression_tests | Regression follows the protocol changes. Keep with protocol/L5 group after deciding dynamic LLM path. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/action_catalog_builder.py` | untracked | B.dynamic_LLM_broader_P1_1_untracked_modules | merge_into_existing | dynamic_llm_prompt_catalog_after_consolidation | Useful semantic catalog, but overlaps with P0 source/action coverage concepts. Prefer merging into a single source/action catalog rather than parallel metadata. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/code_assisted_commonality_runner.py` | untracked | B.dynamic_LLM_broader_P1_1_untracked_modules | keep_debug_only | none_now_debug_only | P0 replay/provenance already owns support/miss reproducibility. This may remain useful as an experimental proposal generator, but generated script/subprocess logic should not enter repo until pruned and bounded. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/commonality_proposal_validator.py` | untracked | B.dynamic_LLM_broader_P1_1_untracked_modules | merge_into_existing | dynamic_llm_validator_refactor | It overlaps strongly with candidate_replay_provenance and rule semantics. If retained, narrow it to proposal pre-validation and reuse P0 replay for support/miss. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/dennis_risk_semantic_lens.md` | untracked | C.docs_notes_prompts | uncertain_need_user_review | prompt_docs_dedup_review | There is also prompts/dennis_risk_semantic_lens.md. Pick one canonical location before committing. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/dynamic_llm_semantic_discovery_runner.py` | untracked | B.dynamic_LLM_broader_P1_1_untracked_modules | keep_historical_only | none_now_historical_or_experimental | P0-7 autonomous rerun now owns foundation-instrumented cold-start validation. This runner has hardcoded historical users/default paths and should not be committed as current capability without refactor. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/dynamic_prompt_builder.py` | untracked | B.dynamic_LLM_broader_P1_1_untracked_modules / C.docs_notes_prompts | uncertain_need_user_review | dynamic_llm_prompt_system_after_route_decision | Prompt assembly is useful only if dynamic LLM route is accepted. It depends on untracked prompts and action catalog. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/llm_commonality_proposer.py` | untracked | B.dynamic_LLM_broader_P1_1_untracked_modules | uncertain_need_user_review | dynamic_llm_proposer_experimental | It is a proposal preparation layer, not replay. Keep only if dynamic LLM proposal route continues; enforce no-real-call boundaries before commit. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/llm_commonality_proposer_prompt.md` | untracked | C.docs_notes_prompts | uncertain_need_user_review | dynamic_llm_prompt_system_after_route_decision | Do not commit prompts until dynamic LLM route and leakage policy are confirmed. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/llm_commonality_shadow_run.py` | untracked | B.dynamic_LLM_broader_P1_1_untracked_modules | keep_debug_only | none_now_debug_only | It duplicates P0 replay/provenance, rule semantics, audit/dedup, and report generation. Keep as debug/historical until split into smaller modules or deleted after confirmation. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/semantic_feature_schema.py` | untracked | B.dynamic_LLM_broader_P1_1_untracked_modules | merge_into_existing | schema_consolidation_before_dynamic_commit | Potentially useful long-term schema asset, but overlaps with candidate_protocol. Prefer merging into existing candidate schema/validation. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/action_family_prompts.yaml` | untracked | C.docs_notes_prompts | uncertain_need_user_review | dynamic_llm_prompt_system_after_route_decision | Overlaps with action_catalog_builder FAMILY_PROMPTS. Commit only after choosing canonical prompt/catalog representation. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/action_semantic_cards.yaml` | untracked | C.docs_notes_prompts | uncertain_need_user_review | dynamic_llm_prompt_system_after_route_decision | Likely duplicates action_catalog_builder cards and P0 source/action coverage concepts. Needs consolidation. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/base_blind_discovery_prompt.md` | untracked | C.docs_notes_prompts | uncertain_need_user_review | dynamic_llm_prompt_system_after_route_decision | Prompt assets should wait until leakage/overfit and dynamic LLM route are explicitly accepted. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/cross_source_discovery_prompt.md` | untracked | C.docs_notes_prompts | uncertain_need_user_review | dynamic_llm_prompt_system_after_route_decision | Cross-source chain logic overlaps with P0 replay/provenance chain reports. Keep out until prompt route is selected. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/dennis_risk_semantic_lens.md` | untracked | C.docs_notes_prompts | uncertain_need_user_review | prompt_docs_dedup_review | Duplicate semantic lens exists at l3_extraction/dennis_risk_semantic_lens.md. Choose one canonical copy. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/oracle_posthoc_evaluation_prompt.md` | untracked | C.docs_notes_prompts | uncertain_need_user_review | dynamic_llm_prompt_system_after_route_decision | Oracle must be final-eval-only; prompt asset should wait for dynamic route and leakage guard decision. |
| `computer_use_poc/baselines/normal_baseline/tests/test_dynamic_llm_semantic_discovery.py` | untracked | D.tests_fixtures | keep_for_next_commit | dynamic_llm_proposer_experimental_tests | It currently passes but depends on untracked dynamic modules and prompt files. Commit only with that module group. |
| `computer_use_poc/baselines/normal_baseline/tests/test_llm_commonality_proposer.py` | untracked | D.tests_fixtures | keep_for_next_commit | dynamic_llm_proposer_experimental_tests | It passes but spans many responsibilities. Keep only if dynamic LLM proposal stack is accepted; otherwise split tests by retained modules. |

## Dynamic LLM Judgement

- `dynamic_llm_semantic_discovery_runner.py`: Not needed for current P0 foundation. It overlaps with committed P0-7 autonomous rerun and contains historical defaults/hardcoded users. Keep only as historical/experimental unless refactored into a generic evaluator.
- `llm_commonality_proposer.py`: Overlaps partly with P0-7/P0-5 by building source groups and proposals, but does not replace replay/provenance. It should be a separate proposal layer if dynamic LLM route continues; enforce no-real-call boundaries.
- `code_assisted_commonality_runner.py`: P0 replay/provenance replaces support/miss validation. This file can be a debug/offline proposal generator, but should not be committed as core until the generated-script path is pruned or bounded.
- `commonality_proposal_validator.py`: Should be merged with or narrowed against candidate_replay_provenance/rule semantics. Keep only as LLM proposal pre-validator, not as a parallel replay engine.
- `semantic_feature_schema.py`: Potential long-term schema asset, but currently overlaps candidate_protocol. Merge into candidate_protocol/schema validation before committing.
- `prompts/**`: Do not commit now. Prompt assets need route confirmation, canonical lens location, and leakage/overfit policy before entering repo.
- `dynamic_tests`: test_dynamic_llm_semantic_discovery.py and test_llm_commonality_proposer.py pass together, but depend on untracked modules and modified tracked protocol files. They are not standalone.

## Tracked Modified Judgement

- `AGENTS.md`: Valuable runtime policy guard, but broad. Separate review/commit; do not roll into P0 or dynamic LLM.
- `runtime_case_execution_runner.py`: Related to raw contract export and future foundation input quality. Separate runtime commit after targeted tests and user confirmation.
- `README.md`: Dynamic LLM/L3 integration doc; commit with dynamic route only.
- `candidate_protocol.py`: Protocol expansion should merge with existing candidate schema and P0 provenance fields before commit.
- `l3_l4_candidate_pooling.py`: Depends on protocol changes; commit only with L3/L4 integration group.
- `l3_value_level_candidate_extractor.py`: Tracked file imports untracked dynamic modules; high dependency risk; needs route decision.
- `l5_value_path_candidate_generator.py`: L5 propagation and derived-feature high-gate; commit with L4/L5 protocol/test group only.
- `normal_baseline_enricher.py`: Small standalone defensive fix; can be separate hygiene commit after confirmation.
- `p0_5_discovery_only_candidates.json`: Fixture update tied to commonality_level/high threshold. Commit only with L4/L5 tests.
- `old_L5_P0_5_tests`: Align with protocol changes. Do not commit independently.

## Recommended Options

### Option A: Cleanup/delete obvious duplicate or debug-only files
- goal: Reduce worktree noise before deciding dynamic LLM route.
- includes: `duplicate Dennis semantic lens doc after canonical location chosen`, `debug-only large shadow/code-assisted runners if user decides not to pursue dynamic LLM route`
- excludes: `tracked runtime/L4/L5 changes`, `P0 committed files`, `profile lure committed docs`
- risk: Medium: deletion requires user confirmation because these may preserve historical experiment context.
- recommend_immediate: `false`

### Option B: Prepare dynamic LLM proposer as a separate P1.1 experimental commit
- goal: If dynamic LLM route continues, consolidate proposer, validator, prompts, schema, tests into a coherent experimental lane.
- includes: `llm_commonality_proposer.py`, `commonality_proposal_validator.py after narrowing`, `dynamic_prompt_builder.py`, `action_catalog_builder.py after source catalog merge`, `selected prompts/**`, `test_dynamic_llm_semantic_discovery.py`, `test_llm_commonality_proposer.py`
- excludes: `runtime_case_execution_runner.py`, `AGENTS.md`, `release/dist/full_runtime`, `debug-only shadow runner unless pruned`
- risk: High: current modules overlap P0 replay/provenance and include prompt/leakage concerns, though tests pass.
- recommend_immediate: `false`

### Option C: Handle tracked L4/L5/runtime old modifications separately
- goal: Split broad tracked changes into runtime raw-contract, protocol/L4/L5, and small baseline hygiene commits.
- includes: `runtime_case_execution_runner.py as one commit after tests`, `candidate_protocol.py/l3_l4/l5/tests/fixture as one protocol commit after consolidation`, `normal_baseline_enricher.py as small hygiene commit`
- excludes: `dynamic LLM prompts/runners until route is decided`, `AGENTS.md unless runtime policy review is explicitly desired`
- risk: Medium to high depending on file group. runtime_case_execution_runner.py is high blast radius.
- recommend_immediate: `false`

## Boundary

- Do not mix dynamic LLM modules into the committed P0 foundation history.
- Do not commit prompts until the dynamic LLM route, leakage policy, and canonical prompt/lens location are confirmed.
- Do not treat passing fixture tests as proof of runtime LLM capability; current modules state no real LLM is called by default.
- `/private/tmp/**` remains local validation output and should not enter repo.
