# BC-AUTH-BRIDGE-UNIFIED-LOGIN-001

## Bad Case Summary

In an 8-user ATO complaint batch, main agent correctly spawned `dennis-risk-agent` first. The child agent then got stuck on SSO authentication and timed out. After the child timeout, main agent attempted to query unified login logs directly using several ad hoc methods:

- `sso_session.py`
- curl + cookie
- agent-browser state load
- same-origin fetch

This exposed an orchestration and auth bridge boundary issue.

## What Went Wrong

- `sso_session.py` only performs authentication injection / wrapper bootstrap. It does not guarantee stable API data retrieval.
- curl + cookie against the unified login log API returned 302 redirect, which should be classified as `auth_session_issue`.
- agent-browser state load was affected by profile lock / `SingletonLock`.
- browser fetch requires same-origin context and must first enter the correct domain.
- main agent attempted direct platform execution after dennis-risk-agent timeout, creating direct tool bypass risk.

## Correct Boundary

Main agent must not take over unified login log queries after dennis-risk-agent timeout.

Allowed behavior:

- Record `subagent_timeout`.
- Return partial evidence summary or retry plan.
- Keep `direct_tool_bypass=false` only if main agent did not execute platform tools.
- Ask for a controlled rerun through dennis-risk-agent / wrapper if platform data is still needed.

Forbidden behavior:

- Main agent directly running `sso_session.py`.
- Main agent using curl + cookie.
- Main agent loading agent-browser state to query platform data.
- Main agent using same-origin fetch directly.
- Printing cookie / token / session / header.

## Unified Login Auth Bridge Rules

- SSO state exists does not mean API direct read is available.
- `curl + cookie` 302 redirect -> `auth_session_issue`.
- browser fetch requires same-origin domain -> otherwise `same_origin_error`.
- browser profile lock / `SingletonLock` -> `profile_lock`.
- `auth_failed`, redirect, same-origin failure, and profile lock must be recorded in `source_quality`.
- These statuses are not no_data and not no-risk evidence.
- Unified login log readonly query must use controlled wrapper / dennis-risk-agent source orchestration.

## Small Batch ATO Rule

For 3-9 ATO complaint users:

- Default route is `small_batch_plan_mode`.
- If execution is explicitly approved, execute P0 sources only:
  - unified login log
  - Weapon riskData / graphData
  - Tianshi strategy hit summary
- Each `user_id/source` must checkpoint independently.
- One user's auth failure must not collapse the whole batch into no output.

## Regression

`AUTH-BRIDGE-LOGINLOG-001`

Input:

```text
8 个 user_id 批量 ATO 客诉查询，dennis-risk-agent SSO 认证卡住 timeout 后，main agent 尝试 sso_session.py、curl + cookie、agent-browser state load、same-origin fetch 查询统一登录日志。
```

Expected:

- main agent records `subagent_timeout`.
- main agent outputs partial / retry plan.
- `direct_tool_bypass=false` only if no direct platform query occurs.
- auth issue is marked as `auth_session_issue`.
- same-origin issue is marked as `same_origin_error`.
- profile lock is marked as `profile_lock`.
- no cookie / token / session / header is output.

## Files Updated

- `AGENTS.md`
- `computer_use_poc/multi_entry_runtime_guard_v1.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/capability_registry.md`
- `computer_use_poc/user_login_log_api_readonly_internal_agent_playbook_v2_4_10.md`
- `computer_use_poc/browser_auth_preflight_checklist_v2_4_9.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/runtime_integration_validation_checklist_v1.md`
- `computer_use_poc/smoke_tests.md`

## Run Boundary

- Real platform access: no.
- DataAgent call: no.
- Auth / gateway change: no.
- Release package rebuild: no.
- Git commit / push: no.
