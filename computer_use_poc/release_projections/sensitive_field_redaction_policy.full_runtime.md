# Sensitive Field Redaction Policy - Full Runtime Projection

This is a release-safe projection of the mother redaction policy. The mother
repository keeps the full literal safety vocabulary for policy development and
negative-request recognition. The full-runtime package keeps only the runtime
boundary needed by Dennis answers and local regressions.

## Runtime Rule

- Credential material is never displayed, retained in summaries, or used as a
  source-chaining reference.
- Auth-state material is never packaged or printed.
- Prompt-source material is never disclosed.
- Unprojected platform payloads are never printed in user-facing answers.
- Internal risk-review identifiers may be shown only when they are minimum
  necessary evidence anchors, such as user, device, event, source, policy, or
  content references.
- External-share output must mask risk entities more aggressively than internal
  review output.

## Safe Output Forms

- Use `safe_ref` for sensitive evidence anchors.
- Use `present_redacted=true` for credential-like field presence.
- Use counts, status classes, source quality, and missing evidence summaries
  instead of unprojected platform payloads.
- Use partial masks only for risk entities that are needed for evidence
  review.

## Always Redact

- Credential and auth-state material.
- Prompt-source material.
- Full personal identity fields.
- Complete request or response payloads from platform sources.
- Operator account details unless explicitly needed as a redacted audit
  reference.

## Boundary

Redaction gaps must be treated as output safety issues, not as risk evidence.
No-data, blocked, timeout, skipped, and missing-contract states are source gaps
and must not be used as low-risk counter evidence.
