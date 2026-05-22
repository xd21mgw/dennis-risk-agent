# Dennis Risk Agent Semi-open Release Manifest Patch Plan v1

This is a plan only. It does not update `outputs/release` or `outputs/dist`.

## 1. Files to Update During Actual Packaging

When the user explicitly requests actual packaging, update or create:

- `outputs/release/<release_name>/README.md`
- `outputs/release/<release_name>/dennis_risk_agent_<release_name>_manifest_v1.md`
- `outputs/final/final_package_manifest.md`
- release snapshot under `outputs/final/` if the release line already uses snapshots

Do not update these files in this readiness review round.

## 2. README Patch Requirements

The release README should state:

- This is a full-scenario semi-open test package.
- It is not ATO-only.
- ATO is the deep sample capability.
- Non-ATO scenarios are formal expert cognition and evidence planning capabilities.
- DataAgent is plan-only by default and is not a universal data substrate.
- question_collection records candidate learning signals but does not automatically modify brain or release.
- Safety guardrails and asset extraction guard are part of runtime boundary.

## 3. Manifest Patch Requirements

Manifest sections should include:

1. Runtime entry / user guide.
2. Full-scenario capability registry.
3. Scene routing.
4. Response templates and evidence contracts.
5. ATO deep sample.
6. Non-ATO runtime summaries:
   - anti-crawler
   - protocol attack
   - group control / device risk
   - account farm / small-account matrix
   - activity anti-cheating
   - traffic anti-cheating
   - traffic diversion
   - cracked app / plugin risk
7. Evidence card / plan mode / strategy recommendation.
8. DataAgent boundary and query plan examples.
9. Safety / asset extraction guard.
10. question_collection.
11. Runtime validation cases.
12. Smoke test / manifest summary.

## 4. question_collection Mapping

Map:

```text
computer_use_poc/question_collection/
→ outputs/release/<release_name>/question_collection/
```

Manifest wording:

```yaml
question_collection:
  scope: full_scenario_user_question_observation
  purpose:
    - learning_candidate_queue
    - user_feedback_capture
    - quality_risk_signal_capture
    - human_review_entry
  schema_layers:
    - agent_observed
    - agent_suggested
    - reviewer_final
  reviewer_decision_default: pending
  boundaries:
    - not_ato_only
    - no_auto_brain_update
    - no_auto_release_update
    - no_auto_dataagent_call
    - no_sensitive_credential_recording
```

## 5. Full-scenario Runtime Summary Manifest Rule

Full-scenario runtime summaries must be listed as formal semi-open capabilities.

Do not list non-ATO summaries under an ATO appendix.

Minimum:

- `anti_crawler_runtime_summary_v1.md`
- `protocol_attack_runtime_summary_v1.md`
- `group_control_runtime_summary_v1.md`
- `activity_anti_cheating_runtime_summary_v1.md`
- `traffic_anti_cheating_runtime_summary_v1.md`
- `traffic_diversion_runtime_summary_v1.md`
- `cracked_app_runtime_summary_v1.md`
- account farm / black-market matrix selected templates or closure summary

## 6. DataAgent Boundary Manifest Rule

Manifest must say:

- DataAgent is mainly for Hive / company warehouse data analysis.
- It is not a universal risk-control backend.
- Non-ATO does not call DataAgent by default.
- DataAgent execution requires explicit user confirmation / authorized environment.
- Semi-open package can generate DataAgent / Hive query plans.

## 7. Final Package Manifest Patch

`outputs/final/final_package_manifest.md` should record:

- release name
- package type: full-scenario semi-open test
- include set
- exclusion list applied
- package scanner result
- no credential assets included
- no full historical run logs
- question_collection included as pending-review learning candidate module

## 8. Snapshot Guidance

If the release line maintains snapshots, create a new snapshot rather than overwrite old ones.

Suggested name:

```text
outputs/final/dennis_risk_agent_<release_name>_semi_open_snapshot.md
```

## 9. Packaging Gate

Do not build `outputs/dist` until:

- filelist candidate is reviewed
- exclusion list is applied
- package scanner passes or warnings are accepted
- audience-scope field policy is confirmed
- user explicitly asks for packaging
