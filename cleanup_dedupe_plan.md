# Cleanup / Dedupe Plan

Scope: plan only. No deletion, code edit, git add, commit, platform access, Hive/DataAgent call, or release/dist/full_runtime refresh was performed.

## Overall Judgement

- `dynamic_llm_route_worth_retaining`: `yes_as_experimental_proposal_layer_only`
- route boundary: Keep proposal generation separate from P0 foundation, replay, provenance, rule semantics, parser drift, and profile lure registry. Do not claim runtime real LLM.
- overlaps with committed P0: `code_assisted_commonality_runner.py`, `commonality_proposal_validator.py`, `dynamic_llm_semantic_discovery_runner.py`, `llm_commonality_shadow_run.py`, `semantic_feature_schema.py`
- future L3 Agent brain assets: `llm_commonality_proposer.py`, `dynamic_prompt_builder.py`, `action_catalog_builder.py after catalog consolidation`, `dennis_risk_semantic_lens.md as canonical lens`, `selected prompt files after leakage review`
- debug or historical runners: `dynamic_llm_semantic_discovery_runner.py`, `llm_commonality_shadow_run.py`, `code_assisted_commonality_runner.py`

## Key Decisions

- `dynamic_llm_semantic_discovery_runner.py`: downgrade to `keep_debug_only`; do not commit as active capability. It overlaps P0-7 and has historical defaults.
- `code_assisted_commonality_runner.py`: `keep_debug_only`; P0 replay/provenance owns support/miss. Generated-script path should not enter core repo without pruning.
- `commonality_proposal_validator.py`: `merge_into_existing`; narrow to LLM proposal pre-validation or merge support/rule logic into existing replay/rule semantics.
- `semantic_feature_schema.py`: `merge_into_existing`; useful schema ideas but duplicates `candidate_protocol`.
- `prompts/**`: defer. Two YAML prompt catalog files and short prompt lens are delete candidates after canonical catalog/lens confirmation.
- `dennis_risk_semantic_lens.md`: keep as likely canonical long-term semantic lens.
- `llm_commonality_proposer.py`: keep as future L3 Agent brain proposal layer, not replay/provenance.

## File Plan

| file_path | suggested_action | overlaps | risk_if_kept | risk_if_deleted | reason |
|---|---|---|---|---|---|
| `computer_use_poc/baselines/normal_baseline/l3_extraction/action_catalog_builder.py` | `merge_into_existing` | P0 foundation | Medium: parallel source/action catalogs will drift and create contradictory family guidance. | Medium: dynamic_prompt_builder and dynamic_llm_semantic_discovery_runner depend on it; deleting requires deleting/refactoring those too. | Worth preserving as source/action semantic catalog, but it duplicates prompts/action_family_prompts.yaml and prompts/action_semantic_cards.yaml. Prefer one canonical catalog before commit. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/code_assisted_commonality_runner.py` | `keep_debug_only` | P0 foundation, candidate replay, candidate provenance, rule semantics, profile lure registry | High: embedded generated-script runner adds a second discovery/replay path and increases audit burden. | Low to medium: loses experimental code-assisted proposal path; no committed P0 capability depends on it. | Do not commit as core. P0 replay/provenance is the authoritative recomputation path; this is only useful as an experimental proposal generator if later pruned. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/commonality_proposal_validator.py` | `merge_into_existing` | P0 foundation, candidate replay, candidate provenance, rule semantics, profile lure registry | High unless narrowed: duplicate replay/rule validation paths can disagree with P0 candidate replay. | Medium: llm_commonality_proposer tests and l3_value_level_candidate_extractor LLM mode depend on it. | Keep only as LLM proposal pre-validator. Support/miss/rule-semantics should delegate to or align with candidate_replay_provenance rather than creating a parallel replay engine. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/dennis_risk_semantic_lens.md` | `keep_for_dynamic_llm_commit` | rule semantics, profile lure registry | Low if canonicalized; medium if duplicate prompt lens remains. | Medium: loses detailed semantic boundaries for future L3 Agent brain and prompt route. | This is the more complete semantic lens and is likely the canonical long-term doc if dynamic LLM/L3 Agent brain continues. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/dynamic_llm_semantic_discovery_runner.py` | `keep_debug_only` | P0 foundation, candidate replay, candidate provenance, rule semantics, parser drift, profile lure registry | High: creates a second autonomous discovery pipeline and may be confused with validated P0 foundation rerun. | Medium: loses earlier experimental runner and tests; safer after extracting any reusable generic helpers. | Downgrade to debug/historical. P0-7 autonomous rerun is now the trusted foundation-instrumented path; this runner has historical defaults and should not be committed as active capability. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/dynamic_prompt_builder.py` | `keep_for_dynamic_llm_commit` | profile lure registry | Medium: prompt assets can leak oracle or old-wave specifics unless guarded. | Medium: dynamic prompt tests and future prompt route lose assembly helper. | Useful if dynamic LLM proposer is retained. It is small and can be kept after prompt/lens canonicalization. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/llm_commonality_proposer.py` | `keep_for_dynamic_llm_commit` | P0 foundation, candidate replay, candidate provenance, rule semantics | Medium: real LLM preflight/import urllib increases perception of runtime LLM readiness; must clearly mark implemented_not_verified unless adapter is real and tested. | Medium to high: deletes the cleanest proposal-layer entrypoint for future L3 brain work. | This is the most defensible future L3 Agent brain component: proposal preparation, not validation/replay. Keep if dynamic LLM route continues, with strict no-real-call boundary by default. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/llm_commonality_proposer_prompt.md` | `uncertain_need_user_review` | profile lure registry | Medium: prompt drift and leakage risk; can be mistaken for production LLM behavior. | Low to medium: proposer can still build source groups; prompt can be recreated after route confirmation. | Prompt assets should not enter repo until dynamic LLM route, leakage policy, and prompt canonicalization are accepted. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/llm_commonality_shadow_run.py` | `keep_debug_only` | P0 foundation, candidate replay, candidate provenance, rule semantics | High: becomes a parallel orchestration path and increases maintenance cost significantly. | Medium: current test_llm_commonality_proposer imports a few helper/report functions; tests need split before deletion. | Too broad for repo as-is. It duplicates P0 replay/provenance/rule cleanup and mixes proposal generation, quality review, dedup, report writing, and L4/L5 visibility. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/semantic_feature_schema.py` | `merge_into_existing` | P0 foundation, candidate replay, candidate provenance, rule semantics | High if separate: two candidate schemas will diverge. | Medium: dynamic_llm_semantic_discovery_runner tests depend on it; schema concepts may be useful. | Potential long-term schema asset, but as a separate schema it duplicates candidate_protocol and committed P0 candidate fields. Merge into existing candidate schema if retained. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/action_family_prompts.yaml` | `delete_now` | profile lure registry | High: duplicate guidance will drift from action_catalog_builder. | Low: not currently read by code; can be recreated if external YAML catalog is preferred later. | Currently unreferenced by dynamic_prompt_builder and duplicates in-code FAMILY_PROMPTS in action_catalog_builder.py. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/action_semantic_cards.yaml` | `delete_now` | P0 foundation | High: duplicate action catalog source creates drift. | Low: not read by current code; future external catalog can be generated from canonical action catalog if needed. | Currently unreferenced and duplicates ACTION_CARDS in action_catalog_builder.py. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/base_blind_discovery_prompt.md` | `uncertain_need_user_review` | P0 foundation, candidate replay, rule semantics, parser drift, profile lure registry | Medium: prompt can go stale or reintroduce old-wave hints. | Medium: dynamic_prompt_builder tests and future prompt route depend on it. | Useful prompt asset but should be reviewed for leakage/overfit and updated to reference committed P0 foundation/registry instead of duplicating it. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/cross_source_discovery_prompt.md` | `uncertain_need_user_review` | candidate replay, candidate provenance, rule semantics | Medium: may duplicate P0 cross-source risk chain reporting. | Low: easy to recreate. | Small and potentially useful, but should wait for prompt route and cross-source chain ownership decision. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/dennis_risk_semantic_lens.md` | `delete_now` | profile lure registry | High: two semantic lenses will diverge and confuse prompt behavior. | Low: replace prompt builder reference with canonical lens if dynamic route continues. | Duplicate of the more complete l3_extraction/dennis_risk_semantic_lens.md. Keep one canonical lens and have dynamic_prompt_builder read it. |
| `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/oracle_posthoc_evaluation_prompt.md` | `uncertain_need_user_review` | candidate provenance | High: if accidentally fed into discovery, it contaminates autonomous proof. | Low: final eval can use non-prompt oracle protocols already documented. | Oracle prompt is leakage-sensitive. It should not be committed until final-eval-only guard is formalized. |
| `computer_use_poc/baselines/normal_baseline/tests/test_dynamic_llm_semantic_discovery.py` | `keep_debug_only` | P0 foundation, rule semantics | Medium: can create false confidence in an obsolete runner. | Medium: loses coverage for action catalog/prompt helpers unless split into smaller tests. | It passes, but validates the historical dynamic runner. Keep only while deciding whether to refactor/delete that runner. |
| `computer_use_poc/baselines/normal_baseline/tests/test_llm_commonality_proposer.py` | `keep_for_dynamic_llm_commit` | P0 foundation, candidate replay, candidate provenance, rule semantics | High if committed as-is: it locks in broad overlapping responsibilities and debug runner dependencies. | Medium: loses useful validator/proposer regression coverage. | It currently passes but is too broad. Keep only if dynamic LLM proposer stack is retained; split tests by retained module before commit. |

## Next Step Options

### A_delete_now_cleanup_list
- goal: Remove unreferenced duplicate prompt/catalog files after user confirms canonical source.
- include/delete candidates: `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/action_family_prompts.yaml`, `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/action_semantic_cards.yaml`, `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/dennis_risk_semantic_lens.md`
- not included/excluded: `llm_commonality_proposer.py`, `commonality_proposal_validator.py`, `dynamic_prompt_builder.py`, `tracked runtime/L4/L5 files`
- risk: Low to medium if canonical lens/catalog decision is made first; otherwise medium due accidental loss of prompt context.
- recommended_immediate: `false`

### B_dynamic_llm_proposer_minimal_commit
- goal: Prepare a minimal experimental proposal-layer commit without replay/provenance duplication.
- include/delete candidates: `llm_commonality_proposer.py`, `dynamic_prompt_builder.py`, `dennis_risk_semantic_lens.md`, `action_catalog_builder.py after catalog dedupe`, `commonality_proposal_validator.py only after narrowing to pre-validation`, `minimal proposer/validator tests split from current broad tests`
- not included/excluded: `dynamic_llm_semantic_discovery_runner.py`, `llm_commonality_shadow_run.py`, `code_assisted_commonality_runner.py generated script path`, `oracle_posthoc_evaluation_prompt.md unless final-eval-only guard exists`, `prompts/action_family_prompts.yaml`, `prompts/action_semantic_cards.yaml`
- risk: Medium-high until validator/replay responsibility is narrowed and prompt leakage guard exists.
- recommended_immediate: `false`

### C_pause_dynamic_llm_handle_tracked_runtime_l4_l5
- goal: Stop dynamic LLM cleanup work and separately address tracked runtime raw contract and L4/L5 protocol changes.
- include/delete candidates: `runtime_case_execution_runner.py raw observation contract group`, `candidate_protocol.py/l3_l4/l5/test fixture group after schema consolidation`, `normal_baseline_enricher.py small hygiene group`
- not included/excluded: `all untracked dynamic LLM modules/prompts/tests`
- risk: Medium; dynamic LLM files remain noisy but tracked production-adjacent changes get isolated.
- recommended_immediate: `true`

## Final Recommendation

- `can_delete_now`: `false`
- `delete_candidates`: `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/action_family_prompts.yaml`, `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/action_semantic_cards.yaml`, `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/dennis_risk_semantic_lens.md`
- `keep_for_next_commit`: `computer_use_poc/baselines/normal_baseline/l3_extraction/dennis_risk_semantic_lens.md`, `computer_use_poc/baselines/normal_baseline/l3_extraction/dynamic_prompt_builder.py`, `computer_use_poc/baselines/normal_baseline/l3_extraction/llm_commonality_proposer.py`, `computer_use_poc/baselines/normal_baseline/tests/test_llm_commonality_proposer.py`
- `user_review_required`: `computer_use_poc/baselines/normal_baseline/l3_extraction/llm_commonality_proposer_prompt.md`, `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/base_blind_discovery_prompt.md`, `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/cross_source_discovery_prompt.md`, `computer_use_poc/baselines/normal_baseline/l3_extraction/prompts/oracle_posthoc_evaluation_prompt.md`, `Before deleting duplicate prompts/lens, confirm canonical catalog/lens location.`, `Before committing llm_commonality_proposer.py, confirm dynamic LLM route remains desired.`, `Before deleting debug runners, confirm historical experiment context is not needed.`
- `recommended_next_action`: First confirm canonical lens/catalog choice, then delete only duplicate unreferenced prompt YAML/lens files; keep dynamic LLM proposer route paused until proposal-vs-replay responsibilities are narrowed.
