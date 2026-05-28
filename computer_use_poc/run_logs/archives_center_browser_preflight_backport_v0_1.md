# Archives Center Browser Preflight Backport v0.1

## Background

Internal Agent live validation for `ARCHIVES-CENTER-BROWSER-ACTIVATION-PREFLIGHT-001` passed and needed to be backported into the mother-body contracts.

Validated result:

- `recoverable_preflight=completed`.
- Browser state was valid and directly entered Archives SPA.
- No SSO / `account.p` middle page appeared.
- No account identifier input or next-step click was triggered.
- Profile page was reachable.
- Publish-chain / 视频作品集 tab was visible.
- Seven video works were visible.
- Visible fields included video ID, upload time, play count, comment count, like count, collect count, and status.
- No credential material was output.
- DataAgent / Hive was not called.
- No full business judgement was performed.

## Backported Rules

- Archives user analysis remains ATO P0 account baseline source.
- Abnormal publish / non-owner publish / traffic-diversion content keeps publish-chain as P0-conditional.
- Preferred SPA entry is `/frontend/archives/index.html#/archives/user/profile?userId={userId}`.
- `/admin/search/user?keyword={userId}` can be wrong-entry AMC/IP blocked and must not be treated as platform unavailable.
- `profile_reachable=true` can complete the account baseline source.
- `publish_chain_visible=true` can complete the abnormal-publish P0-conditional source.
- Missing publish device is `missing_evidence`, not publish-chain unavailable.
- Archives timeout is `archives_browser_timeout`, not `auth_failed`.

## SPA Tab Fallback

- `.ks-tabs__item` accessible click by browser ref may not trigger Vue / ks-tabs tab switching.
- The adapter should try accessible click once.
- If selected state does not change, use DOM eval click by text content and call `HTMLElement.click()`.
- If still failed, try URL hash / route navigation if the contract contains a registered route.
- If still failed, mark `tab_switch_failed`, not source unavailable.

## Files Updated

- `computer_use_poc/platform_access/archives_center_contract_v0_1.yaml`
- `computer_use_poc/platform_access/browser_same_origin_adapter_contract_v0_1.md`
- `computer_use_poc/platform_access/failure_taxonomy_v0_1.yaml`
- `computer_use_poc/platform_access/observation_schema_v0_1.yaml`
- `computer_use_poc/source_orchestration_plan_v1.yaml`
- `computer_use_poc/platform_call_playbook_index.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`

## Validation Cases

- `ARCHIVES-CENTER-BROWSER-ACTIVATION-PREFLIGHT-001`
- `ARCHIVES-CENTER-PUBLISH-CHAIN-TAB-FALLBACK-001`
- `ARCHIVES-CENTER-WRONG-ENTRY-NOT-PLATFORM-BLOCKED-001`

## Boundaries

- Did not access real platforms.
- Did not call DataAgent or Hive.
- Did not modify auth, gateway, safeBins, or TOOLS.
- Did not output or save cookie/token/session/header/password.
- Did not rebuild a package or full release.
- Did not commit git changes.

