# v2.6.1 Archives API-first Core Capability Map Update Run

## Goal

Add the v2.6.1 archives API-first core capability map and align the local Dennis Risk Agent mother-body documents around capability-oriented archives center reading.

This run is local documentation / schema / smoke-test work only.

## Scope

- Added `computer_use_poc/archives_center_core_capability_map_v2_6_1.md`.
- Updated the v2.4.7.2 API inventory with v2.6.1 linkage and pending API additions.
- Updated the internal agent playbook so archives center defaults to capability-oriented API direct read.
- Updated observation schema with the v2.6.1 archives capability observation profile.
- Updated README and smoke tests.

## Version Boundary

- v2.6.1 is not a new platform.
- v2.6.1 is not a continuation branch of v2.4.x.
- v2.4.x remains historical validation record.
- v2.6.1 reorganizes archives center from page / Tab reading into risk capability packages.

## Capability Packages

1. `account_profile`
2. `account_change_trace`
3. `account_action_log`
4. `content_gallery`
5. `content_forensics`
6. `social_interaction`
7. `report_signal`
8. `relation_graph`

## API-first Policy

Default read order:

```text
API direct read
→ DOM scoped JS eval fallback
→ row feature filter fallback
→ scoped snapshot fallback
```

Page fallback is allowed only for:

- `API failed`
- `permission_blocked`
- `response_shape_changed`
- `key_fields_missing`
- `link_url_only`
- `mapping_pending_validation`
- `need_required_param`

## New Inventory Boundary

New endpoints from effective action HAR / screenshot analysis are recorded as inventory candidates. They must stay `pending_from_har_or_screenshot_analysis` until parsed API responses or executed observations validate request / response shape.

Screenshot content must not be written as interface validated.

## Safety Boundary

- No real platform access.
- No DataAgent call.
- No release package update.
- No automatic enforcement.
- No automatic risk finalization.
- No sensitive plaintext output.
- No raw private message / comment / video meta / userRouteTrace output.
- User / photo reports are feedback signals, not strong evidence alone.
- Same-device `type=0/type=1` mapping remains pending.

## Validation

Planned local checks:

- `rg -n "archives_center_core_capability_map_v2_6_1|account_change_trace|pending_from_har_or_screenshot_analysis|214-A" computer_use_poc`
- `git diff --check`

## Follow-up

- Validate pending v2.6.1 interfaces with parsed API observations before marking them `validated`.
- If response shapes change, update only request/response shape and fallback condition; do not infer risk conclusion from interface availability.
