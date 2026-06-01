# Batch ATO Cluster Lens v1

## 1. Positioning

This lens is an overlay on the existing batch risk clustering framework. It does not replace content similarity clustering, device clustering, strategy-hit clustering, time concentration, account-profile clustering, behavior clustering, or abnormal correlation matrix analysis.

Use it when a batch may contain compromised accounts, ATO-driven diversion content, non-trusted WEB/H5/PC login followed by abnormal actions, or common `device_id` with drifting identity variables.

Core flow:

```text
batch input
-> existing_cluster_signal_collection
-> ato_cluster_lens_overlay
-> compromised_account_cluster_detection
-> representative_case_selection
-> representative_ato_single_case_deep_dive
-> cluster_level_backfill
-> batch_conclusion
```

## 2. Required Overlay Signals

### WEB non-trusted login

Mark `web_untrusted_login_cluster` when multiple accounts share one or more of:

- recent WEB / H5 / PC login.
- login source changed from historical APP to WEB / H5 / PC.
- WEB login device / IP / UA / browser fingerprint is not historical baseline.
- WEB login is followed by publish, comment, live, private message or profile change.

### Abnormal login method

Track:

- token / OAuth / scan / one-click login abnormality.
- refreshToken / passToken / logined / byToken control-chain clues.
- resetPwd / password change / account protection / kick out chain.

### Login-to-action closure

Compute `login_to_action_delta` for downstream actions:

- publish video.
- live.
- comment.
- private message.
- profile change.
- four-items change.
- strategy / audit diversion hit.

A short delta, especially 0-30 minutes, is a core ATO lens feature when paired with login/control-chain abnormality.

### Content action deep dive

For diversion or abnormal-content batches, representative samples must run `content_action_deep_dive` and try to extract:

- `photo_id` / `live_id` / `comment_id`.
- publish / action time.
- publish source.
- publish device.
- publish IP / UA.
- audit, strategy or diversion reason.
- four-items information if available.
- alignment with login/control-chain candidate session.

### Device identity consistency

Batch ATO must aggregate `device_identity_inconsistency_cluster`, not just `device_id` frequency.

Compare:

- whether `device_id` is historical common.
- first-seen time and 30/90/180 day active-day counts.
- `device_model` drift.
- `os` / `os_version` drift.
- `app_version` drift.
- UA drift.
- browser fingerprint drift.
- IP / province / city / ASN abnormality.
- login source shift from APP to WEB / H5 / PC.
- login type abnormality.

Risk labels:

- `device_identity_inconsistency_cluster`.
- `possible_device_id_spoofing`.
- `common_device_id_but_abnormal_fingerprint`.
- `common_device_id_not_sufficient_to_exclude_ato`.

Common `device_id` cannot reduce ATO confidence unless the broader device identity variables are also consistent.

### Shared infrastructure

Aggregate:

- shared IP / subnet.
- shared ASN.
- shared UA.
- shared browser fingerprint.
- shared login source / login type.
- shared landing page, contact info or diversion wording.
- shared publish cadence or time window.

### Historical behavior shift

Mark:

- historical normal accounts suddenly publish diversion content.
- historical no-WEB accounts recently use WEB then publish abnormal content.
- historical content category differs from current diversion content.
- historical publish device differs from current control endpoint.

## 3. Cluster Labels

Use the lens to classify each existing cluster:

- `existing_cluster_plus_ato_lens`: existing content/device/strategy/time cluster with ATO lens applied.
- `web_untrusted_login_cluster`: WEB/H5/PC login commonality is material.
- `login_to_action_cluster`: login-to-action delta is short and repeated.
- `device_identity_inconsistency_cluster`: identity variables drift across cases.
- `compromised_account_cluster`: login/control-chain abnormality, downstream action abnormality, and identity/historical shift are jointly supported.
- `high_suspected_ato_cluster`: strong suspicion but one key source is missing.
- `content_abuse_only_cluster`: content or strategy signals exist but ATO control-chain evidence is absent.
- `mixed_cluster`: ATO-driven and non-ATO content abuse / fake-account / human grey traffic are mixed.
- `insufficient_evidence_cluster`: lens cannot be decided because source coverage is insufficient.

## 4. Representative Deep Dive

For every suspected compromised-account cluster, select:

- 2-3 high-suspicion samples.
- 1-2 medium-suspicion samples.
- 1 boundary sample.
- 1 counter-example sample when available.

Selection priorities:

- clearest WEB non-trusted login.
- shortest `login_to_action_delta`.
- strongest `device_identity_inconsistency`.
- most typical diversion content.
- least source gap.
- best representation of the cluster pattern.

Each selected representative sample runs the current ATO single-case chain:

```text
login_logs_search + archives_user_profile + archives_user_analysis + archives_photo_search + track_analysis_check_data_ready
-> multi-source suspicious anchor derivation
-> candidate_control_endpoint_extraction
-> device_identity_consistency
-> historical_baseline_comparison
-> business evidence card
```

## 5. Cluster-Level Backfill

After representative single-case deep dive, backfill to cluster level:

- `login_to_action_delta` distribution.
- `device_identity_inconsistency` coverage.
- `possible_device_id_spoofing` coverage.
- shared IP / UA / ASN / browser fingerprint coverage.
- content similarity coverage.
- landing page / contact info coverage.
- historical behavior shift coverage.
- strategy-hit combination coverage.
- source quality / missing evidence coverage.

Representative proof is not global proof. It supports the represented cluster only after similarity, coverage, source quality and counter-examples are checked.

## 6. Evidence Boundaries

- Existing cluster signals and ATO lens are additive, not mutually exclusive.
- A content-diversion cluster plus WEB non-trusted login commonality should be written as content diversion cluster with ATO stolen-account posting suspicion.
- Batch commonality cannot prove every account is stolen.
- Strategy hit or content hit cannot independently determine ATO.
- Track activity is auxiliary only and cannot prove owner operation.
- Common `device_id` is not an ATO exclusion; run device identity consistency.
- Online login no_data, `response_too_large`, wrapper mismatch, blocked, timeout or partial cannot support low-risk conclusion.
- Admin APP-only login evidence does not close WEB/H5/PC/token/OAuth/scan control-chain evidence.
- Batch ATO long-window or incomplete realtime login/control evidence requires a Hive registry-first query plan. Do not freely guess tables and do not call DataAgent/Hive without per-call authorization.
- When realtime control-chain evidence is incomplete, place `login_log_window_incomplete`, `admin_app_log_only_gap`, `web_control_chain_missing` and `offline_hive_required` in evidence gaps / next actions as applicable.

## 7. User-Facing Output Contract

Batch ATO output must cover:

1. Batch conclusion.
2. Existing cluster evidence.
3. ATO lens hits.
4. Risk clusters with size, commonality, confidence and mixed-cluster markers.
5. Representative single-case summaries.
6. Cluster-level backfill features.
7. Evidence gaps.
8. Next actions.

User-facing output must not dump internal runtime YAML, debug fields, or validation fields by default.
