# Runtime Config Apply Checklist v1

## Purpose

This checklist closes the gap between a readonly runtime config template and a live runtime that actually enforces it.

The presence of `dennis_agent_readonly_runtime_config_template.json` or any equivalent template file is only a design artifact. It does not prove that dennis-risk-agent is running with readonly constraints. The config is effective only after the live `openclaw.json` contains a dedicated `dennis-risk-agent` entry in `agents.list` and the runtime spawns that entry.

Do not use "template exists in repo" as evidence that runtime restrictions are applied.

## Required Checks

Before semi-open runtime validation, verify all of the following in the live runtime config inventory:

| check | required state | failure state |
|---|---|---|
| agent entry | `agents.list` contains an explicit `dennis-risk-agent` entry | only `main` exists |
| profile inheritance | dennis-risk-agent does not inherit full-profile defaults | dennis-risk-agent runs under generic full-profile defaults |
| exec security | `exec.security=allowlist` | arbitrary exec inherited from defaults |
| safe bins | `exec.safeBins` exists and only allows controlled readonly runners such as `sso_session_runner` | shell / curl / arbitrary scripts are available |
| tools deny | `tools.deny` includes write/edit/direct web fetch/browser-abuse capabilities | high-risk tools remain available by default |
| filesystem | `fs.workspaceOnly=true` | runtime can read/write outside intended workspace |
| loop detection | `loopDetection` is enabled | browser / SPA loop has no runtime guard |
| spawn target | main agent spawn resolves to the dedicated dennis-risk-agent entry | main spawns a generic default profile |
| main takeover | main agent does not directly query risk platforms after dennis timeout | main runs ad hoc curl/cookie/browser queries |

## Validation Steps

1. Inventory the live `openclaw.json`.
2. Confirm `agents.list` includes a dedicated `dennis-risk-agent` entry.
3. Confirm the dennis entry does not inherit unrestricted full-profile execution.
4. Confirm `exec.security=allowlist`.
5. Confirm `exec.safeBins` is present and contains only approved controlled runners.
6. Confirm `tools.deny` blocks direct write/edit/web-fetch/browser-abuse paths.
7. Confirm `fs.workspaceOnly=true`.
8. Confirm `loopDetection` is enabled.
9. Run dry validation: main can spawn dennis-risk-agent, but dennis cannot use arbitrary tools outside the readonly wrapper path.
10. Simulate dennis timeout: main records `subagent_timeout` and returns partial / retry / missing-source output instead of taking over platform queries.

## Do Not Misread

- `AGENTS.md` rules existing in the repository do not mean runtime config is applied.
- Release overlay completion does not mean live runtime is applied.
- A valid cookie or SSO session does not mean wrapper-first execution is active.
- Browser same-origin fetch success does not prove the wrapper is available.
- `dennis_agent_readonly_runtime_config_template.json` existing in the repo does not prove live `openclaw.json` includes dennis-risk-agent.

## Failure Handling

If any required check fails:

- set `runtime_config_not_applied`
- do not claim semi-open runtime safety boundaries are effective
- do not run platform validation as if readonly constraints are enforced
- output partial / missing runtime config gap instead of full runtime readiness
- ask the runtime owner to apply the dedicated dennis-risk-agent entry to live `openclaw.json`

## Bad Case Reference

`BC-RUNTIME-CONFIG-NOT-APPLIED-001`:

- readonly runtime template exists
- live `openclaw.json` has no dedicated `dennis-risk-agent` entry
- dennis inherits full-profile defaults
- `safeBins`, `tools.deny`, exec allowlist, workspace-only, and loop detection are not enforced for dennis
- wrapper-first becomes LLM guidance instead of runtime policy
- browser same-origin fetch and manual curl/cookie paths become more likely
- main agent may take over platform querying after dennis timeout

Correct fix: apply runtime config. Do not keep stacking routing documents as a substitute for runtime enforcement.
