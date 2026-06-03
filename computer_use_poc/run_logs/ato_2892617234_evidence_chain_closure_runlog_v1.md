# ATO 2892617234 Evidence Chain Closure Run Log v1

Status: historical_only / regression_source

This log records the Dennis-side evidence-chain learning from repeated
text-only/full-runtime checks for user `2892617234`. It is not a runtime rule,
not a platform transcript, and not a raw source dump.

## Case Boundary

- Case type: account security / ATO single case.
- User-visible conclusion boundary: supports ATO suspicion; does not confirm
  account takeover; does not support low-risk clean-account wording.
- DataAgent/Hive: not called in these runtime checks.
- Raw body / credential material: not retained in this log.

## Iteration Notes

1. Early full-runtime run
   - Problem: answer flattened source status and said completed/blocked sources.
   - Missing: WEB/publish fact chain, WEB login history chain, device
     consistency chain.
   - Root cause: Dennis did not yet consume pure passthrough body into business
     observations.

2. Pure passthrough parser round
   - Improvement: login log `response_too_large` no longer became
     network/auth/no-data.
   - Remaining gap: body visibility and parser mapping were identified, but
     missing fields were mostly explained rather than actively backfilled.

3. Safe capped body / projection round
   - Improvement: visible capped login rows could produce login time, WEB login
     source/type, DID, IP/UA, quickLogin/sync-login status, and byte-limit
     source quality.
   - Remaining gap: Archives photo/profile/user-analysis and Track HTTP 200
     could still be described as transport success without business field
     closure.

4. Chain-first rendering round
   - Improvement: final answer moved toward chain-first: WEB/publish fact,
     WEB login history, device identity alignment.
   - Remaining gap: when `photo_id` existed, Dennis still tended to say
     "next step: web_publish_fact" instead of auto-running registered
     photo detail actions.

5. Current closure round
   - Fix target: if `photo_id` is parsed and publish fields are missing,
     run `archives_photo_profile + archives_photo_meta` as controlled batch
     follow-up before Track/device consistency.
   - Fix target: user-facing source quality should not stop at "Archives/Track
     returned 200"; it must state extracted business fields, missing fields,
     partial subtype, and next-hop execution state.

6. Full-runtime live contract check after refresh
   - Primary batch path: `runtime_case_execution_runner.py --mode live`
     called local browser-backed `/actions/batch`; manual curl and legacy
     runner fallback remained disabled.
   - Finding before fix: photo detail follow-up used a standalone
     `auth_sensitive_serial` batch while still carrying a group dependency on
     `independent_parallel`; the service rejected that follow-up batch with
     HTTP 400, so photo profile/meta results were not returned.
   - Fix: standalone follow-up payloads no longer emit group-level
     `depends_on: [independent_parallel]` unless the payload actually contains
     an `independent_parallel` group.
   - Result after fix: four photo detail sources completed for the two parsed
     `photo_id` anchors, Track readiness executed after candidate device
     resolution, and no manual fallback was used.
   - Remaining case-specific gap: the live photo detail body exposed publish
     source/time context but did not close `publish_device`; therefore
     `web_publish_fact` remains `partial_fields`, `web_login_history` remains
     `partial_transport`, and `device_identity_alignment` remains
     `partial_consistency`.

## Current Evidence Chain Interpretation

- WEB login history:
  - Capped login logs can be partial evidence.
  - Byte limit means missing records are source gap, not no-data or low risk.
- WEB / publish fact:
  - `photo_id` is an anchor, not closure.
  - `archives_photo_profile/meta` must be the controlled next-hop when publish
    source/device/IP-UA are missing.
- Device identity:
  - WEB DID or publish device becomes candidate device input.
  - Candidate devices must be ranked and then used for Track / device baseline
    alignment.
  - Historical baseline still requires realtime source closure or explicit
    offline authorization.

## Regression Use

- `ato_live_evidence_chain_fixture_check.py` owns live-shaped regression.
- Suppressed-body shape remains regression for `service_body_visibility_gap`.
- Visible capped-body shape remains regression for parser and renderer
  consumption.
- Primary-only photo search shape now verifies that photo detail next-hop is
  generated before Track/device alignment.

## Safety

- Risk entity identifiers such as user ID, photo ID, DID, IP, UA and policy
  codes may be used as internal evidence anchors.
- Cookie/token/session/header/password raw values and strict PII raw values
  must not be output or retained in this run log.
