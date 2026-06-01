# BC-BATCH-ATO-MISSING-CLUSTER-LENS

## Background

The batch risk clustering framework already has clustering capabilities: content similarity, device commonality, strategy hits, time concentration, account profile, behavior pattern, abnormal correlation matrix and representative sampling.

The bad case is not "batch has no clustering". The gap is that batch ATO / stolen-account posting analysis can stop at generic clusters and fail to apply a compromised-account / ATO-specific lens.

## Failure Pattern

Input:

- a batch of accounts with similar diversion content or shared strategy hits.
- several accounts also have WEB / H5 / PC non-trusted login.
- downstream publish / comment / live / private message happens shortly after login.
- some accounts use historical common `device_id`, but device model, OS, UA, IP, login source or login type drifts.

Bad output:

- "This is a content-diversion cluster" only.
- "This is a strategy-hit cluster" only.
- "device_id is common, so ATO confidence is lower."
- "representative sample supports ATO, so all accounts are stolen."
- "online login no_data / response_too_large means no login anomaly."

## Correct Behavior

Batch ATO must run:

```text
existing_cluster_signal_collection
-> ato_cluster_lens_overlay
-> compromised_account_cluster_detection
-> representative_case_selection
-> representative_ato_single_case_deep_dive
-> cluster_level_backfill
-> batch_conclusion
```

The output should preserve existing clusters and add ATO labels when supported:

- `existing_cluster_plus_ato_lens`.
- `web_untrusted_login_cluster`.
- `login_to_action_cluster`.
- `device_identity_inconsistency_cluster`.
- `compromised_account_cluster`.
- `high_suspected_ato_cluster`.
- `content_abuse_only_cluster`.
- `mixed_cluster`.
- `insufficient_evidence_cluster`.

## Evidence Rules

- Content diversion cluster + WEB non-trusted login commonality means content diversion cluster with ATO stolen-account posting suspicion.
- Strategy hit and content hit are action anchors or auxiliary evidence, not standalone ATO proof.
- Common `device_id` cannot reduce ATO confidence without full `device_identity_consistency`.
- Track activity cannot prove owner operation.
- Online login no_data, `response_too_large`, wrapper mismatch, blocked or timeout is source gap / Hive-required evidence gap, not low-risk evidence.
- Representative single-case deep dive proves a cluster mechanism only after coverage, similarity, source quality and counter examples are checked; it is not global proof for the whole batch.

## Required Remediation

- Register `batch_ato_cluster_lens` as an overlay under batch risk clustering.
- Add L1 fields for WEB non-trusted login, abnormal login method, `login_to_action_delta`, content-action deep dive, device identity consistency, shared infrastructure and historical behavior shift.
- Add representative sampling and `cluster_level_backfill` requirements.
- Add user-facing batch ATO template that does not dump internal runtime YAML by default.
- Add regression cases for WEB non-trusted login clusters, existing-cluster-plus-ATO-lens, common-device spoofing, no-data boundary, Hive registry-first and representative-not-global-proof.
