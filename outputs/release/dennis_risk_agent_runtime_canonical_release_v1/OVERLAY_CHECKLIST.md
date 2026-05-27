# Overlay Checklist

Use this checklist after copying the release into the internal Agent live workspace.

## File Overlay

- [ ] Release files copied into the intended workspace.
- [ ] `computer_use_poc/runtime_config_apply_checklist_v1.md` exists.
- [ ] `computer_use_poc/runtime_canonical_baseline_v1.md` exists.
- [ ] `AGENTS.md` is updated from this release.
- [ ] `computer_use_poc/runtime_validation_cases_v1.yaml` is updated.
- [ ] `computer_use_poc/smoke_tests.md` is updated.

## Runtime Config Apply

- [ ] Live `openclaw.json` has a dedicated `dennis-risk-agent` entry.
- [ ] dennis-risk-agent does not inherit full-profile defaults.
- [ ] `exec.security=allowlist` is active.
- [ ] `safeBins` is active.
- [ ] `tools.deny` is active.
- [ ] `fs.workspaceOnly=true` is active.
- [ ] `loopDetection` is active.
- [ ] main agent spawn resolves to dennis-risk-agent.

## Runtime Behavior

- [ ] main agent does not take over risk-platform querying after dennis timeout.
- [ ] ATO single case emits partial evidence card on source timeout / auth failure.
- [ ] 2-9 user ATO small batch uses `small_batch_execution_with_checkpoint`.
- [ ] per-source checkpoint preserves completed P0 evidence.
- [ ] feedback writer resolves runtime log path correctly.
- [ ] pilot observation log path is append-only and redacted.

## Source Boundary

- [ ] Browser fallback marks `access_method`.
- [ ] Wrapper-first failure marks `source_quality`.
- [ ] `login_log_window_incomplete` boundary is validated.
- [ ] `app_login_only_source_gap` boundary is validated.
- [ ] `no_data`, timeout, blocked, and auth failure are not risk counter-evidence.

## Safety

- [ ] No cookie, token, session, header, API key, private key, password, phone number, identity number, raw platform response, or raw auth state is present.
- [ ] No historical `outputs/dist` package is nested.
- [ ] No full deep Skill source is included.
- [ ] No full historical run log directory is included.
- [ ] Package scanner / preflight summary is reviewed.
