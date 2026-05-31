# Dennis Passthrough Default Path Migration V1

## Goal

Start Dennis-side migration from browser-backed `compat_summary` to explicit `passthrough` for the first account-security four-source chain:

- `track_analysis_summary`
- `login_logs_search`
- `weapon_inventory`
- `rcp_snapshot`

This change is scoped to Dennis mother files. It does not modify `browser-backed-api-poc` or `outputs/full_runtime`.

## Short-term Boundary

- `passthrough` is the Dennis default account-security browser-backed path.
- `compat_summary` remains as a legacy migration fallback.
- Fallback is not silent. It requires explicit `allow_compat_fallback=true`.
- Existing evidence card shape remains; Dennis evidence summaries can now consume `normalized_observation`.
- Existing summary/compat logic is marked legacy and retained for controlled pilot safety.

## Long-term Boundary

- Browser-backed service should ultimately keep only controlled passthrough.
- Service-side summary / `source_card` / `source_quality` / evidence summary logic should be removed after deletion gates pass.
- New actions should be passthrough-only.
- Dennis owns parser, `normalized_observation`, evidence card, redaction, and risk reasoning.

## Deletion Gates For Legacy Summary Logic

1. Four-source passthrough dual-run passed.
2. `full_runtime` controlled pilot passed.
3. Dennis evidence card is fully usable from `normalized_observation`.
4. Reference checks confirm no main-chain dependency remains on service summary logic.

## Implementation Summary

- `call_account_security_sources()` defaults to explicit `response_mode=passthrough`.
- Passthrough results receive Dennis-owned `source_quality` based on parser output.
- Evidence card business summaries consume `normalized_observation` before relying on legacy `source_card` material.
- Passthrough failures enter source quality and missing evidence.
- `compat_summary` fallback is available only through explicit `allow_compat_fallback=true`.

## Safety Boundary

- No raw upstream body output.
- No raw login record dump.
- No raw Weapon `labelInfo` or `originalLog` dump.
- No cookie / token / session / header / password access.
- No DataAgent / Hive call.
- `outputs/full_runtime` remains builder-owned and is not directly modified.
