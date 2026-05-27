# No Live Auth Repair In Business Case Guard v1

## Goal

Add a minimal runtime guard and output template to prevent business case execution from repairing platform authentication state in-line.

This patch responds to the KNC Q1 self-test issue where Archives Center / admin source redirected to `account.p`, then the agent continued clicking login UI, typing content, guessing API paths, and guessing URLs inside the business case.

## Scope

Updated:

- `computer_use_poc/multi_entry_runtime_guard_v1.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`

Added:

- `computer_use_poc/run_logs/no_live_auth_repair_in_business_case_guard_v1.md`

## Rule Summary

In KNC case execution, single-user account security execution, small batch execution, batch execution, and normal user risk investigation:

- Login page / SSO page / `account.p` page / HTML login response / auth failed / permission blocked / path error must stop that source within 30 seconds.
- The source becomes `auth_session_issue` or `source_gap`.
- The source is written to `remaining_source_gaps`.
- Completed P0 evidence card output must not be blocked.
- The gap must not be treated as low-risk / no-risk counter evidence.

Forbidden in business case execution:

- Click login page.
- Type username / account.
- Complete SSO interactively.
- Guess URL / domain / API path.
- Search historical sessions for URL.
- Debug cookie / session / header.
- Repair auth state for a conditional source.

Archives Center special rule:

- Confirmed entry: `admin.p.adm-corp.kuaishou.com`.
- If redirected to `account.p.adm-corp.kuaishou.com`, mark `archives_auth_session_issue`.
- Do not click "next" / "下一步" in business case.
- "下一步" is only allowed in a separate auth activation task.

## Regression

- `ARCHIVES-AUTH-IN-CASE-NO-LIVE-FIX-001`

## Boundaries

- No real platform access.
- No DataAgent / Hive call.
- No gateway / safeBins / tools change.
- No runner / routing / validator code change.
- No release packaging.
