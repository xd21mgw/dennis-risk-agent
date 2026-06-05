# Readonly Semi-open Release Manifest Guidance

## 1. Purpose

This guidance is for future readonly semi-open release packaging. It prevents development-time assets from being bundled into runtime packages.

This file is guidance only. This turn does not modify formal release packages or outputs/dist.

## 2. Pre-package Checks

Before creating a semi-open package:

- Confirm target audience: internal trusted / KIM semi-open / APP / Web / broader sharing.
- Confirm runtime entry files.
- Confirm capability registry is runtime-safe.
- Confirm field output classification policy is included.
- Confirm asset extraction guard policy is included as a summary or runtime rule.
- Confirm smoke tests are included only as summary unless needed by runtime.

## 3. Must Remove

- `.git`
- auth state files
- cookie / token / session / browser_storage_state_marker files
- raw platform screenshots
- full historical run logs
- full test cases
- full prompt injection and asset extraction attack libraries
- draft files and POC process notes
- raw internal observations
- unredacted field dictionaries
- complete skill / prompt source text unless explicitly required by runtime owner

## 4. Prefer Summary Replacement

| full asset | replacement |
|---|---|
| full skill source | skill summary and runtime behavior contract |
| full routing docs | runtime routing guard summary |
| full capability registry | runtime-safe capability summary |
| full test suite | smoke test summary |
| full run logs | selected redacted readiness summaries |
| full API field dictionary | field category and output policy |
| full DataAgent query templates | query-plan category list |

## 5. Manifest Requirements

Semi-open manifest should include:

- package name and base release
- included runtime files
- explicitly excluded asset classes
- closed P0 list
- known P1 items
- field output policy
- DataAgent boundary
- write-action boundary
- asset extraction boundary

## 6. Asset Minimization Checklist

Run before packaging:

- `asset_extraction_guard_policy.md` reviewed.
- `release_package_asset_minimization_policy.md` reviewed.
- package file list checked for auth state and credentials.
- package file list checked for full run log / test library.
- package manifest explains why selected run logs are included.
- no release package is used as a full project backup.

## 7. Future Work

- Build a package file-list scanner.
- Add CI check for denied path patterns.
- Add manifest completeness check.
- Add runtime response guard for raw asset extraction requests.
