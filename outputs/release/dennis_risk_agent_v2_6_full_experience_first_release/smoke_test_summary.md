# Dennis Risk Agent v2.6 Full Experience-First Smoke Test Summary

## 1. Scope

This summary combines:

- v2.4 runtime-plus integration and routing smoke assets inherited from the base release.
- v2.6 experience-first golden case dry run.
- v2.6 User ↔ Device Entity Resolution text regression.

No real platform query was executed while assembling this package.

## 2. Experience Golden Case Dry Run

Source:

- `computer_use_poc/run_logs/user_experience_golden_cases_dry_run_001.md`

Covered cases:

1. ATO 用户研判：帮我看这个用户是不是被盗号。
2. 登录失败 / 被验证原因：这个用户为什么登录失败 / 被验证。
3. 设备风险补证：这个设备是不是群控 / root / hook / frida。
4. 用户关联设备查询：这个用户最近关联了哪些设备。
5. 设备关联用户查询：这个设备关联了哪些用户。
6. 策略命中解释：这个策略命中到底说明什么。

Dry run status:

- 6 case dry run completed.
- Device-risk case input completeness issue was corrected after dry run.
- Rule now enforced: Device SDK requires deviceId; if input is userId, run user-to-device entity resolution first; if unresolved, return `missing_device_id`.

## 3. Entity Resolution Regression

Source:

- `computer_use_poc/run_logs/entity_resolution_user_device_text_regression_run_v2_6_0.md`

Status:

- 10 cases.
- 10 pass.
- 0 fail.

Confirmed route boundaries:

- `userId + device risk` → user-to-device graphData → Device SDK.
- `userId + login flow` → user login unified log; no graphData / Device SDK.
- `deviceId + device risk` → Device SDK directly.
- `deviceId + related users` → device-to-user graphData.
- Too many candidates → top candidates / ask to narrow scope; no bulk deep query by default.

## 4. Full Package Integration Criteria

This full package is suitable for cloud internal Agent integration because it contains:

- v2.4 runtime-plus core files.
- ATO complete runtime body.
- DataAgent boundary files.
- Key readonly hand / computer_use_poc docs.
- Observation contract.
- Smoke tests.
- v2.6 experience-first files.

It still requires cloud-side verification before being treated as production behavior.

## 5. Priority Cloud Verification

P0:

- ATO user judgment real readonly flow.
- Login failure / verification reason real readonly flow.

P1:

- Device-risk input completeness with userId input.
- Strategy-hit explanation boundary.
- Entity resolution graphData auth / permission / no-data runtime branches.
