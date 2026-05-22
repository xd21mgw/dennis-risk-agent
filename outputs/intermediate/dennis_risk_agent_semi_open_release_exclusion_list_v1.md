# Dennis Risk Agent Semi-open Release Exclusion List v1

This file defines files and path patterns that must not enter the semi-open release package unless an explicit owner review overrides the rule.

## 1. Hard Exclusions

| path / pattern | reason | replacement |
|---|---|---|
| `.git/` | repository metadata and history | none |
| `**/.git/**` | repository metadata and history | none |
| `auth_states/`, `.ks_sso/`, `**/*auth_state*` | authentication state risk | not packaged |
| `**/*storageState*`, `**/*cookie*`, `**/*token*`, `**/*session*`, `**/*header*` when containing credentials | credential leakage risk | redacted summary only |
| `outputs/dist/**` | historical package tarballs, not release source | only target package generated after review |
| `outputs/packages/**` | process artifacts and historical packages | not packaged |
| full `computer_use_poc/run_logs/**` | historical run logs can contain internal process details | selected redacted readiness summaries |
| raw `computer_use_poc/observations/**` | may contain platform-derived details | selected redacted samples only |
| raw screenshots / browser dumps | platform and personal data risk | redacted summary |
| unreviewed `outputs/reviews/**` | internal review and draft material | selected approved summaries |
| unreviewed `eval/**/json/**` full case corpora | case library extraction risk | minimal semi-open prompt matrix |
| `prompt_injection_defense_cases.md` full corpus | safety regression corpus extraction risk | summary or selected tests |
| `asset_extraction_guard_regression_cases.md` full corpus | asset extraction regression corpus extraction risk | summary or selected tests |
| full Skill / Prompt source not approved for sharing | core asset extraction risk | runtime summary / minimized prompt |
| internal platform raw API inventories with sensitive fields | platform access and field leakage risk | high-level capability contract |
| any file containing real cookie / token / session / header / auth state | P0 credential risk | exclude |
| any file containing raw phone / ID card / personal identity details | personal information risk | redact / safe_ref |

## 2. Sensitive Entity Policy

UID / DID / IP can be internal risk-control entity fields. They are not the same class as cookie / token / session / password / authorization / storageState / header credentials.

However, in semi-open release:

- Use safe_ref or partial mask when the audience is broad.
- Prefer count, cohort, distribution, subnet, or derived feature when enough.
- Do not include phone number, cookie, token, session, header, storageState, authorization secret, password, or auth state content.

## 3. Historical POC and Run Log Rule

Historical POC files and run logs are useful for development but should not be shipped by default.

Allowed:

- Selected redacted readiness summaries.
- Minimal validation summaries.
- User-facing guide.

Not allowed:

- Full historical `run_logs/`.
- Raw observations.
- Long internal debugging transcripts.
- Unreviewed platform failures with internal path details.

## 4. DataAgent and Platform Interface Rule

Do not include:

- Unreviewed internal platform field dictionaries.
- Raw DataAgent query templates that reveal broad internal table or field usage beyond approved query plan examples.
- Any material implying DataAgent is a universal data substrate.

Allowed:

- Boundary documents stating DataAgent is for Hive / warehouse analysis.
- Redacted query question examples.
- Plan-only contract.

## 5. Build-time Checks

Before actual packaging:

1. Run package asset scanner on candidate release directory.
2. Inspect filelist against this exclusion list.
3. Confirm selected run logs are redacted.
4. Confirm question_collection examples contain no credentials or personal sensitive plaintext.
5. Confirm non-ATO runtime summaries are included as formal capabilities, not appendix.
