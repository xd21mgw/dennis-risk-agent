# Multi-entry Candidate Readiness Closure Run v1

## 1. Goal

Close P0/P1 readiness gaps before building a Multi-entry Semi-open Candidate package.

This run is documentation and local dry-run only:

- no real platform access
- no DataAgent / Hive call
- no release / outputs/dist update
- no credential plaintext output

Input validation basis:

- internal Agent multi-entry runtime guard dry-run validation: 8/8 PASS
- no entry bypass observed
- no KIM-specific bypass observed
- no automatic DataAgent call observed
- no sensitive field output risk observed

## 2. Wrapper JSON Output Closure

Updated local `computer_use_poc/sso_session_runner.py` and contract docs so wrapper output is machine parseable.

Closure points:

- stdout contains exactly one JSON envelope.
- stderr is reserved for human-readable diagnostics.
- success / failed / partial envelope schema is documented.
- `json.loads(stdout)` can parse success and validation failure outputs.
- `recallSource=2,0,1,3` is preserved in constructed unified login URL.
- no cookie / token / session / browser_storage_state_marker / header is output.
- wrapper remains dry-run local URL construction in this repository; no real platform call.

Envelope:

- `schema_version=sso_session_runner_envelope_v1`
- `status=success|failed|partial`
- `result`
- `metadata`
- `security`
- `error`
- `logs`

Local checks:

- valid unified login URL: parseable success envelope
- illegal `platform_key`: parseable failed envelope
- injected `user_id`: parseable failed envelope

## 3. Main Agent Routing Solidification

Updated multi-entry routing docs to treat runtime guard as main-agent routing contract, not only a prompt guideline.

Required before Dennis spawn:

- intent classification
- execution / plan / fast_ack decision
- mixed request decomposition
- field output policy selection
- DataAgent execution boundary
- response length / channel constraint

Routing defaults:

- ATO single case -> `execution_readonly`
- ATO expansion / 举一返三 -> `plan_mode_only`
- black_market_account_matrix paused branch -> `fast_ack` / `async_ack`
- DataAgent request -> `plan_only` / `require_confirmation`
- write action -> `deny` / `plan_only`
- sensitive credential output -> `deny` / `redact`

If routing decision cannot be produced, the entry must fail closed to plan-only or clarification.

## 4. Semi-open User Guide

Added `computer_use_poc/runtime_semi_open_user_guide_v1.md`.

The guide covers:

- supported capabilities
- unsupported actions
- user input fields
- historical case login-log window gap
- output boundary
- KIM / APP / Web channel differences

## 5. KIM Length Constraint Closure

Added text regression expectations:

- Routing Summary first for long KIM responses.
- Long evidence table becomes summary + `safe_ref` / follow-up.
- KIM does not output over-channel long reports.
- Web may output long reports, but still obeys field policy and DataAgent boundary.

## 6. Candidate Package Blocking Status

P0 blocker status:

- wrapper JSON parseability: closed locally
- main agent routing contract: documented and smoke-tested
- KIM length constraint: documented and smoke-tested

Known pre-package items that still require runtime validation:

- APP/Web actual deployment validation
- main agent implementation wiring for normalized routing decision
- routing trace marker implementation, if runtime observability is required

Candidate package recommendation:

- No P0 documentation blocker remains for preparing a Multi-entry Semi-open Candidate package.
- Runtime owner should still validate APP/Web entry behavior before broad semi-open rollout.

## 7. Not Done

- Did not access real platform.
- Did not call DataAgent / Hive.
- Did not update outputs/dist.
- Did not update formal release package.
- Did not implement a production approval system.
- Did not implement audit log persistence.
