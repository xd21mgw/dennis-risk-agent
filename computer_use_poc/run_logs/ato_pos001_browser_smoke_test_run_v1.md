# ATO pos_001 Browser Smoke Test Run v1

## 1. Smoke Test Goal

case_id: `ato_pilot_pos_001`
user_id_ref: `user_ref_pos_001`
event_time: `2026-05-12 12:53:16`
abnormal_action: 异常发布色情内容 / 封禁

This run log records the browser observation smoke test result provided by the user. It does not call real platforms in this repository run, does not call DataAgent / Hive, and does not update release / outputs/dist.

Goals:

- Verify whether agent-browser can read Archives Center SPA pages.
- Verify whether Tianshi / strategy platform same-origin fetch can return strategy hits.
- Verify whether `archives_observation` and `strategy_or_event_observation` can be attached to a single-case ATO evidence card.

## 2. Execution Boundary

- readonly_only: true
- platform_write_action: false
- dataagent_called: false
- hive_called: false
- release_or_outputs_dist_modified: false
- no_sensitive_plaintext: true
- raw_reference_policy: safe_ref only

## 3. archives_observation Summary

status: ok

Observation:

- Archives Center browser observation is available.
- Current account status is shown as normal.
- Current status differs from the case registry description that referenced a ban.

Interpretation boundary:

- The current normal account status may mean the ban has been lifted, the ban was time-limited and recovered, or the registry information is stale.
- Current normal status must not be used as counter evidence that nothing abnormal happened at `event_time`.
- Current status is an account-state snapshot, not a historical event-time reconstruction.

## 4. strategy_or_event_observation Summary

status: ok

Observation:

- On the event date, 4 production strategy hits were observed.
- Strategy type: `ANTICRAWL_COMMON`.
- `riskDecision`: block.
- `confidence`: strong.
- Hit strategy: `BS_AntiCrawlPolicy_vision_profile_ban_user_limit`.
- The closest hit was about 34 minutes from `event_time`.
- No ACCOUNT / LOGIN strategy hit was observed.

Interpretation boundary:

- `ANTICRAWL_COMMON` is platform risk-control hit evidence, not direct ATO evidence.
- It can support that there were risk-control events near the abnormal event, but it does not prove account takeover.
- No ACCOUNT / LOGIN hit must not be used as counter evidence against ATO.
- No ACCOUNT / LOGIN hit does not mean there was no credential abuse, token reuse, Web/H5 session issue, or historical login-chain anomaly.

## 5. Source Quality

| source | status | source quality | boundary |
|---|---|---|---|
| Archives Center | ok | browser observation usable for account profile and current account status | current status is not event-time counter evidence |
| Tianshi / strategy platform | ok | browser same-origin fetch usable for strategy hit evidence | strategy hit is not direct ATO evidence |
| Unified login log | window_incomplete | online reliable window still incomplete for this historical event | over-window no_data cannot be counter evidence |
| Weapon | api_direct_empty_graph | previous API-direct graph was empty | empty graph cannot be counter evidence |
| Publish audit / token / Web-H5 session / ban reason | missing | key ATO chain evidence missing | requires offline Hive / DataAgent query plan |

## 6. Evidence Card Update Suggestion

### Strong Evidence

- No direct strong ATO evidence is available from this browser smoke test alone.

### Medium Evidence

- Event-day production strategy block hits exist near the abnormal event time.
  - evidence_source: strategy_or_event_observation
  - source_type: browser_dom_read / browser same-origin fetch
  - source_quality: status ok, reliability medium-high for strategy hit existence
  - boundary: not direct ATO evidence

### Weak Evidence

- Archives Center current profile and account status were readable through browser observation.
  - evidence_source: archives_observation
  - source_type: browser_dom_read
  - source_quality: status ok, useful as account profile/current state source
  - boundary: current status is weak context only

### Counter Evidence

- Current account normal status is not counter evidence against historical abnormal behavior.
- ACCOUNT / LOGIN no-hit is not counter evidence against ATO.
- Weapon empty graph is not counter evidence against device or account risk.

### Missing Evidence

- Publish audit log.
- Web/H5 session evidence.
- Token creation / refresh / usage chain.
- Ban reason and ban timeline.
- Complete offline login sequence around `event_time`.
- Offline Hive / DataAgent query plan for historical reconstruction.

## 7. Conclusion

- browser_observation_smoke_test: pass
- Archives Center can be supplemented through agent-browser path.
- Tianshi / strategy platform can be supplemented through browser same-origin fetch.
- Browser observation data quality is higher than API-direct-only observation for this historical pilot case.
- `pos_001` still cannot form a final ATO conclusion from current browser observation alone.
- Key ATO evidence still requires offline Hive / DataAgent query plan.

## 8. Next Recommendations

- Do not expand browser smoke testing to all 7 historical pilot cases by default.
- For semi-open testing, prioritize fresh cases where `event_time` is within the online login-log reliable window.
- For historical pilot cases, prefer generating offline Hive / DataAgent query plans before further manual browser observation.
- Use `pos_001` as the minimal browser-observation smoke sample for Archives Center + Tianshi route validation.
