# Asset Extraction Guard Baseline Run v1

## 1. Goal

Establish a semi-open baseline to prevent Dennis Risk Agent core asset extraction through conversation, file read requests, release package contents, or disguised handover/audit prompts.

This run is documentation and regression baseline only:

- no real platform access
- no real API call
- no auth state read
- no runtime connection
- no enforce mode
- no release/dist update

## 2. Added Files

- `computer_use_poc/asset_extraction_guard_policy.md`
- `computer_use_poc/asset_extraction_guard_regression_cases.md`
- `computer_use_poc/release_package_asset_minimization_policy.md`
- `computer_use_poc/readonly_semi_open_release_manifest_guidance.md`
- `computer_use_poc/asset_extraction_guard_coverage_matrix.md`
- `computer_use_poc/run_logs/asset_extraction_guard_baseline_run_v1.md`

## 3. Modified Files

- `computer_use_poc/smoke_tests.md`

## 4. Protected Asset Coverage

Covered assets:

- source code
- system / developer / skill prompts
- raw skill source
- routing rules
- capability registry
- security policy / evaluator source
- case library / test cases
- run logs
- release package manifest and package contents
- internal platform API fields
- DataAgent query templates
- user / device / strategy / login-log field dictionaries
- semi-open sample library
- historical retrospectives

## 5. Regression Coverage

Regression case count: 32

Covered request types:

- direct source request
- full directory tree request
- prompt / skill extraction
- routing / capability registry extraction
- evaluator / policy source extraction
- test case / run log / release export
- full API / field dictionary extraction
- DataAgent query template extraction
- handover / audit / admin / developer / leaver disguise
- package / markdown / yaml-json bulk export
- bad case and safety test library extraction

## 6. Release Minimization Summary

Semi-open packages should exclude by default:

- `.git`
- historical `outputs/dist`
- full run logs
- drafts / POC process files
- full test suites
- full prompt injection / asset extraction case libraries
- raw internal screenshots
- auth state / cookie / token / session / browser_storage_state_marker
- unredacted observations
- development helper files not required by runtime

Allowed materials should be runtime-minimal:

- runtime guard
- field output policy
- response templates
- minimal README
- runtime-safe capability summary
- selected redacted readiness summaries
- non-sensitive manifest

## 7. Smoke Tests Update

Added smoke coverage for:

- no source fulltext output
- no system / skill prompt output
- no full policy / evaluator output
- no full case library / run logs
- no full API field dictionary
- no project package export
- allow high-level summary
- allow module responsibility outline
- release package excludes `.git`, auth state and credentials
- release package excludes full historical run logs and full test suites
- semi-open package follows runtime-minimal principle

## 8. Not Done

- Did not implement runtime file-read preflight.
- Did not implement package scanner.
- Did not implement enforce mode.
- Did not modify formal release or outputs/dist.
- Did not submit git commit.

## 9. Release Recommendation

Do not immediately rebuild formal release only for this baseline.

Before the next semi-open candidate package, run the asset minimization checklist and ensure the package does not include full test libraries, full run logs, prompt source, raw skill source, auth state, or development-only assets.
