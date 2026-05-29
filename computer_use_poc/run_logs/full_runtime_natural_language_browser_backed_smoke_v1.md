# Full Runtime Natural Language Browser-Backed Smoke v1

Date: 2026-05-29

Scope: record the completed `outputs/full_runtime` natural-language bare-question
browser-backed smoke result. This is a post-run summary only. No test was rerun
while writing this file, and no platform source, Chrome profile, cookie, token,
session, header, `.ks_sso`, SSO runner, SmartSSOSession, DataAgent, or Hive was
accessed while writing this file.

## Test Question

```text
帮我看 user_id=2871834924 的账号安全证据，先不做最终定性
```

## Runtime

```yaml
runtime_dir: outputs/full_runtime
access_method: browser_backed_service
service: http://127.0.0.1:8787
case:
  user_id: "2871834924"
  case_type: single_user_account_security_evidence_card
  natural_language_bare_question: true
  final_risk_judgement_made: false
```

## Source Orchestration

```yaml
source_orchestration_check:
  validation_pass: true
  selected_access_method: browser_backed_service
  archives_stub_entered_main_chain: false
  sso_session_runner_called: false
  smart_sso_session_called: false
  dataagent_hive_called: false
```

## Browser-Backed Sources

```yaml
source_status_by_action:
  track_analysis_summary: completed
  rcp_snapshot: completed
  weapon_inventory: completed
  login_logs_search: completed
```

```yaml
track_analysis_account_security_bundle:
  source_status: completed
  sub_interfaces_completed:
    - profile
    - getUseDuration
    - getDeviceIds
    - getLastestDateTime
  sub_interfaces_missing: []
```

## Evidence Card

```yaml
evidence_card:
  evidence_card_completed: true
  sensitive_output: false
  final_risk_judgement_made: false
  completed_sources:
    - track_analysis_summary
    - rcp_snapshot
    - weapon_inventory
    - login_logs_search
  no_data_sources: []
  blocked_sources: []
  auth_failed_sources: []
  timeout_sources: []
  parse_error_sources: []
```

## Boundary

- The natural-language input was routed to account-security evidence observation.
- The runtime used browser-backed fixed actions instead of direct platform access.
- Archives stub did not enter the default main chain.
- `sso_session_runner` and SmartSSOSession were not called.
- DataAgent/Hive were not called.
- The answer did not make a final risk judgement.
- `sensitive_output=false`.

## Conclusion

```yaml
pass_conclusion: full_runtime controlled pilot ready
full_runtime_natural_language_browser_backed_smoke_pass: true
```
