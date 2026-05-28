# Plan-only Diagnostic Rubric and Gate Patch v1

## Purpose

Add a lightweight diagnostic framework so Dennis Risk Agent capability issues are not debugged by guessing after a single failed case. The framework separates:

- `config/runtime`
- `intent/routing`
- `source_orchestration`
- `evidence_reasoning`
- `output_contract`

## Files Changed

- `computer_use_poc/plan_only_diagnostic_rubric_v1.md`
- `computer_use_poc/failure_triage_card_template_v1.md`
- `computer_use_poc/multi_entry_runtime_guard_v1.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/capability_registry.md`
- `computer_use_poc/platform_call_playbook_index.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`

## Rules Added

- Plan-only diagnostics validate route/source design but do not prove runtime config, auth, safeBins, or platform availability.
- Plan-only output still requires `routing_metadata` with `execution_mode=plan_mode_only`, `platform_called=false`, `dataagent_called=false`, and `reason_not_executed`.
- Execution output requires `evidence_card`, `source_quality`, and `routing_metadata`.
- DataAgent/Hive must be authorized per call; insufficient P0/P1 evidence does not grant automatic Hive execution.
- Browser is not a P0 default source when API runner / API direct can answer.
- Explicit strategy-hit questions must treat strategy hit as an explicit target source.
- Strategy hit is not final ATO / cheating judgement.
- no_data / blocked / timeout / auth_failed are source quality states, not no-risk proof.

## Regression Added

- `PLAN-DIAG-SINGLE-ATO-POLICY-HIT-001`
- `PLAN-DIAG-SMALL-BATCH-MIXED-ATO-001`
- `PLAN-DIAG-STRATEGY-RECOMMENDATION-OAUTH-001`
- `FAILURE-TRIAGE-CARD-TEMPLATE-001`

## Boundaries

- Did not access real platforms.
- Did not call DataAgent or Hive.
- Did not modify auth, gateway, safeBins, or TOOLS config.
- Did not repackage release or overlay artifacts.
- Did not submit git changes.
