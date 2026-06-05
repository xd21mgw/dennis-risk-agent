# Asset Extraction Guard Coverage Matrix

| protected_asset_type | risk_request_type | current_protection_strategy | regression_case_coverage | release_minimization_coverage | current_limitations | next_todo |
|---|---|---|---|---|---|---|
| source code | direct source / full implementation request | deny_raw_extraction | AEG-001, AEG-012 | exclude development helper files unless runtime required | no runtime file-read interceptor yet | add runtime preflight for file read |
| system / developer 提示词 | prompt extraction | deny_raw_extraction | AEG-003 | do not include raw prompts in semi-open package | prompt may be loaded in runtime memory | runtime refusal template |
| skill prompt/source | skill raw text request | deny_raw_extraction / degrade_to_outline | AEG-004, AEG-022 | replace with skill summary | runtime may require selected skill text | create runtime-safe skill summaries |
| routing rules | raw routing export | deny_raw_extraction / summary only | AEG-005 | include runtime guard summary | some routing docs still detailed | split runtime summary vs dev docs |
| capability registry | full registry export | degrade_to_outline | AEG-006 | include runtime-safe registry summary | current registry may be verbose | create minimized registry |
| security evaluator/policy | evaluator or policy source request | deny_raw_extraction | AEG-007, AEG-008, AEG-032 | include only runtime-safe policy/script if needed | local scripts still in repo | package scanner |
| case library / test cases | full case/test export | deny_raw_extraction | AEG-009, AEG-018, AEG-030 | exclude full test libraries | smoke_tests remains large | create smoke summary for package |
| run logs | copy all logs | deny_raw_extraction | AEG-010, AEG-024 | include only selected redacted readiness logs | selected logs may still expose process details | log redaction scanner |
| release package | package/export request | deny_raw_extraction | AEG-011, AEG-025 | manifest-driven minimal packaging | no automated allowlist enforcement | packaging checklist automation |
| internal API fields | full API/field dictionary | deny_raw_extraction / outline | AEG-013, AEG-016 | field category summary only | docs may contain detailed fields | field dictionary minimization |
| user/device fields | full profile field request | degrade_to_outline | AEG-014, AEG-015 | include field categories only | existing docs detailed | generate public-safe field summary |
| DataAgent query templates | full template library request | deny_raw_extraction | AEG-017 | include query-plan category only | templates in eval docs | package denylist |
| historical materials | retrospectives / bad cases | deny_raw_extraction | AEG-029 | exclude historical retrospectives | historical files remain in repo | archive access policy |
| disguised extraction | handover/audit/admin/dev/leaver | deny_raw_extraction or outline | AEG-019 to AEG-023, AEG-031 | package rules unaffected by requester claim | social engineering still relies on model behavior | runtime policy injection |
| config files | yaml/json bulk export | deny_raw_extraction | AEG-028 | exclude full configs unless runtime required | config minimization manual | config allowlist |

## Current Coverage Summary

- Direct raw extraction: covered by deny rules.
- Disguised handover/audit/admin requests: covered by regression cases.
- Release package over-inclusion: covered by minimization policy and manifest guidance.
- Test / run log / case library leakage: covered by deny and package exclude rules.

## Current Limits

- Documentation baseline only.
- No runtime enforce mode.
- No file-read preflight in this turn.
- No package scanner in this turn.
- No automated prompt/source redaction middleware in this turn.

## Next TODO

- Implement runtime asset extraction preflight.
- Add package allowlist/denylist scanner.
- Create runtime-safe capability registry summary.
- Create runtime-safe smoke summary.
- Add redaction checks for selected run logs.
