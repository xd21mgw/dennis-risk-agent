# Archives Auth Recovery Username Prefill v1

## Purpose

Codify the Archives Center auth recovery behavior observed in the recent successful recovery flow without changing gateway, safeBins, tools, runner logic, or live auth state.

## Background

During Archives Center supplement, the agent saw `account.p.adm-corp.kuaishou.com` and initially treated the condition as possible IP authorization / auth blocker. After the user provided `username=muguangwu`, the agent filled the username, clicked "下一步", the user completed employee SSO, `archives_auth-state category.json` was saved, and state reload later reached the Archives SPA. Same-origin fetch to `/archives/user/home/info?userId=642202874` returned HTTP 200 with `hasData=true`.

## Rules Added

- `account.p.adm-corp.kuaishou.com` login page is not by itself IP whitelist failure.
- Username prefill and "下一步" are allowed only in a separate `archives_center_auth_activation_fix` / platform auth activation task, not inside KNC, single-user, or batch business case execution.
- If the username input is the only visible field and username is known, prefilled, or already provided in the conversation, use it without asking again.
- If password, QR, SMS, or MFA appears after the username step, pause for user manual completion.
- After user SSO completion, save `archives_auth-state category.json` and perform a health check:
  - close browser
  - state load `archives_auth-state category.json`
  - open Archives user home page
  - confirm no login redirect
  - same-origin fetch `/archives/user/home/info?userId=...`
  - require HTTP 200 and `hasData=true`
- Expired `archives_auth-state category.json` maps to `auth-state category_expired` / `manual_sso_required`, not agent IP failure.
- Do not output cookie, token, session, header, or auth state details.

## Regression Added

- `ARCHIVES-AUTH-USERNAME-PREFILL-001`
- `ARCHIVES-AUTH-STATE-EXPIRED-NOT-IP-BLOCK-001`
- `ARCHIVES-AUTH-HEALTH-CHECK-001`

## Files Updated

- `computer_use_poc/browser_auth_preflight_checklist_v2_4_9.md`
- `computer_use_poc/platform_call_playbook_index.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`

## Boundaries

- Did not access the real platform.
- Did not call DataAgent or Hive.
- Did not modify gateway, safeBins, or tools.
- Did not modify `sso_session_runner.py`.
- Did not repackage release or overlay artifacts.
- Did not save or output sensitive auth material.
