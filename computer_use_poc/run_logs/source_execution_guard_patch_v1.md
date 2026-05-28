# Source Execution Guard Patch v1

## Background

Internal Agent investigation found that `dennis-risk-agent` inherits workspace bootstrap files such as AGENTS.md, TOOLS.md, SOUL.md, USER.md, IDENTITY.md, and session memory. Auth and runner troubleshooting details in those files can induce the subagent to read SSO state, build Cookie/Header manually, debug runners, or troubleshoot auth bridge during real evidence-card execution.

## Fix

- Added a Dennis source execution guard to AGENTS.md.
- Marked auth / runner troubleshooting content as `main_agent_config_ops_only`, `deprecated_for_dennis_subagent`, and `not_for_case_execution`.
- Added equivalent guard text to TOOLS.md and runtime guard.
- Added source failure template to answer templates.
- Added source execution guard metadata to the source orchestration plan.
- Extended `source_orchestration_check.py` to detect forbidden case-execution markers, runner/auth debug flags, source attempt overrun, and missing source_quality for `tool_gap` / `auth_bridge_gap`.
- Added smoke and regression cases for source attempt limit, cookie-state read, manual cookie/curl, runner debug, tool gap, partial evidence card, and main-config-only auth playbook.

## Boundaries

- Did not access real platforms.
- Did not call DataAgent or Hive.
- Did not change auth, gateway, safeBins, or live config.
- Did not rework RCP contract.
- Did not run real case execution.
- Did not build a full runtime release.
