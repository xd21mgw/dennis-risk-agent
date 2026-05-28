# Dennis Risk Agent Platform Access Execution v0.1 Overlay

This is a runtime overlay for internal Agent / dennis-risk-agent smoke validation.

It is not a full runtime release, not a public Skill package, and not a safe-summary delta. It only carries the files needed to synchronize Platform Access Execution v0.1 into an internal runtime workspace.

## Purpose

This overlay provides:

- standard runner wrapper entrypoint;
- `platform_access` contracts;
- RCP `eventList` main entry and `fastQueryHbase` fallback rules;
- Weapon `graphData` / `riskData` execution contracts;
- login log fixed-window boundary;
- Archives Center P0 / publish-chain boundary;
- track-analysis event-day activity contract;
- unified `platform_access_observation` schema;
- failure taxonomy and smoke / regression cases.

## Security Boundary

This package does not include authentication state or sensitive execution material. It does not include raw HAR files, raw observations, cookie, token, session, header, password material, DataAgent/Hive results, historical full run logs, or a full runtime release.

Each user environment is responsible for its own platform state, browser profile, SSO state, and permissions.
