# Browser Same-Origin Adapter Contract v0.1

Some platform APIs are confirmed only when the browser is already on the correct origin and the user's environment has a valid platform state. This adapter contract keeps those cases structured without turning business execution into auth repair or URL exploration.

## Scope

- Applies to Archives Center, RCP/eventList, track-analysis, and other registered same-origin APIs.
- The project does not carry auth state. It only defines how to execute if the user's browser/profile/state is ready.
- Same-origin access is an `access_method`, not proof that a source is lower priority.

## Allowed

- Use a registered entry domain and registered API path.
- Verify current origin before fetch.
- Perform readonly same-origin API requests for registered contracts.
- Return `platform_access_observation` with `invocation_method=browser_same_origin`.
- Classify HTML/login page, redirect, AccessProxy, path block, or parse errors as structured source states.

## Forbidden

- Guess domains or paths.
- Click login pages in business cases.
- Type username, password, SMS, QR, or MFA in business cases.
- Debug cookie/session/header material.
- Treat same-origin failure as no-data.
- Treat one blocked path as whole-platform unavailable.

## Failure Mapping

- Wrong origin: `same_origin_mismatch`.
- API requires browser origin but runner/direct call was attempted: `same_origin_required`.
- Registered path permission blocked: `api_path_permission_blocked`.
- Some paths work while others fail: `platform_partial_available`.
- HTML/login page after valid same-origin setup: `auth_failed` or `accessproxy_session_invalid`.

## Archives Center SPA Tab Interaction

`archives_spa_tab_interaction` covers Archives Center Vue / ks-tabs pages where accessible click references do not always trigger the SPA state change.

Issue:

- `agent-browser click @ref` may not trigger Vue or `.ks-tabs__item` switching.

Affected UI:

- `.ks-tabs__item`
- Archives Center 视频作品集 tab

Preferred sequence:

1. Try accessible click once.
2. If selected state does not change, use DOM eval click.
3. If still failed, try URL hash or route navigation when the contract has a registered route.
4. If still failed, mark `tab_switch_failed`, not source unavailable.

Allowed eval action:

- Find the tab element by text content.
- Call `HTMLElement.click()`.

Stop conditions:

- No matching tab element.
- Repeated click with no selected-state change.
- SPA route loop.
- Permission page.
- Timeout.

Output statuses:

- `tab_switch_completed`
- `tab_switch_failed`
- `publish_chain_visible`
- `publish_chain_missing`

Boundary:

- Do not output cookie/token/session/header/password.
- Do not perform write operations.
- Do not make a business risk judgement inside the adapter.
- Do not mark Archives source unavailable just because tab click by ref failed.

Account identifier / activation rules:

- `current_user_account_identifier` may come from the current user environment or current conversation.
- Dennis environment example `muguangwu` is an example only; `do_not_hardcode_for_other_users`.
- `if_prefilled`: reuse the prefilled value.
- `fill_account_identifier_if_empty`: allowed only in a separate auth activation task, not inside business execution.
- `click_next_or_continue_once`: allowed only in a separate auth activation task.
- QR / MFA / password / captcha / SMS means `user_manual_action_required`.
- In business case execution and recoverable preflight, do not wait for manual action. Mark the source `user_manual_action_required`, write source quality, and continue partial evidence.
- Only a dedicated auth activation task may briefly wait for user manual action.
- Permission page means `permission_blocked`.
- Repeated activation loop means `activation_loop_detected`.
