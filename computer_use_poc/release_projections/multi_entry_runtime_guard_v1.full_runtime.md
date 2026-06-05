# Multi-entry Runtime Guard - Full Runtime Projection

Guard marker: `DENNIS_ROUTING_GUARD_V1`.

This file is the release-safe runtime projection of the mother guard. It keeps
the required routing and execution boundary markers used by local preflight,
without shipping the full mother guard text.

## Routing Modes

- `single_entity_execution_mode`: explicit single-entity risk checks use the
  controlled runtime runner and source plan.
- `small_batch_execution_with_checkpoint`: small batches still require source
  checkpoints, source quality, and bounded execution.
- `batch_clustering_mode`: large or commonality-focused batches must avoid
  per-user uncontrolled execution and must produce bounded batch evidence.

## Source Plan Gate

Before executing any platform source, the runtime must build a source plan and
read the platform playbook index:

- `platform_call_playbook_index`
- 执行任何平台 source 前，必须先读取
- `platform_call_preflight`

No source plan means no platform source call.

## Realtime API Confirmation Boundary

- 实时只读 API 查询不需要用户确认 when the request is a bounded, registered,
  readonly source call with required fields present.
- DataAgent / Hive / 大批量 / 写操作 / 高风险操作需要确认.

## Controlled Execution Boundary

- Live case execution uses the registered runtime runner and browser-backed
  batch action contract.
- `/actions/batch` and `browser_backed_actions_batch_v1` are source-plan
  execution paths, not general-purpose platform access.
- Main agent must not take over platform source execution after a source gap or
  subagent timeout.
- Legacy runner and manual diagnostic paths are not case-execution fallback
  paths.
- Auth or permission gaps must be recorded as source quality, not repaired in
  the middle of a business case.

## Source Quality Boundary

The following states must be preserved in `source_quality` and missing
evidence:

- `no_data`
- `blocked`
- `timeout`
- `auth_failed`
- `parse_error`
- `skipped`
- `missing_contract`
- `partial`

These states are not low-risk counter evidence.

## Batch Commonality Boundary

- Source coverage is not risk commonality.
- Field extraction is not group evidence.
- Batch anchors must be aggregated before L2 drilldown selection.
- Single-entity anchors can provide context, but cannot support a group
  candidate by themselves.
- `group_profile_candidate` is not a confirmed group.
- Single-round output is `limited_commonality`; rolling stability requires more
  than one round.

## DataAgent Boundary

DataAgent/Hive execution requires explicit per-call authorization. Query plans
and validation plans must not be written as completed validation.
