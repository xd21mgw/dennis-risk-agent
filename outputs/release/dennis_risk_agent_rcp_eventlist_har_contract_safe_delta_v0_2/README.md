# Dennis Risk Agent RCP eventList HAR Contract Safe Delta v0.2

This package is a release-safe delta overlay for synchronizing the RCP eventList contract into the internal Agent and dennis-risk-agent runtime.

It is not a full runtime release. It is not a platform runtime test bundle. It only carries the RCP eventList contract YAML, failure taxonomy YAML, and safe synchronization instructions.

Scope:

- RCP eventList is the primary strategy-hit entry.
- eventList is a ClickHouse-like event query builder.
- Primary invocation is browser_same_origin.
- HTTP SSO direct remains needs_har_request_body_exact_replay.
- Wrong request body shape and wrong time field format must be classified before auth or permission.

This package does not carry platform state, network-capture payloads, transient runtime memory, pilot logs, or workspace-only operator notes.
