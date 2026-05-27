# General Evidence Reasoning Contract Patch v1

## Goal

Generalize the issues exposed by the `62950989` live review into a Dennis Risk Agent wide reasoning contract. This patch is not ATO-only. It applies to account security, protocol attack, group control, anti-crawler, activity anti-cheating, traffic diversion, traffic anti-cheating, strategy attribution, and batch risk clustering.

## Triggering Problems

- A single source `no_data` was over-read as risk exclusion.
- Strategy hits were at risk of being treated as deterministic proof instead of cross-validation leads.
- New Hive / DataAgent / platform evidence could reverse the conclusion, but the response did not always force conclusion recomputation.
- Final answers were not consistently gated by evidence card, source quality, and routing metadata.
- Raw evidence, strategy hit, inference, counter evidence, and missing evidence were easy to mix in one narrative.

## New General Rules

- `no_data_not_risk_exclusion`: source `no_data` is a source state, not a no-risk counter-evidence item.
- `strategy_hit_not_final_judgement`: strategy hits, model scores, blacklist hits, and risk tags are leads, not final judgements.
- `raw_evidence_first`: raw behavior, entity relation, time sequence, and device/IP/action consistency have priority.
- `evidence_type_separation`: each evidence item must be typed as raw evidence, strategy hit, model score, inference, user claim, counter evidence, or missing evidence.
- `conclusion_recompute_after_new_evidence`: new evidence must trigger conclusion recomputation.
- `source_window_boundary`: each source must expose time-window and coverage limits.
- `partial_not_final`: incomplete / blocked / stale / timed-out sources can only support partial or insufficient conclusions.
- `template_hard_gate`: evidence-mode answers must include evidence card, source quality, and routing metadata.

## Modified Files

- `computer_use_poc/general_evidence_reasoning_contract_v1.md`
- `computer_use_poc/multi_entry_runtime_guard_v1.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/platform_call_playbook_index.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`
- Runtime summaries under `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/`

## Scenario Coverage

- Account security / ATO: login log `no_data`, user claim, strategy hit, and Hive pending result are not final proof.
- Protocol attack: missing interface logs, field absence, and a single abnormal field are not enough without request-shape and version evidence.
- Group control: device tags and model scores require account/device/IP/rhythm/relationship validation.
- Anti-crawler: QPS, UA anomaly, or one policy hit requires interface, entity aggregation, and normal-baseline validation.
- Activity anti-cheating: reward or strategy anomalies require register-active-task-reward-withdraw chain evidence.
- Traffic diversion: reports or one message/comment require relation and conversion-path validation.
- Traffic anti-cheating: exposure/click/conversion anomalies require source, placement, aggregation, path, and downstream-value checks.
- Strategy attribution: policy attribution explains event hit mechanics but is not final cheating judgement.
- Batch clustering: co-occurrence, top strategy, or shared infrastructure is only a lead until joined with current-batch evidence and denominator checks.

## Regression Added

- `GENERAL-NODATA-NOT-RISK-EXCLUSION-001`
- `GENERAL-STRATEGY-HIT-NOT-FINAL-JUDGEMENT-001`
- `GENERAL-NEW-EVIDENCE-RECOMPUTE-001`
- `GENERAL-EVIDENCE-TYPE-SEPARATION-001`
- `GENERAL-EVIDENCE-CARD-HARD-GATE-001`
- `GENERAL-PARTIAL-SOURCE-NOT-FINAL-001`
- `GENERAL-SOURCE-WINDOW-BOUNDARY-001`

## Not Done

- No real platform access.
- No DataAgent call.
- No gateway / safeBins / tools config change.
- No release package rebuild.
- No track-analysis runner addition.

## Validation Plan

- Parse `computer_use_poc/runtime_validation_cases_v1.yaml`.
- Compile touched Python if any local Python is included in the verification set.
- Check keyword coverage for the new contract and regression IDs.
- Run `git diff --check`.
