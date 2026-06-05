# v2.6 Full Experience-First Semi-Open Validation Summary

## 1. Run Status

```yaml
test_stage: v2.6_full_experience_first_semi_open
release_entry: outputs/release/dennis_risk_agent_v2_6_full_experience_first_release/
run_type: semi_open_validation_summary
real_platform_query_by_codex: false
new_platform_hand_added: false
real_read_logic_changed: false
dist_package_updated: false
git_commit_created: false
```

## 2. validation_timeline

- v2.6 full experience-first release 已集成，主入口为 `outputs/release/dennis_risk_agent_v2_6_full_experience_first_release/`。
- SSO state preflight 已通过。
- 登录失败 / 被验证原因解释真实只读回归已通过。
- Weapon `/apiv2/*` 调用路径已复核并修正此前错误的 `permission_blocked` 结论。
- Q3-Q8 半开放自测结果已进入本摘要，不合并日志摘要全文。

## 3. capability_status_matrix

| capability | status | note |
|---|---|---|
| `unified_login_log_check` | pass | `sso_session.py + GET /rest/unified/log/search` API direct read 稳定读取。 |
| `tianshi_strategy_hit_check / fastQueryHbase` | pass | `sso_session.py + GET /v2/rest/event/fastQueryHbase` 稳定读取。 |
| `archives_center_profile_check` | pass_but_browser_session_dependent | API direct read 可能 302；需 agent-browser recoverable_preflight + browser session 内 same-origin fetch / DOM read。 |
| `weapon graphData user_to_device` | api_pass_but_test_user_no_data | `no_data` 是当前图谱无结果 / 覆盖差异，不是 `permission_blocked`。 |
| `weapon graphData device_to_user` | pass | 移动端 did 可返回关联用户候选。 |
| `weapon riskData` | pass | 移动端 did 可返回设备侧标签。 |
| `tianshi eventList POST` | partial_todo | fastQueryHbase 可用；请求级详情需要封装 eventList POST。 |
| `frontend_activity_profile` | not_open_for_real_execution | 当前只保留 design / TODO，不作为半开放真实执行能力。 |

## 4. auth-state category_preflight_result

```yaml
sso_state_file: workspace/.ks_sso/sso-state.json
state_exists: true
covered_domains:
  - rcp
  - xz
  - weapon
  - track-analysis
  - rap
  - user-center-workbench
expired_cookie_detected: false
platform_specific_state_required_for_preflight: false
clarification:
  - archives_auth-state category.json / weapon_platform_auth-state category.json may be subset backups.
  - Missing platform-specific *_state.json must not be treated as full state loss.
```

## 5. real_readonly_validation_result

```yaml
login_failure_or_verify_reason: pass
unified_login_log_api: pass
tianshi_fastQueryHbase: pass
archives_center: pass_but_auth_session_risk
archives_execution_note:
  - archives center has APIs, but real execution depends on SSO + archives independent login / browser session.
  - if API direct read returns 302, use agent-browser recoverable_preflight.
  - after recoverable preflight, use same-origin fetch or DOM read inside logged-in browser session.
  - if still blocked, return auth_blocked / permission_blocked, not no_data.
```

## 6. semi_open_q3_q8_result

```yaml
Q3_strategy_hit_explanation:
  status: partial
  reason: fastQueryHbase works; eventList POST not packaged yet for request-level detail.
Q4_user_related_devices:
  status: partial
  reason: weapon user_to_device graphData API reachable; test user returned no_data, not permission_blocked.
  fallback_candidates:
    - unified login log device distribution
    - archives center recent login device
Q5_device_related_users:
  status: pass
  evidence: device_to_user via /apiv2/graphData works.
Q6_device_risk_evidence:
  status: pass
  evidence: Device SDK riskData via /apiv2/riskData works.
Q7_Q8_frontend_activity_related:
  status: not_open_for_real_execution
  reason: frontend_activity_profile remains design_only / TODO for semi-open stage.
```

## 7. weapon_apiv2_recheck_result

```yaml
path_correction:
  wrong_path: /anti-device/*
  correct_api_prefix: /apiv2/*
  correction: /anti-device/* blocked by AMC is UI path blocked / path_error, not Weapon API permission_blocked.
user_to_device:
  endpoint: /apiv2/graphData
  params: product=KUAISHOU, productName=KUAISHOU, groupKey=USER_ID, dimKey=DEVICE_ID, searchLevel=2
  status: api_pass_but_test_user_no_data
device_to_user:
  endpoint: /apiv2/graphData
  params: product=KUAISHOU, productName=KUAISHOU, groupKey=DEVICE_ID, dimKey=USER_ID, searchLevel=2
  status: pass
  sample_result: code=0, 3 nodes, 2 edges, 2 related candidate users
riskData:
  endpoint: /apiv2/riskData
  status: pass
  sample_findings:
    - no SIM card
    - APK launch count less than 10
    - phone system service Hook
    - frida=0
  boundary: Hook level=50 is high-severity device-side evidence but not final cheating / ATO conclusion.
```

## 8. key_corrections

- Weapon `/anti-device/*` blocked by AMC must not be recorded as Weapon API `permission_blocked`.
- Weapon core readonly calls should use `/apiv2/*`.
- `graphData no_data` means current Weapon graph has no result under that query condition; it does not prove no relationship exists.
- `user_to_device no_data` must not be written as “user has no devices”.
- Archives center should not be described as fully unavailable or pure HTTP API direct read.
- Device-side tags and graph relations are evidence / leads, not final conclusions.

## 9. current_semi_open_scope

1. 登录失败 / 被验证原因解释。
2. 策略命中解释。
3. ATO 用户研判。
4. 用户关联设备查询。
5. 设备关联用户查询。
6. 设备风险补证。

## 10. still_limited_capabilities

- `eventList POST`: partial / TODO for request-level detail.
- `frontend_activity_profile`: not open for real execution.
- Archives center: usable, but browser-session-dependent and must declare auth/session risk in Plan.
- Batch queries: not allowed in this stage.
- DataAgent / Hive: not default; only for explicit offline aggregate / long-window tasks.

## 11. next_todos

- Package eventList POST via agent-browser same-origin fetch or an independent POST script.
- Add semi-open regression for archives center recoverable_preflight failure branches.
- Add real no_data / auth / permission runtime samples for Weapon graphData.
- Keep frontend_activity_profile as TODO until real execution is explicitly reopened.
