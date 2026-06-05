# Field Output Classification Policy v1

## 1. Purpose

This policy standardizes Dennis Risk Agent output classification for risk-analysis fields and credential secrets. It prevents repeated misclassification of IP, UID, DID, deviceId, and tokenId as P0 credential leakage while keeping true authentication secrets strictly protected.

This policy applies to:

- KIM E2E reports.
- Runtime validation.
- Observation contracts.
- Evidence cards.
- Run logs.
- Batch pattern summaries.
- Internal and semi-open Dennis Agent responses.

## 2. Field Classes

Runtime and evidence-card code uses these canonical class names:

- `credential_secret`
- `pii_strict`
- `risk_entity_identifier`
- `source_summary_metric`

| canonical class | examples | default_output_policy | severity_if_plaintext |
|---|---|---|---|
| `credential_secret` | token secret, accessToken, refreshToken, cookie, session, sessionId, authorization header, authToken, password, salt, browser_storage_state_marker, auth credential in headers, KIM code, login ticket, credential secret | never plaintext; `present_redacted` / `credential_present_redacted` only | P0 |
| `pii_strict` | phone number, ID card, real-name identity information, precise personal identity fields, verification code | limited masking / presence summary; no full plaintext | P1/P0 depending exposure |
| `risk_entity_identifier` | UID / user_id, DID, device_id / deviceId, deviceceid, IP, UA / user_agent, photo_id, event_id / eventId, source_id / sourceId, policy_code / strategyId / hitFusePolicyCode, tokenId when it is an event identifier rather than a token secret, login method, logSource, timestamp / `_occurTime`, device model, app version, coarse geo | internal risk review keeps the raw risk entity by default for evidence chaining; external share masks by audience scope | P1 if audience policy is wrong; not P0 credential leakage by default |
| `source_summary_metric` | IP subnet, ASN, carrier, geo cluster, device risk tags, same-device count, registration cohort, behavior-object cluster, risk label distribution, success/failure counts, time-series summary | preferred output for reports and KIM responses | usually safe if no raw sensitive values |

## 3. P0 Credential / Authentication Secrets

Never output plaintext:

- token plaintext.
- accessToken / refreshToken plaintext.
- cookie / session / sessionId plaintext.
- authorization header / authToken plaintext.
- password / salt.
- browser_storage_state_marker.
- authentication credentials inside headers.
- KIM code / login ticket / credential secret.

Output strategy:

- Only output `present_redacted` or `credential_present_redacted`.
- Never write plaintext to run log, KIM response, report, observation, evidence card, or raw reference.
- If requested by a user prompt, deny or redact.

## 4. Highly Sensitive Personal Information

Default no full plaintext:

- phone number.
- ID card / real-name identity information.
- precise personal identity information.
- verification code.

Output strategy:

- phone number:
  - `internal_risk_review`: keep first 7 digits, for example `1381234****`.
  - `external_share`: keep first 3 digits, for example `138********`.
  - Full phone number is never output.
- ID card:
  - never output the full number.
  - `internal_risk_review`: only weak summary such as `id_card_present=true` and `birth_year_present=true`.
  - `external_share`: only `id_card_present=true`.
- real name:
  - never output the raw name by default.
  - use `name_present=true`.

## 5. Risk Entity Fields

Risk entity fields are normal inputs for risk analysis:

- UID / user_id.
- DID / device_id / deviceId / deviceceid.
- IP.
- UA / user_agent.
- photo_id.
- event_id / eventId.
- policy_code / source_id / strategy_id / hitFusePolicyCode.
- tokenId when it is an event identifier rather than a token secret.
- requestId / sourceId / strategyId / adminaction.
- appVersion / UA / device model / login method / coarse geo.

Output strategy:

- Trusted internal risk analysis / source observation / evidence card: output raw risk entity identifiers by default when they are needed to chain evidence. This includes user_id, device_id / DID, IP, UA / user_agent, photo_id, event_id, source_id, policy_code / strategy_id, login_type, publish_source, device model, and app version. Do not write “IP/device_id hidden so cannot judge” in internal risk review; keep these anchors for login-vs-publish device alignment, same-device expansion, and historical baseline checks.
- KIM semi-open: may output by default when useful, but avoid large-scale detail export; use `safe_ref` or partial mask when the audience or channel is broader.
- Larger semi-open, cross-team sharing, or outbound materials: default to `masked`, `safe_ref`, `count`, or `distribution`. `external_share` small-batch headings may use aliases such as `用户 U1（user_***1837）` or `用户 A`.
- Do not confuse risk entity fields with token / cookie / session / password credential secrets.

`tokenId` rule:

- If it is a token event identifier, it is not a token secret.
- Internal risk review keeps it as a risk entity identifier; external share may mask it by audience scope.
- If it exposes a reusable credential secret, treat it as P0 credential.

## 6. Derived / Aggregate Features

Preferred output:

- IP subnet / ASN / carrier / geo cluster.
- device risk labels.
- same-device count.
- registration cohort.
- behavior-object cluster.
- risk label distribution.
- success/failure counts.
- time-series summary.

Output strategy:

- Prefer these features in KIM responses, reports, and cross-team sharing.
- If derived features satisfy the analysis need, avoid raw detail.

## 7. Output Scope Matrix

| output_scope | risk_entity_identifier | credential_secret | pii_strict | recommended_output |
|---|---|---|---|---|
| `internal_risk_review` | raw risk entity identifiers allowed by default for evidence chaining | never plaintext | limited masking / weak summary | evidence card values with field paths; credentials present_redacted |
| `external_share` | masked / aggregate only | never plaintext | stricter masking / presence only | masked, safe_ref, count, distribution, no raw detail |

## 8. Validation Rules

- IP / UID / DID / deviceId plaintext is not automatically P0 credential leakage.
- Whether to mask risk entity fields depends on audience scope, sharing scope, field purpose, and output channel.
- True P0 leakage only includes authentication credential plaintext or reusable secrets.
- `sensitive_output=false` / `no_sensitive_plaintext=true` must not be applied as a one-size-fits-all ban on all risk entity fields. In browser-backed evidence cards it means no credential secrets and no raw full body / raw record / raw labelInfo / raw originalLog full dump.
- Runtime validation and KIM E2E should classify fields through this policy.
- Broad semi-open / external share outputs may mask IP / UID / deviceId / UA by audience and sharing scope, but this masking must not be applied to internal evidence chaining or source observations.

## 9. Boundary

- This policy does not authorize arbitrary data access.
- This policy does not weaken credential redaction.
- This policy does not change DataAgent boundaries.
- This policy only controls output classification and reporting severity.
