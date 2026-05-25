# Batch Risk Golden Samples v1

These are simulated text-level golden samples. They contain no real platform data, no real user identifiers, no credentials, and no raw internal observations.

Purpose:

- Verify that Batch Risk Clustering Analysis Pack can support the full loop:
  - multi case input.
  - clustering.
  - representative sampling.
  - abnormal correlation matrix.
  - attack path hypotheses.
  - evidence gaps.
  - follow-up plan.
  - strategy / monitoring / grey release suggestions.

## Group 1: ATO Mixed Batch

### batch input 摘要

- batch_id: `golden_ato_mixed_001`
- entity_count: 12 users
- risk_domain: account_security
- scenario_type: ato_mixed_batch
- time_window: 2 hours around abnormal login / reset / publish events
- input facts:
  - 4 users show repeated password failure followed by successful login from new device and kick-out events.
  - 3 users show Harmony / OAuth / one-key login followed by token revoke or password reset.
  - 3 users show user claim only, no current login-chain evidence.
  - 2 users show normal new-phone migration pattern with stable geo, trusted device binding, and no downstream abnormal action.

### selected_mode

`batch_clustering_mode`, because entity_count=12 and the batch is mixed. Do not deep-check all users online by default.

### expected clusters

| cluster_id | cluster_name | covered_cases | expected evidence level |
|---|---|---|---|
| C1 | credential_stuffing_candidate | 4 | medium |
| C2 | Harmony_OAuth_one_key_takeover_candidate | 3 | medium |
| C3 | user_claim_only_or_source_gap | 3 | weak / source_gap |
| C4 | likely_normal_device_migration | 2 | counter / false_positive_review |

### expected abnormal correlation matrix

| relation_direction | observed_pattern | baseline_comparison | evidence_level | required_followup |
|---|---|---|---|---|
| password_failure_burst -> new_device_login | 4/12 clustered in short window | baseline_missing | medium | unified login timeline, device trust history |
| login_method=Harmony/OAuth -> abnormal_action=password_reset/token_revoke | 3/12 | baseline_missing | medium | OAuth grant records, token lifecycle |
| user_claim -> ATO conclusion | claims exist without platform evidence | not_applicable | weak | platform evidence required |
| stable_geo+trusted_device -> no downstream abnormal_action | 2/12 | baseline_missing | counter | confirm no publish/reset/payment anomaly |

### representative samples

- `ato_mixed_01`: high-confidence positive sample for credential stuffing candidate.
- `ato_mixed_05`: high-confidence positive sample for Harmony/OAuth path.
- `ato_mixed_08`: source-gap sample with user claim only.
- `ato_mixed_11`: suspected false positive sample for normal device migration.

### expected evidence cards

`ato_mixed_01`:

- strong_evidence: none until login timeline raw evidence is available.
- medium_evidence: password failure burst + new device login + kick-out sequence from current input.
- weak_evidence: user claim.
- missing_evidence: full login event order, device risk, reset / bind / publish audit.
- preliminary_judgement: credential stuffing candidate, not strong conclusion.

`ato_mixed_05`:

- medium_evidence: Harmony/OAuth login method followed by abnormal account action.
- missing_evidence: OAuth grant, token issued/revoke chain, downstream action audit.
- preliminary_judgement: Harmony/OAuth one-key takeover candidate.

`ato_mixed_08`:

- weak_evidence: user claim only.
- missing_evidence: all platform chain evidence.
- preliminary_judgement: insufficient evidence.

`ato_mixed_11`:

- counter_evidence: stable device migration indicators and no abnormal downstream action in input.
- missing_evidence: full login timeline.
- preliminary_judgement: likely false positive / manual review.

### expected pattern summary

- The batch should be split into at least 4 clusters.
- Do not write “this is one ATO gang”.
- Credential stuffing and Harmony/OAuth takeover are separate hypotheses.
- User-claim-only cases should become source_gap, not strong ATO.
- Normal migration cases should be used to calibrate false-positive boundary.

### expected cannot-conclude boundary

- Cannot conclude all 12 are ATO.
- Cannot conclude same gang without join key, shared infrastructure, shared device/IP, or shared OAuth app.
- Cannot use user claim as strong evidence.

### expected follow-up plan

- Online readonly: sample login timelines for 3-5 representatives, device trust, reset/bind/publish audit.
- DataAgent/Hive plan: only if over window or if batch expansion is needed; group by login_method, device_id, IP subnet, event order.
- Strategy: separate credential stuffing controls from OAuth / one-key login controls; add review path for normal migration.

### common failure modes

- Collapsing all 12 into “batch ATO”.
- Misclassifying Harmony/OAuth path as credential stuffing.
- Treating user claim as raw evidence.
- Ignoring false-positive normal migration cluster.

## Group 2: Protocol Downgrade / Forged Client Batch

### batch input 摘要

- batch_id: `golden_protocol_downgrade_001`
- entity_count: 24 devices / users
- risk_domain: traffic_anti_cheating
- scenario_type: protocol_downgrade_or_forged_client
- input facts:
  - 11 cases use old app versions with high request frequency.
  - 6 cases show mixed app versions from same DID family.
  - 5 cases show abnormal `mod` values including `mod=POST`.
  - 7 cases show DID mismatch across request and frontend activity.
  - frontend activity is partial or missing in 9 cases.

### selected_mode

`batch_clustering_mode`, because entity_count=24.

### expected clusters

| cluster_id | cluster_name | covered_cases | expected evidence level |
|---|---|---|---|
| C1 | old_version_high_frequency | 11 | medium |
| C2 | did_mismatch_multi_version | 7 | medium |
| C3 | abnormal_mod_field_semantics_pending | 5 | weak / source_gap |
| C4 | frontend_activity_gap | 9 | weak to medium |

### expected abnormal correlation matrix

| relation_direction | observed_pattern | baseline_comparison | evidence_level | required_followup |
|---|---|---|---|---|
| app_version=old -> high_request_frequency | concentrated in 11/24 | baseline_missing | medium | version population baseline |
| DID mismatch -> frontend_activity_gap | overlap in 6 cases | baseline_missing | medium | request/frontend join quality |
| mod field -> protocol hypothesis | `mod=POST` appears in 5 cases | baseline_missing | weak | field semantics dictionary |
| mixed_version_same_DID_family -> request burst | 6 cases | baseline_missing | medium | device graph and version history |

### representative samples

- `proto_03`: old version + high request frequency.
- `proto_09`: DID mismatch + frontend activity gap.
- `proto_14`: abnormal mod field, semantics pending.
- `proto_20`: suspected normal old client user for false-positive boundary.

### expected evidence cards

- raw evidence: app_version, DID relation, request frequency, frontend activity presence/absence from current input.
- derived evidence: old-version share, DID mismatch overlap, frontend gap ratio.
- model_inference: none unless explicitly provided.
- missing_evidence: normal version baseline, mod field dictionary, UA / endpoint / request interval.
- blocked_evidence: if frontend source partial, mark source_gap.

### expected pattern summary

- Candidate protocol / forged client path exists but requires field semantics and baseline.
- `mod=POST` must not be interpreted as HTTP method without schema.
- Old version alone is insufficient; high frequency + DID mismatch + frontend gap is stronger.

### expected cannot-conclude boundary

- Cannot conclude protocol attack from old version alone.
- Cannot conclude `mod=POST` means HTTP POST.
- Cannot conclude same toolchain without shared endpoint, UA, version pattern, DID mismatch or infrastructure.

### expected follow-up plan

- Get field dictionary for `mod`.
- Compare version distribution to normal traffic.
- Group by endpoint, UA, request interval, DID consistency, frontend activity.
- Sample 3-5 cases for request timeline and frontend presence.
- Strategy: monitor downgrade + DID mismatch + frontend gap as combined candidate, not single-field block.

### common failure modes

- Treating `mod=POST` as HTTP method.
- Calling all old-version users protocol attackers.
- Ignoring normal old client / compatibility traffic.

## Group 3: Interface Request Spike

### batch input 摘要

- batch_id: `golden_interface_spike_001`
- entity_count: 520 request entities / source refs
- risk_domain: anti_crawler
- scenario_type: interface_request_spike
- input facts:
  - endpoint A request volume increased 6x.
  - endpoint B increased 2x after campaign start.
  - monitoring pipeline changed sampling from 10% to 30%.
  - 35% of endpoint A traffic has missing frontend activity.
  - response code 429 increased, but only in two regions.

### selected_mode

`alert_batch_or_population_analysis_mode`, because entity_count=500+.

### expected clusters

| cluster_id | cluster_name | covered_cases | expected evidence level |
|---|---|---|---|
| C1 | endpoint_A_possible_crawler_or_protocol | endpoint A high-volume subset | medium |
| C2 | endpoint_B_campaign_business_spike | endpoint B campaign subset | weak / likely normal |
| C3 | monitoring_sampling_change_artifact | affected metric stream | counter / source_gap |
| C4 | regional_rate_limit_cluster | 429 in two regions | weak to medium |

### expected abnormal correlation matrix

| relation_direction | observed_pattern | baseline_comparison | evidence_level | required_followup |
|---|---|---|---|---|
| endpoint=A -> frontend_activity_gap | 35% gap | baseline_missing | medium | normal frontend gap baseline |
| endpoint=B -> campaign_window | aligns with campaign | baseline_missing | weak / normal explanation | campaign traffic baseline |
| sampling_policy_change -> observed_volume | monitoring changed 10% to 30% | source_change_detected | counter | normalize metrics |
| region -> response_code_429 | concentrated in two regions | baseline_missing | weak | infra status, proxy / ASN split |

### representative samples

- `if_spike_01`: endpoint A + frontend gap + high frequency.
- `if_spike_02`: endpoint A + normal frontend activity for boundary.
- `if_spike_03`: endpoint B campaign traffic.
- `if_spike_04`: 429 regional cluster.
- `if_spike_05`: monitoring sampling change artifact.

### expected evidence cards

- C1 sample should have medium derived evidence, missing raw request interval / UA / ASN.
- C2 sample should include counter evidence from campaign alignment.
- C3 sample should mark source metric change as counter / source-quality issue.

### expected pattern summary

- Do not directly strong-judge crawler.
- Output at least three competing explanations:
  - crawler / protocol direct call.
  - normal campaign traffic.
  - monitoring denominator / sampling change.
- Use abnormal correlation matrix to isolate endpoint A rather than entire system.

### expected cannot-conclude boundary

- Cannot conclude crawler until request intervals, UA, IP/ASN, frontend gap baseline and sampling-normalized trend are checked.
- 429 increase can be infra or rate-limit effect, not proof of bot.

### expected follow-up plan

- DataAgent/Hive aggregation by endpoint, UA, IP subnet/ASN, frontend_activity_presence, response_code, region, campaign flag.
- Normalize pre/post sampling change.
- Compare endpoint A vs B.
- Strategy: dashboard slice + rate-limit grey validation + manual review of representative requests.

### common failure modes

- Calling all spike traffic crawler.
- Ignoring monitoring sampling change.
- Ignoring business campaign as normal explanation.

## Group 4: Activity Arbitrage / Channel Fake Volume

### batch input 摘要

- batch_id: `golden_activity_arbitrage_001`
- entity_count: 180 users / devices
- risk_domain: activity_anti_cheating
- scenario_type: channel_reward_arbitrage
- input facts:
  - channel X has high reward_claim within first 10 minutes.
  - channel X has low D7 retention.
  - 42% of channel X cases share device families or emulator-like environment tags.
  - channel Y has high reward_claim but normal retention and diverse devices.
  - channel Z has low retention but low reward_claim.

### selected_mode

`large_batch_aggregation_mode`, because entity_count=180.

### expected clusters

| cluster_id | cluster_name | covered_cases | expected evidence level |
|---|---|---|---|
| C1 | channel_X_reward_low_retention_device_reuse | channel X subset | medium |
| C2 | channel_Y_high_reward_normal_retention | channel Y subset | counter / likely normal |
| C3 | channel_Z_low_retention_no_reward_abuse | channel Z subset | weak / business quality issue |

### expected abnormal correlation matrix

| relation_direction | observed_pattern | baseline_comparison | evidence_level | required_followup |
|---|---|---|---|---|
| channel=X -> reward_claim | high early claim | baseline_missing | medium | channel reward baseline |
| channel=X -> low_retention | low D7 retention | baseline_missing | medium | cohort retention baseline |
| channel=X -> device_reuse | 42% shared device families | baseline_missing | medium | device graph / emulator risk |
| channel=Y -> reward_claim | high reward but normal retention | baseline_missing | counter | normal campaign explanation |
| channel=Z -> low_retention | low retention but low reward | baseline_missing | weak | quality issue, not arbitrage |

### representative samples

- `arb_01`: channel X + reward + device reuse.
- `arb_02`: channel X + reward but no device reuse.
- `arb_03`: channel Y high reward normal retention false-positive control.
- `arb_04`: channel Z low retention no reward abuse boundary.

### expected evidence cards

- derived evidence should include channel-conditional reward rate, retention and device reuse ratio.
- raw evidence should be limited to current sample facts.
- missing evidence: baseline for channel, campaign rules, reward eligibility, device graph confidence.

### expected pattern summary

- The abnormal direction is channel -> reward_claim / low_retention / device_reuse.
- The conclusion is not “channel abnormal” generically.
- Channel Y and Z provide counterexamples.

### expected cannot-conclude boundary

- Cannot block all channel X users until baseline and device graph confidence are verified.
- Cannot treat low retention alone as arbitrage.
- Cannot treat high reward alone as fake volume.

### expected follow-up plan

- Hive aggregation by channel, reward_claim, retention, device family, emulator tag, cohort, campaign_id.
- Sample 3-5 channel X cases and 1-2 channel Y/Z boundary cases.
- Strategy: grey rule for high early reward + device reuse + low retention; monitoring with holdout and channel owner review.

### common failure modes

- Writing only “渠道异常”.
- Ignoring relation direction.
- Treating retention as direct black production evidence.

## Group 5: Internal Alert Batch Secondary Attribution

### batch input 摘要

- batch_id: `golden_alert_secondary_001`
- entity_count: 86 alerts
- risk_domain: strategy_recall_review
- scenario_type: alert_batch_secondary_attribution
- input facts:
  - all cases already hit strategy S.
  - 48 cases are behavior_type=publish_spam with similar object targets.
  - 18 cases are normal high-frequency creator workflow.
  - 12 cases have missing source logs due to timeout.
  - 8 cases are high-impact users with complaints.
  - strategy S reason is broad: high frequency + abnormal object cluster.

### selected_mode

`large_batch_aggregation_mode`, because entity_count=86 and the input is a strategy recall batch.

### expected clusters

| cluster_id | cluster_name | covered_cases | expected evidence level |
|---|---|---|---|
| C1 | likely_spam_publish_object_cluster | 48 | medium |
| C2 | normal_creator_high_frequency | 18 | counter / false_positive_review |
| C3 | source_timeout_gap | 12 | source_gap |
| C4 | high_impact_manual_review | 8 | manual_review_priority |

### expected abnormal correlation matrix

| relation_direction | observed_pattern | baseline_comparison | evidence_level | required_followup |
|---|---|---|---|---|
| strategy_id=S -> behavior_type=publish_spam | 48/86 | baseline_missing | medium | object target baseline |
| strategy_id=S -> normal_creator_workflow | 18/86 | counter | false_positive_signal | creator profile / historical behavior |
| timeout_source -> unknown_risk | 12/86 | source_gap | hypothesis_only | rerun source or offline logs |
| high_impact_user -> complaint | 8/86 | manual_review | review_priority | customer / ops context |

### representative samples

- `alert_01`: likely true positive spam publish cluster.
- `alert_02`: normal creator high-frequency false positive.
- `alert_03`: source timeout gap.
- `alert_04`: high-impact complaint sample.
- `alert_05`: edge sample with mixed spam and normal creator signals.

### expected evidence cards

- Do not repeat strategy reason as final conclusion.
- Include strategy hit as raw/behavior evidence source, not final judgement.
- Include counter evidence from creator workflow.
- Include blocked evidence for timeout sources.

### expected pattern summary

- This is a secondary attribution task.
- Strategy S recall contains true-positive cluster, false-positive cluster, source-gap cluster and review-priority cluster.
- Need representative samples and false-positive boundary before expanding controls.

### expected cannot-conclude boundary

- Cannot conclude all strategy hits are risky.
- Cannot treat strategy reason as sufficient evidence.
- Cannot ignore timeout cases as low risk.

### expected follow-up plan

- Aggregate by behavior_type, object target, creator profile, complaint status, source timeout status.
- Deep review 3-5 representative samples.
- Strategy: split rule S into publish-spam object cluster logic and creator workflow exemption / review queue.
- Monitoring: true positive rate, complaint rate, manual overturn rate, timeout source ratio.

### common failure modes

- Repeating strategy hit reason without secondary attribution.
- Ignoring false positives.
- Treating timeout as no issue.
