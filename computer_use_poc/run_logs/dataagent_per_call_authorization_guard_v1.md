# DataAgent Per-call Authorization Guard v1

## Goal

Fix the authorization boundary for DataAgent / Hive execution. Realtime readonly API sources can run automatically when required fields are complete, but DataAgent / Hive execution requires explicit user confirmation for every query.

## Reason

Live testing showed that the agent could treat an earlier "查吧 DataAgent" as permission to continue later Hive queries. That is not acceptable. DataAgent / Hive is higher-cost and broader-scope than realtime readonly API sources, so confirmation is per call, not session-wide.

## Rules Added

- Every DataAgent / Hive execution requires explicit confirmation.
- Every new SQL requires confirmation.
- Every new table requires confirmation.
- Every new time window requires confirmation.
- Every new problem or evidence direction requires confirmation.
- Follow-up messages such as "继续查", "再查一下", "看设备活跃", or "查同设备其他账号" still require a new confirmation if they require DataAgent / Hive.

## Allowed Without Confirmation

- Generate a DataAgent query plan.
- Generate recommended SQL.
- Recommend tables and fields.
- Summarize returned DataAgent / Hive results.
- Analyze existing Hive results.

## Output Contract

Before execution, output:

- why DataAgent / Hive is needed
- recommended table
- query scope
- time window
- question to answer
- estimated cost / scan risk when relevant
- explicit confirmation request

## Modified Files

- `computer_use_poc/multi_entry_runtime_guard_v1.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/platform_call_playbook_index.md`
- `computer_use_poc/approval_policy.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`

## Regression Added

- `DATAAGENT-PER-CALL-AUTHORIZATION-001`
- `DATAAGENT-FIRST-CONSENT-NOT-SESSION-WIDE-001`
- `DATAAGENT-FOLLOWUP-STILL-REQUIRES-CONFIRMATION-001`
- `REALTIME-API-AUTO-BUT-DATAAGENT-CONFIRM-001`

## Not Done

- Did not access real platforms.
- Did not call DataAgent.
- Did not modify gateway / safeBins / tools.
- Did not repackage release.
