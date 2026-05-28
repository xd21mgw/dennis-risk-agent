# Platform Access Execution v0.1 Overlay Smoke Tests

## WEAPON-GRAPHDATA-WRAPPER-SMOKE-001

Expected: dennis-risk-agent uses `computer_use_poc/bin/sso_session_runner`; wrapper/dependency errors are not reported as auth failures.

## WEAPON-RISKDATA-DIRECT-DEVICEID-001

Expected: known `deviceId` can trigger Weapon `riskData` directly; graphData is discovery only when `deviceId` is missing.

## RCP_EVENTLIST_STRATEGY_HIT_SMOKE_001

Expected: RCP `eventList` is the primary strategy-hit event list source; `fastQueryHbase` is fallback; missing upstream IDs produce `missing_upstream_id`.

## RCP-EVENTLIST-CUSTOM-COLUMNS-001

Expected: `tableHeaderList` / custom columns are supported; unconfirmed fields are field-level partial, not whole-chain unknown.

## TRACK-ANALYSIS-EVENT-DAY-ACTIVITY-001

Expected: event-day activity alignment follows track-analysis contract and does not become standalone final judgement.

## ARCHIVES-CENTER-PUBLISH-CHAIN-P0-001

Expected: Archives user analysis is ATO P0 and abnormal publish chain is P0-conditional.
