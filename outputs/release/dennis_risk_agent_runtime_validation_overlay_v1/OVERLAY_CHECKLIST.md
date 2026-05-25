# Overlay Checklist v1

## Before overlay

- Confirm this package is used as a runtime overlay, not a major release.
- Confirm no real platform access is needed for validation.
- Confirm DataAgent is not called during validation.
- Confirm auth and gateway files are not modified.
- Confirm full domain skill source is not copied.
- Confirm template feedback queue is not used as live runtime output.
- Run release preflight against this overlay directory.

## After overlay

- Verify KIM/webchat risk questions spawn Dennis Risk Agent.
- Verify non-risk coding tasks still use direct main-agent execution.
- Verify follow-up prompts such as `查一下吧` / `继续` / `看下` inherit previous context only when the batch fingerprint is unchanged.
- Verify a new batch id, entity set, time window, or risk domain starts fresh context.

## Feedback writer validation

- Validate `feedback_record` append behavior with a safe synthetic record.
- Validate `linked_previous_record_id` is passed by the live caller after a real KIM follow-up.
- Validate high-value feedback enters `runtime_logs/question_collection/question_learning_candidate_queue_v1.csv`.
- Validate generic useful feedback does not enter the candidate queue by default.
- Validate the template queue under `computer_use_poc/question_collection/` is not mutated by live traffic.

## Evidence quality validation

- Validate evidence type separation: facts, behavior events, user claims, inference, hypothesis, and missing evidence.
- Validate single-case evidence card contains completed, blocked, timeout, and missing source fields.
- Validate `no_data`, timeout, blocked, and partial source states are treated as source gaps, not no-risk proof.
- Validate `BC-HARMONY-ATO-001` does not collapse Harmony or OAuth takeover into credential stuffing.

## Batch clustering validation

- Prompt: `这 10 个用户像不像一批 ATO？`
  - Expected: `batch_clustering_mode`, no one-by-one online execution.
- Prompt: mixed positive and negative case summaries.
  - Expected: layered clusters, not one forced risk class.
- Prompt: multi-device / multi-IP / multi-version / nickname mutation batch.
  - Expected: abnormal correlation matrix with direction and evidence boundary.
- Missing denominator or sample bias.
  - Expected: `denominator_status` marks the gap and no strong enrichment claim is made.
- Correlation without join key.
  - Expected: `cannot_conclude_boundary` states why same-source judgement cannot be made.
- Strategy recommendation or expansion request with attached ids.
  - Expected: plan mode, no platform call, DataAgent/Hive only as later plan.

## Track-analysis and browser downgrade validation

- Validate track-analysis starts with stats-first planning.
- Validate browser or SPA loop stops after 3 failed attempts.
- Validate blocked browser, 2FA, HTML auth page, and parse failure produce a partial evidence card.

## Asset preflight validation

- Run:

```bash
python3 computer_use_poc/release_preflight_check.py outputs/release/dennis_risk_agent_runtime_validation_overlay_v1
```

- Expected:
  - `preflight_pass=true`
  - `package_should_block=false`
  - safe summary only

## Rollback validation

- Confirm a pre-overlay snapshot exists.
- Confirm rollback restores only overlaid runtime files.
- Confirm append-only runtime logs are not rewritten.
- Confirm auth, browser state, and gateway state are not touched.

