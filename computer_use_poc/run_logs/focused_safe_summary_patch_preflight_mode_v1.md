# focused_safe_summary_patch preflight mode v1

## Goal

Add a lightweight preflight mode for release-safe summary patch packages. The existing preflight gate only supported full runtime release packages and required full runtime files, which caused focused summary packages to fail `required_files_pass` even when scanner safety passed.

## Problem

`outputs/release/dennis_risk_agent_tianshi_runtime_patch_v1_safe/` intentionally contains only safe summary files:

- `README.md`
- `PATCH_MANIFEST.md`
- `CAPABILITY_DELTA_SUMMARY.md`
- `ROUTING_DELTA_SUMMARY.md`
- `ANSWER_TEMPLATE_DELTA_SUMMARY.md`
- `ROUTING_METADATA_CONTRACT_SUMMARY.md`
- `VALIDATION_SUMMARY.md`
- `OVERLAY_INSTRUCTIONS.md`
- `SAFETY_BOUNDARIES.md`
- `PATCH_CHECKLIST.md`

It must not include full mother-body runtime files such as runtime user guide, multi-entry guard, complete answer templates, complete registry, complete routing, smoke test source, process logs, or POC documents.

## Change

`computer_use_poc/release_preflight_check.py` now supports:

- `--release-type full_runtime_release`
- `--release-type focused_safe_summary_patch`
- alias: `--package-type`

`full_runtime_release` keeps the previous required-file policy.

`focused_safe_summary_patch` checks only the 10 safe summary files and still runs `package_asset_scanner.py`. If scanner reports `package_should_block=true`, preflight fails closed.

## Output Fields

Preflight output now includes:

- `release_type`
- `scanner_pass`
- `package_should_block`
- `required_files_pass`
- `preflight_pass`

## Validation Target

Command:

```bash
python3 computer_use_poc/release_preflight_check.py --release-type focused_safe_summary_patch outputs/release/dennis_risk_agent_tianshi_runtime_patch_v1_safe
```

Expected:

- `release_type=focused_safe_summary_patch`
- `scanner_pass=true`
- `package_should_block=false`
- `required_files_pass=true`
- `preflight_pass=true`

## Boundaries

- No full runtime release was rebuilt.
- No complete mother-body file was copied into the patch package.
- No run_logs / POC / source observation were introduced into the safe package.
- No real platform access.
- No DataAgent call.
