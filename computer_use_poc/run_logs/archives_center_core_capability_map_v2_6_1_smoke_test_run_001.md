# v2.6.1 Archives API-first Core Capability Smoke Test Run 001

## Scope

execution_mode: `v2_6_1_capability_smoke_test`

This run records the internal Agent observation summary for the v2.6.1 archives API-first core capability map. It is documentation-only in this repository update.

## Boundary

- No real platform access by Codex in this update.
- No DataAgent call.
- No release package update.
- No core Skill modification.
- No sensitive plaintext output.
- No auth state export.
- No write operation.
- No risk finalization.
- No enforcement or punishment suggestion.

## Overall Result

- 8 / 8 capability packages completed API-first small-loop smoke coverage.
- 6 capability packages basically succeeded.
- 2 capability packages remain partial.
- Page / DOM / selector were not triggered by default.
- Fallback only triggered under allowed conditions.

This is `capability_smoke_test_passed`, not full API regression.

## Capability Results

### 1. account_profile

Result: basically_success

- `/archives/user/home/info`: success.
- `/archives/user/home/getUserLabel`: success.
- `/archives/draco/getPunishStatus`: user-level unavailable; requires photo/live `targetId`.

Boundary:

- `getPunishStatus` must not be treated as a generic user-level API.

### 2. account_change_trace

Result: basically_success

- `/v4/audit/user/fourinfo/log/search`: success.
- Current sample: `empty_result`.

Boundary:

- `empty_result` must not be interpreted as no profile change.

### 3. account_action_log

Result: basically_success

- `/v3/user/log/coreLogs/fetch`: success.
- Current sample: `empty_result`.

Boundary:

- `empty_result` must not be interpreted as no operation log.

### 4. content_gallery

Result: basically_success

- `/v3/user/gallery/photo/list`: success, observed `total=746`.
- `/v4/archives/gallery/live/list`: success, `empty_result`.
- `/archives/user/gallery/momentList`: success, `empty_result`.

Boundary:

- Empty live/moment result must not be used as no-risk evidence.

### 5. content_forensics

Result: basically_success

- `/v3/photo/profile`: success.
- `/v3/photo/meta`: success.
- `/v3/photo/report/aggregate`: success.
- `/archives/photo/home/userAutonomy`: success.

Boundary:

- `photo/meta` lacks `publishDevice`, `publishVersion`, and `isImport` in the observed sample.
- Use `profile.uploadSource`, `photoMethod`, and related profile fields as proxy features when meta fields are missing.
- Do not output full video meta JSON.

### 6. social_interaction

Result: partial

- `/archives/user/message/search`: success.
- Observed `total=4029930781`, suspected internal counter or unreliable total.
- `/archives/photo/comment/search`: success.
- `/v3/user/profile/relation/fans/list`: success.
- `/v3/user/profile/relation/follow/list`: success.

Boundary:

- Do not treat message `total` as true total volume.
- Record `list_len` and field structure only.
- Private message / comment content remains summarized, not raw output.

### 7. report_signal

Result: partial

- `/v4/archives/report/user/search`: success, `empty_result`.
- `/v4/archives/report/photo/search`: persistent 500.

Boundary:

- Mark photo report search as `server_error_500 / request_shape_uncertain / pending`.
- Do not write `/v4/archives/report/photo/search` as validated.
- Report signals are external feedback signals and not strong evidence alone.

### 8. relation_graph

Result: basically_success

- `/archives/user/search/device type=0`: success.
- `/archives/user/search/device type=1`: success with `empty_result`.
- Correct payload: `{keyword, inputType: 0, type}`.

Boundary:

- `type=0/type=1` business semantics remain `mapping_pending_validation`.
- Do not write hard-coded login/register mapping.

## Documentation Updates

Updated:

- `computer_use_poc/archives_center_core_capability_map_v2_6_1.md`
- `computer_use_poc/archives_center_api_inventory_v2_4_7_2.md`
- `computer_use_poc/archives_center_internal_agent_playbook.md`
- `computer_use_poc/observation_schema.md`
- `computer_use_poc/smoke_tests.md`
- `computer_use_poc/README.md`

## Conclusion

The v2.6.1 archives API-first core capability map can be marked:

`v2.6.1 archives API-first capability smoke test passed`

with the following caveats:

- Not full API regression.
- `getPunishStatus` is not a generic user-level API.
- `report/photo/search` remains pending due persistent 500.
- `message/search total` is unreliable.
- Empty results are not no-risk evidence.
- Same-device type mapping remains pending.
