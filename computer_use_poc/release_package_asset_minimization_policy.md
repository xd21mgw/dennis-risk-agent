# Release Package Asset Minimization Policy

## 1. Goal

Semi-open release packages must be runtime-minimal. A release package is not a full knowledge-base backup and must not contain unnecessary source assets, historical process files, full test libraries, or sensitive internal materials.

## 2. Default Exclusions

Semi-open release packages should not include:

- `.git`
- historical `outputs/dist` packages
- full historical `run_logs`
- drafts
- POC process files
- full test suites
- full prompt injection case library
- full asset extraction regression case library
- raw internal platform screenshots
- auth state files
- cookie / token / session / storageState
- local temporary files
- unredacted observation raw text
- unnecessary development helper source files
- historical retrospectives containing sensitive internal fields

## 3. Allowed Runtime Materials

Semi-open release packages may include:

- Runtime-required skill summaries.
- Runtime capability registry summary or runtime-safe version.
- Runtime preflight policy.
- Minimal evaluator scripts required by runtime.
- Response templates.
- Minimal README.
- Minimal smoke test summary.
- Non-sensitive manifest.
- Field output classification policy.
- Runtime guard and routing contract.

## 4. Allowlist / Denylist

| path_pattern | include_or_exclude | reason | risk_if_included | replacement_if_excluded |
|---|---|---|---|---|
| `.git/**` | exclude | Repository metadata is not runtime needed | source history leakage | none |
| `outputs/dist/**` | exclude | Historical packages duplicate assets | uncontrolled package propagation | manifest pointer only |
| `computer_use_poc/run_logs/**` | exclude by default | Process logs may contain internal detail | case / platform leakage | selected redacted readiness logs |
| `computer_use_poc/run_logs/*readiness*` | include selectively | Candidate validation evidence | low if redacted | summary only |
| `computer_use_poc/run_logs/*pilot*` | include selectively | Semi-open ATO pilot evidence | case detail leakage | redacted pilot summary |
| `computer_use_poc/*regression_cases*.md` | exclude by default | Full attack/test library | adversarial prompt library leakage | coverage matrix summary |
| `computer_use_poc/asset_extraction_guard_regression_cases.md` | exclude from semi-open runtime | Full extraction attack library | users learn bypass prompts | coverage summary |
| `computer_use_poc/prompt_injection_defense_cases.md` | exclude from semi-open runtime | Full prompt injection library | jailbreak prompt leakage | smoke summary |
| `skills/**/SKILL.md` | exclude raw unless runtime required | Skill source is core asset | prompt/skill extraction | skill summary |
| `computer_use_poc/capability_registry.md` | include summary/runtime-safe version | Required for routing | full internal capability exposure | runtime registry summary |
| `computer_use_poc/security_preflight_evaluator.py` | include only if runtime requires | Runtime guard script | implementation copying | compiled/deployed service or summary |
| `computer_use_poc/security_preflight_policy.yaml` | include runtime-safe version only | Runtime policy | full policy extraction | minimized policy |
| `computer_use_poc/smoke_tests.md` | include minimal summary only | Validation signal | full test suite leakage | smoke test summary |
| `computer_use_poc/field_output_classification_policy_v1.md` | include | Required output policy | low | none |
| `computer_use_poc/multi_entry_runtime_guard_v1.md` | include | Required entry guard | low-medium | runtime prompt summary |
| `**/*auth*state*` | exclude | Auth state | credential leakage | none |
| `**/*cookie*` | exclude | Credential material | P0 leakage | none |
| `**/*token*` | exclude unless policy doc only | Credential ambiguity | P0 leakage | redacted policy text |
| `**/*session*` | exclude unless policy doc only | Credential ambiguity | P0 leakage | redacted policy text |
| `**/*.tmp` | exclude | Local temp | accidental leakage | none |

## 5. Principles

- Prefer summaries over full source.
- Prefer runtime-minimal assets over development materials.
- Prefer on-demand internal access over default packaging.
- Do not include full test sets or case libraries in semi-open packages.
- Do not treat release packages as archival backups.
- Include only what the runtime needs to behave safely and usefully.

## 6. Packaging Checklist

Before packaging:

1. Run asset minimization checklist.
2. Verify no auth state, cookie, token, session, storageState or headers.
3. Verify no full case library / test suite.
4. Verify no full run log dump.
5. Verify only selected redacted readiness logs are included.
6. Verify manifest explains included files and excluded assets.
7. Verify field output policy and runtime guard are present.
8. Verify package can function without development-only documents.
