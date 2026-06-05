# Release / Overlay Readiness Checklist

This checklist is the release and live-overlay gate for Dennis Risk Agent runtime changes. It prevents repeat drift between mother-body docs, release overlays, live config, source wrappers, routing guards, and platform playbooks.

## Scope

- Applies before every release package, focused overlay, or live workspace overlay.
- Does not replace live `openclaw.json` validation.
- Does not access real platforms or DataAgent.
- Must be run together with `runtime_preflight_check.py`, `package_asset_scanner.py`, and the relevant smoke tests.

## Release Before Package

- `computer_use_poc/sso_session_runner.py` is a controlled real executor for unified login log, not `dry_run_only`.
- `bin/sso_session_runner` is a safeBin wrapper entrypoint that delegates to `computer_use_poc/sso_session_runner.py`; do not maintain a second runner implementation.
- Weapon runner actions are present for controlled `/apiv2/graphData` and `/apiv2/riskData` reads only.
- Runner imports `ks_aimate.sso_login_client.SmartSSOSession` as the preferred live executor.
- Runner has a controlled `.ks_sso/sso-state.json` cookie-state fallback for `kuaishou.com` cookies only.
- Runner supports:
  - `--platform login_log`
  - `--action query_user_login_log`
  - `--user-id`
  - `--timeout`
  - `--format json`
- Runner emits structured observation with `source_status`, `source_quality`, `redaction_applied`, `real_platform_request_executed`, and `executor_mode`.
- Runner emits auth refresh fields: `auth_refresh_attempted`, `auth_refresh_status`, `retry_after_refresh`, and `source_status_before_refresh`.
- Runner handles initial 302 / HTML login page / access proxy redirect by running one controlled SSO refresh through `skills/kuaishou-sso-login-client/scripts/sso_session.py` with the runner-built whitelist URL, then retrying once.
- No `target_url`, arbitrary URL, curl+cookie, or manual header handoff path is introduced.
- Static preflight pass does not prove live auth success; live runner command must still be tested after overlay.
- `DENNIS_ROUTING_GUARD_V1` appears in runtime guard docs.
- `single_entity_execution_mode`, `small_batch_execution_with_checkpoint`, `batch_clustering_mode`, and `strategy_recommendation_plan_mode` are documented.
- `source checkpoint` and `partial evidence card` are mandatory for ATO execution.
- `platform_call_playbook_index.md` exists and is listed as platform-call preflight reading.
- `runtime_validation_cases_v1.yaml` contains release/overlay gate cases.
- `smoke_tests.md` contains release/overlay must-run checks.

## Overlay Before Live Apply

- Do not copy old overlay packages over newer runtime files.
- Focused overlays must not include top-level `AGENTS.md` or `TOOLS.md` unless explicitly declared as a `main-entry patch`.
- `TOOLS.md` must contain `TOOLS_MAIN_ENTRY_GUARD_FULL`; a focused overlay must not replace it with a short stub.
- Verify overlay file list is generated from the canonical baseline, not from historical patch folders.
- Verify no full deep skill source, full prompt, historical run logs, source observations, auth state, cookie, token, session, header, or risky fixtures are included.
- Verify release notes explicitly distinguish:
  - template exists
  - release overlay copied
  - live runtime config actually applied
- Overlay must not reintroduce dry-run runner behavior or constructed-url-only success.

## Live Validation

- Live `openclaw.json` has a dedicated `dennis-risk-agent` entry.
- `dennis-risk-agent` does not inherit full-profile defaults.
- `exec.security=allowlist` is active.
- `exec.security=full` is forbidden for `dennis-risk-agent`.
- `safeBins` includes only approved controlled runners.
- exec approvals / allowlist for `dennis-risk-agent` is non-empty and includes the `sso_session_runner` wrapper plus `python3`.
- `tools.deny` blocks write/edit and direct unsafe platform access paths.
- `fs.workspaceOnly=true` is active.
- `loopDetection` is active.
- Main agent can spawn `dennis-risk-agent`.
- Main agent does not take over platform querying after Dennis timeout.
- Expired SSO cookie / ticket triggers runner auth refresh + single retry; refresh failure returns structured `auth_failed` / `blocked`, not a direct bypass.
- Real-time readonly API calls do not ask the user for confirmation when required fields are present.
- DataAgent / Hive / big batch / write / high-risk operations require plan or confirmation.
- Source checkpoints are written after each source.
- ATO single case returns a partial evidence card when any source is blocked, timed out, or auth failed.
- 2-9 user ATO complaint batches use `small_batch_execution_with_checkpoint`.
- `candidate_queue` and pilot observation logs write to canonical paths.

## Rollback Check

- Rollback target is a known canonical release, not an arbitrary historical overlay.
- Rollback does not restore dry-run-only runner.
- Rollback does not remove `DENNIS_ROUTING_GUARD_V1`.
- Rollback does not remove `runtime_config_not_applied` and direct-bypass guards.
- Rollback preserves source checkpoint, source_quality, and partial evidence fallback.
- After rollback, rerun `runtime_preflight_check.py` and smoke tests before live traffic.

## Not Allowed

- `dry_run_only` runner success.
- `constructed_url`-only success.
- Legacy-only `sso_session` import dependency.
- Arbitrary URL / `target_url` runner input.
- Multiple auth refresh retries or auth refresh loops.
- curl + cookie as a runtime platform access path.
- main agent direct platform bypass after Dennis timeout.
- Using old cached data as "no-cache" realtime result.
- Treating `no_data`, `blocked`, `timeout`, or `auth_failed` as no-risk counter evidence.
- Skipping platform playbook preflight because memory retrieval failed.
- Browser UI loop as default source path.

## Required Runtime Behaviors

- Runner real executor or structured fail-closed observation.
- `DENNIS_ROUTING_GUARD_V1`.
- Single / small / batch routing split:
  - 1 user: `single_entity_execution_mode`
  - 2-9 ATO complaint users: `small_batch_execution_with_checkpoint`
  - 10-49 entities: `batch_clustering_mode`
  - 50+ entities: aggregation / DataAgent-Hive query plan
- Real-time readonly API does not require user confirmation.
- DataAgent / Hive / big batch / write / high-risk operations require plan or confirmation.
- Platform playbook is read before source access.
- Each source produces checkpoint.
- Partial evidence card is emitted before overall timeout.
- `source_quality` records `no_data`, `blocked`, `auth_failed`, `timeout`, `parse_error`, and `missing_evidence`.
