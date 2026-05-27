# Selected Run Log Summaries

The full `computer_use_poc/run_logs/` path is intentionally excluded from this canonical release because package scanner rules treat run log directories as high-risk process assets. This file preserves release-safe summaries of the two relevant closure logs.

## ATO Small Batch / Auth Bridge / Source Boundary Closure

Source log represented: `computer_use_poc/run_logs/ato_small_batch_auth_bridge_source_boundary_unified_patch_v1.md`

Summary:

- consolidated ATO single source checkpoint and partial evidence fallback
- added 2-9 user `small_batch_execution_with_checkpoint`
- clarified unified login auth bridge boundaries
- documented login log reliable-window and APP-login-only source gaps
- added regression coverage for single ATO, small batch, auth bridge, window boundary, and source gap

## Runtime Config Apply / Canonical Baseline Closure

Source log represented: `computer_use_poc/run_logs/runtime_config_apply_canonical_baseline_patch_v1.md`

Summary:

- clarified that readonly runtime config templates do not equal live runtime enforcement
- added runtime config apply checklist
- added canonical runtime baseline
- documented `BC-RUNTIME-CONFIG-NOT-APPLIED-001`
- set live apply order: apply dennis entry, validate runtime constraints, overlay ATO rules, run single and small-batch regression

## Boundary

This summary intentionally does not include raw run log bodies, raw platform response, historical case details, credentials, auth state, or user-sensitive material.
