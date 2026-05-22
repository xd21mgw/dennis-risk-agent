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

| class | examples | default_output_policy | severity_if_plaintext |
|---|---|---|---|
| P0 credential / authentication secrets | token secret, accessToken, refreshToken, cookie, session, sessionId, authorization header, authToken, password, salt, storageState, auth credential in headers, KIM code, login ticket, credential secret | `present_redacted` / `credential_present_redacted` only | P0 |
| Highly sensitive personal information | phone number, ID card, real-name identity information, precise personal identity fields, verification code | `masked_redacted` / `safe_ref` / `count` / `distribution`; plaintext only with explicit internal authorization and strict necessity | P1/P0 depending exposure |
| Risk entity fields | UID / user_id, DID, deviceId, deviceceid, IP, tokenId when it is an event identifier rather than a token secret, requestId, sourceId, strategyId, adminaction, appVersion, UA, device model, login method, coarse geo | controlled by audience scope; usable as analysis entities in trusted internal risk analysis | P1 if audience policy is wrong; not P0 credential leakage by default |
| Derived / aggregate features | IP subnet, ASN, carrier, geo cluster, device risk tags, same-device count, registration cohort, behavior-object cluster, risk label distribution, success/failure counts, time-series summary | preferred output for reports and KIM responses | usually safe if no raw sensitive values |

## 3. P0 Credential / Authentication Secrets

Never output plaintext:

- token plaintext.
- accessToken / refreshToken plaintext.
- cookie / session / sessionId plaintext.
- authorization header / authToken plaintext.
- password / salt.
- storageState.
- authentication credentials inside headers.
- KIM code / login ticket / credential secret.

Output strategy:

- Only output `present_redacted` or `credential_present_redacted`.
- Never write plaintext to run log, KIM response, report, observation, evidence card, or raw reference.
- If requested by a user prompt, deny or redact.

## 4. Highly Sensitive Personal Information

Default no plaintext:

- phone number.
- ID card / real-name identity information.
- precise personal identity information.
- verification code.

Output strategy:

- Use `masked_redacted`, `safe_ref`, `count`, or `distribution`.
- Plaintext requires explicit internal authorization and strict necessity.
- External or broad semi-open outputs should avoid plaintext.

## 5. Risk Entity Fields

Risk entity fields are normal inputs for risk analysis:

- UID / user_id.
- DID / deviceId / deviceceid.
- IP.
- tokenId when it is an event identifier rather than a token secret.
- requestId / sourceId / strategyId / adminaction.
- appVersion / UA / device model / login method / coarse geo.

Output strategy:

- Trusted internal risk analysis: may output as analysis entities for evidence cards, pattern summaries, and case tables when necessary.
- KIM semi-open: may output by default when useful, but avoid large-scale detail export; use `safe_ref` or partial mask when the audience or channel is broader.
- Larger semi-open, cross-team sharing, or outbound materials: default to `masked`, `safe_ref`, `count`, or `distribution`.
- Do not confuse risk entity fields with token / cookie / session / password credential secrets.

`tokenId` rule:

- If it is a token event identifier, it is not a token secret.
- Default output should be `token_id_ref` or partial mask.
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

## 7. Audience Scope Matrix

| audience_scope | risk_entity_fields | credential_secrets | recommended_output |
|---|---|---|---|
| internal_trusted_risk_analysis | allowed when necessary | never plaintext | evidence card values or safe refs; credentials present_redacted |
| KIM_semi_open | generally allowed with output-policy calibration | never plaintext | entity values when needed, otherwise safe_ref / partial mask / distribution |
| broad_semi_open | default masked / safe_ref | never plaintext | safe_ref, count, distribution, derived features |
| cross_team_or_external_share | default masked / aggregate only | never plaintext | masked, safe_ref, count, distribution, no raw detail |

## 8. Validation Rules

- IP / UID / DID / deviceId plaintext is not automatically P0 credential leakage.
- Whether to mask risk entity fields depends on audience scope, sharing scope, field purpose, and output channel.
- True P0 leakage only includes authentication credential plaintext or reusable secrets.
- `no_sensitive_plaintext=true` must not be applied as a one-size-fits-all ban on all risk entity fields.
- Runtime validation and KIM E2E should classify fields through this policy.
- Broad semi-open outputs should still default IP / UID / deviceId to safe refs or partial masks to prevent unbounded propagation.

## 9. Boundary

- This policy does not authorize arbitrary data access.
- This policy does not weaken credential redaction.
- This policy does not change DataAgent boundaries.
- This policy only controls output classification and reporting severity.
