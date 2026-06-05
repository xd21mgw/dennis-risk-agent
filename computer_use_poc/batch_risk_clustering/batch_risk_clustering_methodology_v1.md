# Batch Risk Clustering Methodology v1

Status: runtime_methodology

Batch attack judgement converts a flat list of users, devices, alerts or events
into entity graphs, source commonality, risk clusters, attack-chain hypotheses,
evidence boundaries and strategy candidates. It must not become a per-entity
transcript and must not infer "same gang" from one shared weak clue.

## 1. Three-Mode Workflow

1. Select exactly one mode from
   `full_observation_mode`, `sample_expand_validate_mode`, and
   `wide_table_aggregate_mode`.
2. Run `entity_resolution_first`.
3. Produce source-level `source_commonality_card` objects or consume
   `wide_table_aggregate_report`.
4. Run `multi_source_fusion`.
5. Output `cluster_summary_card` per risk / boundary / counter cluster.
6. Render cluster-level attack chains through `attack_chain_renderer`.
7. Produce strategy candidates with coverage, precision/unknown precision,
   false-positive risk and validation requirements.
8. Keep `source_quality`, `missing_evidence`, and conclusion boundary visible.

## 2. Mode Responsibilities

### full_observation_mode

Use for 2-10 entities when the user asks to see whether a small set is related
or wants detailed observation. All entities can be observed within the current
safe realtime source scope, but the answer is still horizontal commonality
first, not one-by-one logs.

### sample_expand_validate_mode

Use for >10 urgent / unknown / "先看看" / same-origin questions where no wide
table result exists yet. Sample 10, run full observation on the sample, repeat
up to 5 rounds / 50 deep checks, then continue, stop, or recommend offline
validation. See `batch_risk_representative_sampling_v1.md`.

### wide_table_aggregate_mode

Use for wide table / features / coverage / precision / recall / strategy /
historical review / DataAgent/Hive intent. DataAgent/Hive returns a
`wide_table_aggregate_report`; Dennis explains risk and recommends validation.
The registered candidate table for the first batch is
`ks_rc_bs.dws_risk_register_gang_user_week_feature_wide_di`, marked
`registered_candidate_not_executed` until authorized and confirmed.

## 3. Entity Resolution First

`entity_graph` is a top-level batch layer, not a side effect of Weapon:

- user input -> user to device expansion.
- device input -> device to user expansion.
- mixed input -> user-device graph.
- high-degree entities are marked and capped, not blindly expanded.
- blocked / no_data / timeout goes to `source_quality` and
  `conclusion_boundary`.

See `batch_risk_case_schema_v1.md` for the full schema.

## 4. Commonality Before Fusion

Realtime batch observation produces `source_commonality_card` per source:

- login log: login time concentration, IP/C segment, login type, token / kick /
  resetPwd / new-device signals, no_data/window boundary.
- archive/admin: account state, profile baseline, content/action anchors,
  punishment / appeal / complaint context.
- Weapon: user-device edges, high-degree devices, risk labels, stable-device
  counter evidence.
- RCP/Tianshi: sourceId / policy_code / event_type / hit time commonality with
  `strategy_hit_not_final_judgement`.
- Track/frontend: frontend activity alignment, missing frontend activity, device
  activity consistency.

Do not skip this layer and jump directly to an all-batch conclusion.

## 5. Multi-Source Fusion

Fusion promotes a shared signal only when evidence type and denominator support
it:

- Strong shared signals normally need cross-source agreement, such as device
  commonality + login commonality + behavior commonality.
- Strategy hit alone, same IP alone, same app version alone, same weak device
  label alone, or model score alone cannot finalize risk.
- Normal mixed samples and counter evidence must be listed separately.
- Source conflict remains in `conflicting_signals`.
- partial / no_data / blocked / timeout changes the conclusion boundary.

## 6. Cluster Summary

Batch conclusions are cluster based:

- single dominant cluster;
- multiple risk clusters;
- normal mixed / evidence-insufficient cluster;
- counter-evidence cluster.

Main cluster coverage below 70% is not "no risk"; it may indicate mixed risk.
Normal mixed samples above about 30% must raise false-positive risk.

## 7. Attack Chain Rendering

Render attack chains per cluster:

- `complete_chain`: key links closed by current evidence.
- `partial_chain`: important links exist but some fields or sources are missing.
- `hypothesis_chain`: statistical / inferred chain only.
- `no_chain`: no coherent chain from current evidence.

Wide-table correlation alone can only create `statistical_chain_hypothesis` or
`hypothesis_chain` unless representative samples close runtime evidence.

Risk-specific nodes vary:

- device farm / group control: infrastructure -> account control -> synchronized
  behavior -> monetization / diversion.
- ATO abnormal publish: control entry -> account takeover -> publish/content
  handoff -> platform response.
- protocol automation / anti-crawler: endpoint access -> request pattern ->
  frontend/backend mismatch -> data extraction or abuse goal.

## 8. ATO Cluster Lens

ATO / compromised-account lens is additive, not a separate batch mode. It adds:

- WEB / H5 / PC untrusted login commonality.
- token / OAuth / scan / one-click / refreshToken / passToken / byToken /
  resetPwd / kickout signals.
- `login_to_action_delta`.
- content action deep dive for representative samples.
- device identity consistency: model, OS, app version, UA, browser fingerprint,
  IP / province / city / ASN, login source and login type.
- shared infrastructure: IP, ASN, UA, browser fingerprint, landing page, contact
  info, diversion wording and cadence.
- historical behavior shift.

Boundaries:

- Representative single-case proof does not prove every account in the batch.
- Content diversion + ATO lens should be written as "content diversion cluster
  with ATO stolen-account posting suspicion" when both apply.
- Online login no_data / response_too_large / blocked / timeout is a source gap,
  not low-risk evidence.
- Batch ATO long-window evidence uses registry-first offline planning only;
  DataAgent/Hive is never executed without authorization.

## 9. Strategy Candidate Discipline

Expose both a user-visible priority and an action group. Priority orders
recommendations; it does not grant action permission.

- `P0` + `ready_for_controlled_gray_validation`: multi-source support,
  reasonable denominator, false-positive boundary known, still needs controlled
  gray validation. It is not auto-launch or direct disposition.
- `P1` + `combine_before_use`: useful feature but unsafe alone; use with other
  signals, review, second verification or scoring.
- `P2` + `monitor_or_expand_only`: weak signal for monitoring, offline mining or
  sample expansion; not recommended for direct treatment.

Each candidate must include coverage estimate, precision estimate or
`not_evaluable`, false-positive risk, stability, rollout suggestion, required
validation data and not-recommended usage.

## 10. Evidence Boundaries

- Current batch facts must come from current input, current realtime observation
  or an authorized current `wide_table_aggregate_report`.
- Historical cases are context or hypothesis only.
- no_data is not no-risk.
- blocked / timeout / partial sources are source gaps.
- Similarity alone does not prove same gang.
- Wide-table statistical correlation is not a complete attack-chain fact.
- Representative sample conclusions require full-batch validation before
  population coverage claims.
- Credential secrets and strict PII plaintext must not be output; risk entity
  identifiers may be retained for internal risk evidence chaining.
