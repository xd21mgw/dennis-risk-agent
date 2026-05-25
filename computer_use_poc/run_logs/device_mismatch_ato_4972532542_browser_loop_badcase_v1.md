# DEVICE-MISMATCH-ATO-001 / 4972532542 Browser Loop Bad Case v1

## 1. Case Background

User-provided case:

- user_id: `4972532542`
- claim: publishing device for sexual-diversion video differed from daily-use device.
- user feedback: claimed account takeover.

This run log is based only on user-provided summary. No real platform query was executed in this Codex round.

## 2. What Went Wrong

The sub-agent was asked to complete Archives Center + track-analysis + device graph + login log full observation.

Observed failure mode:

- track-analysis browser task got stuck on device dropdown / SPA controls.
- repeated clicking / screenshotting produced no useful evidence.
- another sub-agent ran for a long time and likely stalled in Archives recoverable preflight or track-analysis browser.

This is a browser / SPA operation boundary issue, not a core risk-brain reasoning failure.

## 3. Evidence Strength Calibration

| item | evidence_type | strength | boundary |
|---|---|---|---|
| User says account was stolen | `user_claim` | weak | user claim cannot prove ATO |
| Violation / sexual-diversion video published | `behavior_event` | weak to medium | proves behavior occurred, not who operated |
| Publishing device differs from daily device | `raw_evidence` if observed, otherwise `inference` | medium | supports suspicion, requires login / device / publish audit corroboration |
| Phishing page / OAuth / frontend access | `missing_evidence` unless observed | missing | must not be written as confirmed |
| track-analysis browser loop | `missing_evidence` / `partial_source` | source gap | not no-risk evidence |

## 4. Required Runtime Behavior

If browser / SPA source loops or blocks:

- stop after 3 failed attempts on the same UI action;
- mark `operation_loop_detected=true`;
- mark `platform_access_partial=true`;
- mark `browser_overuse=true`;
- output partial evidence card;
- list completed sources and missing sources;
- suggest manual check, offline Hive / DataAgent query plan, or auth / selector fix.

## 5. Regression Cases Added

- `DEVICE-MISMATCH-ATO-001`
- `USER-CLAIM-WEAK-EVIDENCE-001`
- `PARTIAL-EVIDENCE-BROWSER-BLOCKED-001`
- `TRACK-SPA-LOOP-001`

## 6. Boundary

- real_platform_called: false
- DataAgent_called: false
- auth_state_modified: false
- gateway_modified: false
- release_repacked: false
- git_committed: false
