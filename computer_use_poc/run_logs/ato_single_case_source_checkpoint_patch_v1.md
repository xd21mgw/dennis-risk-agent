# ATO Single Case Source Checkpoint Patch v1

## Scope

This run records a local-only patch for Dennis Risk Agent ATO single-case execution orchestration.

The live follow-up showed that `user_id=290534602` correctly entered `single_entity_execution_mode` and successfully completed unified login log observation, but later RCP / archives browser work consumed the whole 3 minute budget. The completed login evidence was lost because source checkpoints were not preserved into a partial evidence card.

## Boundaries

- Real platform access: no.
- DataAgent call: no.
- Auth / gateway change: no.
- Real query execution: no.
- Release package rebuild: no.
- Live workspace overlay: no.
- Git commit / push: no.

## Fix Summary

### Per-source checkpoint

Each source must emit a checkpoint immediately after completion or failure:

- `source_name`
- `source_type`
- `source_status`: completed / no_data / blocked / auth_failed / timeout / parse_error / skipped
- `evidence_summary`
- `evidence_time_range`
- `source_quality`
- `raw_reference_safe_id`
- `collected_at`
- `failure_reason`
- `next_source_decision`

Completed source evidence must not be lost when a later source fails. `no_data` is still a completed source but must be marked `no_data_not_risk_exclusion`.

### Source priority

P0:

- Unified login log.
- Weapon riskData / graphData.
- Tianshi strategy hit summary.

P1:

- Archives profile.
- Track-analysis stats-first.

P2:

- RCP browser.
- Archives browser recoverable_preflight.
- Track-analysis SPA detail.

P2 browser sources must not block output after a P0/P1 source has completed.

### Overall deadline

- Default total budget: 180s.
- If any P0/P1 source completed, stop extending P2 browser sources at the 120s or 150s checkpoint.
- Emit partial evidence card before the overall timeout.
- Browser source failures are recorded as `timeout_sources`, `blocked_sources`, or `auth_failed_sources`.

### Partial evidence card

Required fields:

- `case_id`
- `user_id`
- `final_status: partial`
- `conclusion_state`
- `completed_sources`
- `no_data_sources`
- `blocked_sources`
- `auth_failed_sources`
- `timeout_sources`
- `parse_error_sources`
- `missing_evidence`
- `source_quality`
- `strong_evidence`
- `medium_evidence`
- `weak_evidence`
- `counter_evidence`
- `caveats`
- `next_action`

Boundary:

- `no_data`, `timeout`, `blocked`, and `auth_failed` are not counter evidence.
- User claim is not strong evidence.
- Browser timeout means only that the source was unavailable.

### Observation logging

Execution must write an observation skeleton before source work begins:

- `user_prompt`
- `routing_mode`
- `execution_mode`
- `final_status=running`
- `started_at`
- `subagent_session_id`
- `main_session_id`

Every source checkpoint should append or update observation. Final timeout must still leave an observation record with source lists and `partial_reason`.

## Regression Added

- `SINGLE-ATO-SOURCE-CHECKPOINT-001`
- `SINGLE-ATO-OVERALL-DEADLINE-001`

## Modified Files

- `AGENTS.md`
- `computer_use_poc/multi_entry_runtime_guard_v1.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/capability_registry.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/runtime_integration_validation_checklist_v1.md`
- `computer_use_poc/smoke_tests.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/account_security_runtime_summary_v1.md`

## Validation Plan

- YAML parse for `computer_use_poc/runtime_validation_cases_v1.yaml`.
- Keyword coverage for checkpoint / deadline / source priority / regressions.
- `git diff --check`.

## Remaining Runtime Work

Cloud runtime still needs to overlay or sync these workflow guardrails, then rerun:

- `user_id=290534602` ATO single-case path.
- Weapon auth_required / timeout source.
- RCP / archives browser timeout source.
- Observation skeleton and partial metadata output.
